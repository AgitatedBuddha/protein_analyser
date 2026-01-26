"""
Unit tests for the nutrition label extractors.

These tests run without API calls using mocked responses.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import jsonschema
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors import (
    NutritionExtractor,
    AminoacidExtractor,
    ExtractionResult,
    get_extractor,
    detect_profile_type,
    get_brand_from_path,
    EXTRACTORS,
)
from extractors.base import BaseExtractor


class TestProfileDetection:
    """Tests for profile type detection from filenames."""
    
    def test_detect_nutrients_profile(self):
        assert detect_profile_type(Path("images/brand/nutrients_profile.png")) == "nutrients"
        assert detect_profile_type(Path("images/brand/nutritional_info.jpg")) == "nutrients"
        assert detect_profile_type(Path("nutrition_label.png")) == "nutrients"
    
    def test_detect_aminoacid_profile(self):
        assert detect_profile_type(Path("images/brand/aminoacid_profile.png")) == "aminoacid"
        assert detect_profile_type(Path("images/brand/amino_acids.jpg")) == "aminoacid"
    
    def test_detect_unknown_profile(self):
        assert detect_profile_type(Path("images/brand/label.png")) == "unknown"
        assert detect_profile_type(Path("random_file.jpg")) == "unknown"


class TestBrandExtraction:
    """Tests for brand name extraction from path."""
    
    def test_get_brand_from_path(self):
        assert get_brand_from_path(Path("images/OriginPlantProtein/nutrients_profile.png")) == "OriginPlantProtein"
        assert get_brand_from_path(Path("/full/path/BrandName/label.png")) == "BrandName"


class TestExtractorRegistry:
    """Tests for extractor registry and factory."""
    
    def test_registry_has_nutrients(self):
        assert "nutrients" in EXTRACTORS
        assert EXTRACTORS["nutrients"] == NutritionExtractor
    
    def test_registry_has_aminoacid(self):
        assert "aminoacid" in EXTRACTORS
        assert EXTRACTORS["aminoacid"] == AminoacidExtractor
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_get_extractor_nutrients(self):
        extractor = get_extractor("nutrients")
        assert isinstance(extractor, NutritionExtractor)
        assert extractor.PROFILE_TYPE == "nutrients"
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_get_extractor_aminoacid(self):
        extractor = get_extractor("aminoacid")
        assert isinstance(extractor, AminoacidExtractor)
        assert extractor.PROFILE_TYPE == "aminoacid"
    
    def test_get_extractor_invalid(self):
        with pytest.raises(ValueError, match="Unknown profile type"):
            get_extractor("invalid")


class TestNutritionExtractor:
    """Tests for NutritionExtractor class."""
    
    def test_profile_type(self):
        assert NutritionExtractor.PROFILE_TYPE == "nutrients"
    
    def test_skill_files(self):
        assert NutritionExtractor.PROMPT_FILE == "extract_nutrition_label_v1.prompt.md"
        assert NutritionExtractor.SCHEMA_FILE == "extract_nutrition_label_v1.schema.json"
    
    def test_file_patterns(self):
        assert "nutrients_profile.*" in NutritionExtractor.FILE_PATTERNS


class TestAminoacidExtractor:
    """Tests for AminoacidExtractor class."""
    
    def test_profile_type(self):
        assert AminoacidExtractor.PROFILE_TYPE == "aminoacid"
    
    def test_skill_files(self):
        assert AminoacidExtractor.PROMPT_FILE == "extract_aminoacid_profile_v1.prompt.md"
        assert AminoacidExtractor.SCHEMA_FILE == "extract_aminoacid_profile_v1.schema.json"
    
    def test_file_patterns(self):
        assert "aminoacid_profile.*" in AminoacidExtractor.FILE_PATTERNS


class TestNutritionSchemaValidation:
    """Tests for nutrition JSON schema validation."""
    
    def test_valid_output_passes_validation(self, sample_nutrition_schema, valid_nutrition_output):
        """Valid extraction output should pass schema validation."""
        try:
            jsonschema.validate(valid_nutrition_output, sample_nutrition_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Valid output failed validation: {e.message}")
    
    def test_invalid_output_fails_validation(self, sample_nutrition_schema, invalid_extraction_output):
        """Invalid extraction output should fail schema validation."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_extraction_output, sample_nutrition_schema)
    
    def test_missing_product_id_fails(self, sample_nutrition_schema, valid_nutrition_output):
        """Missing product_id should fail validation."""
        del valid_nutrition_output["product_id"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(valid_nutrition_output, sample_nutrition_schema)
    
    def test_invalid_confidence_range_fails(self, sample_nutrition_schema, valid_nutrition_output):
        """Confidence outside 0-1 range should fail validation."""
        valid_nutrition_output["quality"]["extraction_confidence"] = 1.5
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(valid_nutrition_output, sample_nutrition_schema)


class TestAminoacidSchemaValidation:
    """Tests for amino acid JSON schema validation."""
    
    def test_valid_output_passes_validation(self, sample_aminoacid_schema, valid_aminoacid_output):
        """Valid amino acid extraction output should pass schema validation."""
        try:
            jsonschema.validate(valid_aminoacid_output, sample_aminoacid_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Valid amino acid output failed validation: {e.message}")
    
    def test_invalid_serving_basis_fails(self, sample_aminoacid_schema, valid_aminoacid_output):
        """Invalid serving_basis enum value should fail."""
        valid_aminoacid_output["extracted_fields"]["serving_basis"] = "invalid"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(valid_aminoacid_output, sample_aminoacid_schema)


class TestExtractorValidation:
    """Tests for BaseExtractor.validate_output method."""
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_validate_valid_nutrition_output(self, valid_nutrition_output):
        """Extractor should validate correct nutrition output."""
        extractor = NutritionExtractor()
        valid, errors = extractor.validate_output(valid_nutrition_output)
        assert valid is True
        assert errors == []
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_validate_invalid_output(self, invalid_extraction_output):
        """Extractor should catch invalid output."""
        extractor = NutritionExtractor()
        valid, errors = extractor.validate_output(invalid_extraction_output)
        assert valid is False
        assert len(errors) > 0


class TestPromptLoading:
    """Tests for prompt file loading."""
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_nutrition_prompt_loads(self):
        """Nutrition prompt should load correctly."""
        extractor = NutritionExtractor()
        prompt = extractor.prompt
        assert len(prompt) > 0
        assert "nutrition" in prompt.lower()
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_aminoacid_prompt_loads(self):
        """Amino acid prompt should load correctly."""
        extractor = AminoacidExtractor()
        prompt = extractor.prompt
        assert len(prompt) > 0
        assert "amino" in prompt.lower()
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_nutrition_prompt_contains_key_instructions(self):
        """Nutrition prompt should contain key extraction instructions."""
        extractor = NutritionExtractor()
        assert "HALLUCINATION" in extractor.prompt.upper()
        assert "null" in extractor.prompt.lower()
    
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'})
    def test_aminoacid_prompt_contains_categories(self):
        """Amino acid prompt should mention amino acid categories."""
        extractor = AminoacidExtractor()
        assert "EAA" in extractor.prompt.upper()
        assert "BCAA" in extractor.prompt.upper()


class TestMockedExtraction:
    """Tests using mocked API responses."""
    
    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_openai_extraction_flow(self, mock_openai_class, mock_openai_response, tmp_path):
        """Test extraction flow with mocked OpenAI response."""
        # Create a dummy image file
        test_image = tmp_path / "nutrients_profile.png"
        test_image.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01')
        
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        # Run extraction
        extractor = NutritionExtractor(provider="openai")
        result = extractor.extract(test_image, "test_product")
        
        # Verify
        assert result.product_id == "test_product_001"
        assert result.valid is True
        assert result.provider == "openai"
        assert result.profile_type == "nutrients"
        assert result.extracted_fields["protein_g_per_serving"] == 25


class TestExtractionResult:
    """Tests for ExtractionResult model."""
    
    def test_extraction_result_creation(self, valid_nutrition_output):
        """ExtractionResult should be creatable with valid data."""
        result = ExtractionResult(
            product_id=valid_nutrition_output["product_id"],
            profile_type="nutrients",
            extracted_fields=valid_nutrition_output["extracted_fields"],
            raw_evidence=valid_nutrition_output["raw_evidence"],
            quality=valid_nutrition_output["quality"],
            provider="openai",
            model="gpt-4o",
            valid=True,
        )
        
        assert result.product_id == "test_product_001"
        assert result.profile_type == "nutrients"
        assert result.valid is True
        assert result.validation_errors == []
    
    def test_extraction_result_with_errors(self):
        """ExtractionResult should store validation errors."""
        result = ExtractionResult(
            product_id="test",
            profile_type="aminoacid",
            extracted_fields={},
            raw_evidence={},
            quality={},
            provider="gemini",
            model="gemini-2.0-flash",
            valid=False,
            validation_errors=["Missing required field: eaas"],
        )
        
        assert result.valid is False
        assert result.profile_type == "aminoacid"
        assert len(result.validation_errors) == 1
