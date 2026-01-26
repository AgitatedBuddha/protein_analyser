"""
Pytest configuration and shared fixtures for nutrition label extraction tests.
"""

import json
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PROJECT_DIR = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_DIR / "skills"


@pytest.fixture
def sample_nutrition_schema() -> dict:
    """Load the nutrition extraction schema."""
    schema_path = SKILLS_DIR / "extract_nutrition_label_v1.schema.json"
    return json.loads(schema_path.read_text())


@pytest.fixture
def sample_aminoacid_schema() -> dict:
    """Load the amino acid extraction schema."""
    schema_path = SKILLS_DIR / "extract_aminoacid_profile_v1.schema.json"
    return json.loads(schema_path.read_text())


@pytest.fixture
def sample_nutrition_prompt() -> str:
    """Load the nutrition extraction prompt."""
    prompt_path = SKILLS_DIR / "extract_nutrition_label_v1.prompt.md"
    return prompt_path.read_text()


@pytest.fixture
def sample_aminoacid_prompt() -> str:
    """Load the amino acid extraction prompt."""
    prompt_path = SKILLS_DIR / "extract_aminoacid_profile_v1.prompt.md"
    return prompt_path.read_text()


@pytest.fixture
def valid_nutrition_output() -> dict:
    """A valid nutrition extraction output that should pass schema validation."""
    return {
        "product_id": "test_product_001",
        "extracted_fields": {
            "serving_size_g": 32.5,
            "energy_kcal_per_serving": 121.44,
            "protein_g_per_serving": 25,
            "carbohydrates_g_per_serving": 4.01,
            "total_fat_g_per_serving": 0.60,
            "sodium_mg_per_serving": 230
        },
        "raw_evidence": {
            "label_basis_detected": "per_serving",
            "visible_rows": [
                {"nutrient_text": "Energy Value", "value_text": "121.44", "unit_text": "kcal"},
                {"nutrient_text": "Protein", "value_text": "25", "unit_text": "g"},
            ],
            "protein_composition_visible": False,
            "protein_composition_notes": ""
        },
        "quality": {
            "extraction_confidence": 0.95,
            "ambiguities": [],
            "warnings": []
        }
    }


@pytest.fixture
def valid_aminoacid_output() -> dict:
    """A valid amino acid extraction output that should pass schema validation."""
    return {
        "product_id": "test_product_001_amino",
        "extracted_fields": {
            "serving_basis": "per_serving",
            "eaas": {
                "total_g": 9.1,
                "bcaas": {
                    "total_g": 4.713,
                    "leucine_g": None,
                    "isoleucine_g": None,
                    "valine_g": None
                },
                "lysine_g": None,
                "methionine_g": None,
                "phenylalanine_g": None,
                "threonine_g": None,
                "tryptophan_g": None,
                "histidine_g": None
            },
            "seaas": {
                "total_g": 4.1,
                "arginine_g": None,
                "cysteine_g": None,
                "glycine_g": None,
                "proline_g": None,
                "tyrosine_g": None
            },
            "neaas": {
                "total_g": 8.1,
                "serine_g": None,
                "alanine_g": None,
                "aspartic_acid_g": None,
                "glutamic_acid_g": None
            }
        },
        "raw_evidence": {
            "eaas_listed": ["Isoleucine", "Leucine", "Valine", "Lysine", "Methionine", "Phenylalanine", "Threonine", "Tryptophan", "Histidine"],
            "seaas_listed": ["Arginine", "Cysteine", "Glycine", "Proline", "Tyrosine"],
            "neaas_listed": ["Serine", "Alanine", "Aspartic Acid", "Glutamic Acid"],
            "individual_values_visible": False,
            "notes": "Only category totals shown"
        },
        "quality": {
            "extraction_confidence": 0.8,
            "ambiguities": [],
            "warnings": []
        }
    }


@pytest.fixture
def invalid_extraction_output() -> dict:
    """An invalid extraction output missing required fields."""
    return {
        "product_id": "test_product_002",
        "extracted_fields": {
            "serving_size_g": 30,
            # Missing other required fields
        },
        "raw_evidence": {
            "label_basis_detected": "per_serving",
            # Missing required fields
        },
        "quality": {
            "extraction_confidence": 0.5,
        }
    }


@pytest.fixture
def mock_openai_response(valid_nutrition_output: dict):
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(valid_nutrition_output)
    return mock_response


@pytest.fixture
def mock_gemini_response(valid_nutrition_output: dict):
    """Mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(valid_nutrition_output)
    return mock_response


@pytest.fixture
def sample_image_path() -> Path:
    """Path to a sample test image (if exists)."""
    # Try to find a real image in the project
    images_dir = PROJECT_DIR / "images"
    if images_dir.exists():
        for brand_dir in images_dir.iterdir():
            if brand_dir.is_dir() and not brand_dir.name.startswith("."):
                for img in brand_dir.glob("*.png"):
                    return img
    
    # Fallback to fixtures directory
    return FIXTURES_DIR / "sample_label.png"


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require API keys",
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API key)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration"):
        return
    
    skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
