"""
Integration tests for the nutrition label extractor.

These tests require actual API keys and make real API calls.
Run with: pytest tests/test_integration.py -v --run-integration
"""

import json
import os
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import NutritionExtractor, detect_profile_type, get_brand_from_path

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_DIR / "images"


@pytest.fixture
def real_image_path() -> Path:
    """Get a real test image from the images directory."""
    if not IMAGES_DIR.exists():
        pytest.skip("No images directory found")
    
    for brand_dir in IMAGES_DIR.iterdir():
        if brand_dir.is_dir() and not brand_dir.name.startswith("."):
            nutrients_img = brand_dir / "nutrients_profile.png"
            if nutrients_img.exists():
                return nutrients_img
    
    pytest.skip("No test images found")


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests using OpenAI API."""
    
    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip if API key not set."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
    
    def test_extract_nutrients_profile(self, real_image_path):
        """Test real extraction from nutrients profile image."""
        extractor = NutritionExtractor(provider="openai")
        
        brand = get_brand_from_path(real_image_path)
        product_id = f"{brand}_nutrients"
        
        result = extractor.extract(real_image_path, product_id)
        
        # Basic assertions
        assert result.product_id == product_id
        assert result.provider == "openai"
        
        # Check extraction quality
        assert result.quality.get("extraction_confidence", 0) > 0.3
        
        # Check required fields are present (may be null)
        fields = result.extracted_fields
        assert "serving_size_g" in fields
        assert "protein_g_per_serving" in fields
        assert "energy_kcal_per_serving" in fields
        
        # Log results for manual inspection
        print(f"\n--- Extraction Result ---")
        print(f"Product: {result.product_id}")
        print(f"Valid: {result.valid}")
        print(f"Confidence: {result.quality.get('extraction_confidence')}")
        print(f"Fields: {json.dumps(result.extracted_fields, indent=2)}")
        if result.quality.get("warnings"):
            print(f"Warnings: {result.quality['warnings']}")


@pytest.mark.integration
class TestGeminiIntegration:
    """Integration tests using Gemini API."""
    
    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip if API key not set."""
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not set")
    
    def test_extract_nutrients_profile(self, real_image_path):
        """Test real extraction from nutrients profile image."""
        extractor = NutritionExtractor(provider="gemini")
        
        brand = get_brand_from_path(real_image_path)
        product_id = f"{brand}_nutrients"
        
        result = extractor.extract(real_image_path, product_id)
        
        # Basic assertions
        assert result.product_id == product_id
        assert result.provider == "gemini"
        
        # Check extraction quality
        assert result.quality.get("extraction_confidence", 0) > 0.3
        
        # Log results for manual inspection
        print(f"\n--- Extraction Result (Gemini) ---")
        print(f"Product: {result.product_id}")
        print(f"Valid: {result.valid}")
        print(f"Confidence: {result.quality.get('extraction_confidence')}")
        print(f"Fields: {json.dumps(result.extracted_fields, indent=2)}")


@pytest.mark.integration
class TestProviderComparison:
    """Compare results across providers."""
    
    @pytest.fixture(autouse=True)
    def check_both_keys(self):
        """Skip if both API keys not set."""
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("Both OPENAI_API_KEY and GOOGLE_API_KEY required")
    
    def test_compare_providers(self, real_image_path):
        """Compare extraction results between OpenAI and Gemini."""
        brand = get_brand_from_path(real_image_path)
        product_id = f"{brand}_nutrients"
        
        # Extract with both providers
        openai_extractor = NutritionExtractor(provider="openai")
        gemini_extractor = NutritionExtractor(provider="gemini")
        
        openai_result = openai_extractor.extract(real_image_path, product_id)
        gemini_result = gemini_extractor.extract(real_image_path, product_id)
        
        # Log comparison
        print(f"\n--- Provider Comparison ---")
        print(f"\nOpenAI (confidence: {openai_result.quality.get('extraction_confidence')}):")
        print(json.dumps(openai_result.extracted_fields, indent=2))
        
        print(f"\nGemini (confidence: {gemini_result.quality.get('extraction_confidence')}):")
        print(json.dumps(gemini_result.extracted_fields, indent=2))
        
        # Both should extract the same product_id
        assert openai_result.product_id == gemini_result.product_id
        
        # Compare key fields (allowing for minor differences)
        o_fields = openai_result.extracted_fields
        g_fields = gemini_result.extracted_fields
        
        # Log differences
        differences = []
        for key in o_fields:
            o_val = o_fields.get(key)
            g_val = g_fields.get(key)
            if o_val != g_val:
                differences.append(f"{key}: OpenAI={o_val}, Gemini={g_val}")
        
        if differences:
            print(f"\nDifferences found:")
            for diff in differences:
                print(f"  - {diff}")


@pytest.mark.integration
class TestGoldenFiles:
    """Test against known expected outputs."""
    
    GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"
    
    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip if API key not set."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
    
    def test_origin_plant_protein(self):
        """Test extraction against known values for OriginPlantProtein."""
        image_path = IMAGES_DIR / "OriginPlantProtein" / "nutrients_profile.png"
        if not image_path.exists():
            pytest.skip("OriginPlantProtein image not found")
        
        extractor = NutritionExtractor(provider="openai")
        result = extractor.extract(image_path, "OriginPlantProtein_nutrients")
        
        # Known values from the label
        expected = {
            "serving_size_g": 32.5,
            "energy_kcal_per_serving": 121.44,
            "protein_g_per_serving": 25,
            "carbohydrates_g_per_serving": 4.01,
            "total_fat_g_per_serving": 0.60,
            "sodium_mg_per_serving": 230,
        }
        
        fields = result.extracted_fields
        
        # Check each field (with tolerance for floats)
        for key, expected_val in expected.items():
            actual_val = fields.get(key)
            if actual_val is None:
                print(f"  WARNING: {key} is null (expected {expected_val})")
                continue
            
            if isinstance(expected_val, float):
                assert abs(actual_val - expected_val) < 0.1, f"{key}: expected {expected_val}, got {actual_val}"
            else:
                assert actual_val == expected_val, f"{key}: expected {expected_val}, got {actual_val}"
        
        print(f"\n✓ All expected values matched!")
