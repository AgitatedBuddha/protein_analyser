"""
Nutrition Label Extractor

Extracts nutritional information from protein powder nutrition labels.
"""

from pathlib import Path
from typing import Optional

from .base import BaseExtractor


class NutritionExtractor(BaseExtractor):
    """
    Extractor for nutrition labels.
    
    Extracts: serving size, energy, protein, carbohydrates, fat, sodium.
    """
    
    PROFILE_TYPE = "nutrients"
    PROMPT_FILE = "extract_nutrition_label_v1.prompt.md"
    SCHEMA_FILE = "extract_nutrition_label_v1.schema.json"
    
    # File patterns to search for
    FILE_PATTERNS = [
        "nutrients_profile.*",
        "nutrition_profile.*",
        "nutritional_info.*",
        "nutrition.*",
    ]
    
    @classmethod
    def find_image(cls, brand_dir: Path) -> Optional[Path]:
        """Find nutrition label image in a brand directory."""
        for pattern in cls.FILE_PATTERNS:
            matches = list(brand_dir.glob(pattern))
            for match in matches:
                if match.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    return match
        return None
