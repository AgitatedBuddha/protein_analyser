"""
Base Extractor Module

Contains shared LLM client initialization and API calling logic.
"""

import base64
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, Optional

import jsonschema
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
SKILLS_DIR = BASE_DIR / "skills"


class ExtractionResult(BaseModel):
    """Result from label extraction."""
    product_id: str
    profile_type: str = Field(description="Type of profile extracted")
    extracted_fields: dict
    raw_evidence: dict
    quality: dict
    provider: str = Field(description="LLM provider used")
    model: str = Field(description="Model used for extraction")
    valid: bool = Field(description="Whether output passed schema validation")
    validation_errors: list[str] = Field(default_factory=list)


class BaseExtractor(ABC):
    """
    Base class for label extractors.
    
    Provides shared LLM client initialization and API calling logic.
    Subclasses implement profile-specific extraction.
    """
    
    # Subclasses must define these
    PROFILE_TYPE: str = ""
    PROMPT_FILE: str = ""
    SCHEMA_FILE: str = ""
    
    def __init__(
        self,
        provider: Literal["openai", "gemini"] = "gemini",
        model: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model or self._default_model()
        self._client = self._init_client()
        self._prompt: Optional[str] = None
        self._schema: Optional[dict] = None
    
    def _default_model(self) -> str:
        """Get default model for provider."""
        if self.provider == "openai":
            return "gpt-4o"
        elif self.provider == "gemini":
            return "gemini-2.0-flash"
        raise ValueError(f"Unknown provider: {self.provider}")
    
    def _init_client(self):
        """Initialize LLM client based on provider."""
        if self.provider == "openai":
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            return OpenAI(api_key=api_key)
        
        elif self.provider == "gemini":
            from google import genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            return genai.Client(api_key=api_key)
        
        raise ValueError(f"Unknown provider: {self.provider}")
    
    @property
    def prompt(self) -> str:
        """Load and cache prompt."""
        if self._prompt is None:
            prompt_path = SKILLS_DIR / self.PROMPT_FILE
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            self._prompt = prompt_path.read_text()
        return self._prompt
    
    @property
    def schema(self) -> dict:
        """Load and cache schema."""
        if self._schema is None:
            schema_path = SKILLS_DIR / self.SCHEMA_FILE
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            self._schema = json.loads(schema_path.read_text())
        return self._schema
    
    def _encode_image(self, image_path: Path) -> tuple[str, str]:
        """Encode image to base64 and determine MIME type."""
        suffix = image_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime_type = mime_types.get(suffix, "image/png")
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        return image_data, mime_type
    
    def _call_openai(self, image_path: Path, product_id: str) -> dict:
        """Call OpenAI API for extraction."""
        image_data, mime_type = self._encode_image(image_path)
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract information from this label. Product ID: {product_id}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            max_tokens=2000,
            temperature=0,
        )
        
        content = response.choices[0].message.content
        return self._parse_response(content)
    
    def _call_gemini(self, image_path: Path, product_id: str) -> dict:
        """Call Gemini API for extraction."""
        import PIL.Image
        
        image = PIL.Image.open(image_path)
        full_prompt = f"{self.prompt}\n\nExtract information from this label. Product ID: {product_id}"
        
        response = self._client.models.generate_content(
            model=self.model,
            contents=[full_prompt, image],
            config={
                "temperature": 0,
                "max_output_tokens": 2000,
            },
        )
        
        return self._parse_response(response.text)
    
    def _parse_response(self, content: str) -> dict:
        """Parse LLM response, removing markdown if present."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    
    def validate_output(self, output: dict) -> tuple[bool, list[str]]:
        """Validate extraction output against schema."""
        errors = []
        try:
            jsonschema.validate(output, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(str(e.message))
            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
            return False, errors
    
    def extract(self, image_path: str | Path, product_id: str) -> ExtractionResult:
        """
        Extract information from a label image.
        
        Args:
            image_path: Path to the label image
            product_id: Identifier for the product
        
        Returns:
            ExtractionResult with extracted data and validation status
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Call appropriate API
        if self.provider == "openai":
            output = self._call_openai(image_path, product_id)
        else:
            output = self._call_gemini(image_path, product_id)
        
        # Validate output
        valid, errors = self.validate_output(output)
        
        return ExtractionResult(
            product_id=output.get("product_id", product_id),
            profile_type=self.PROFILE_TYPE,
            extracted_fields=output.get("extracted_fields", {}),
            raw_evidence=output.get("raw_evidence", {}),
            quality=output.get("quality", {}),
            provider=self.provider,
            model=self.model,
            valid=valid,
            validation_errors=errors,
        )
    
    @classmethod
    def find_image(cls, brand_dir: Path) -> Optional[Path]:
        """Find the appropriate image file in a brand directory."""
        # Subclasses should override this to define their file patterns
        return None


def detect_profile_type(image_path: Path) -> Literal["nutrients", "aminoacid", "unknown"]:
    """
    Detect profile type from filename.
    
    Uses explicit filename-based detection for reliability.
    """
    name = image_path.stem.lower()
    
    if "nutrient" in name or "nutrition" in name:
        return "nutrients"
    elif "amino" in name:
        return "aminoacid"
    else:
        return "unknown"


def get_brand_from_path(image_path: Path) -> str:
    """Extract brand name from image path (parent directory name)."""
    return image_path.parent.name
