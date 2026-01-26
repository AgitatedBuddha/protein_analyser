"""
Extractors Package

Provides modular extractors for different label types.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

from .base import (
    BaseExtractor,
    ExtractionResult,
    detect_profile_type,
    get_brand_from_path,
)
from .nutrition import NutritionExtractor
from .aminoacid import AminoacidExtractor


class ProductInfo(BaseModel):
    """Product pricing and quantity information."""
    weight_kg: Optional[float] = None
    price_inr: Optional[float] = None
    price_per_kg: Optional[float] = None
    servings_per_pack: Optional[float] = None
    price_per_serving: Optional[float] = None


class BrandExtractionResult(BaseModel):
    """Combined extraction result for a brand."""
    brand: str
    extraction_timestamp: str
    product_info: Optional[ProductInfo] = None
    nutrients: Optional[dict] = None
    aminoacids: Optional[dict] = None


# Extractor registry
EXTRACTORS = {
    "nutrients": NutritionExtractor,
    "aminoacid": AminoacidExtractor,
}


def get_extractor(
    profile_type: Literal["nutrients", "aminoacid"],
    provider: Literal["openai", "gemini"] = "gemini",
    model: Optional[str] = None,
) -> BaseExtractor:
    """
    Factory function to get the appropriate extractor.
    
    Args:
        profile_type: Type of profile to extract
        provider: LLM provider (openai or gemini)
        model: Optional model override
    
    Returns:
        Configured extractor instance
    """
    if profile_type not in EXTRACTORS:
        raise ValueError(f"Unknown profile type: {profile_type}. Available: {list(EXTRACTORS.keys())}")
    
    extractor_class = EXTRACTORS[profile_type]
    return extractor_class(provider=provider, model=model)


def extract_brand(
    brand_dir: str | Path,
    provider: Literal["openai", "gemini"] = "gemini",
    model: Optional[str] = None,
    extract_nutrients: bool = True,
    extract_aminoacids: bool = True,
) -> BrandExtractionResult:
    """
    Extract all requested profiles for a brand.
    
    Args:
        brand_dir: Path to brand directory
        provider: LLM provider
        model: Optional model override
        extract_nutrients: Whether to extract nutrition profile
        extract_aminoacids: Whether to extract amino acid profile
    
    Returns:
        BrandExtractionResult with requested extractions
    """
    brand_dir = Path(brand_dir)
    if not brand_dir.is_dir():
        raise ValueError(f"Not a directory: {brand_dir}")
    
    brand_name = brand_dir.name
    result = BrandExtractionResult(
        brand=brand_name,
        extraction_timestamp=datetime.now().isoformat(),
    )
    
    # Extract nutrients if requested
    if extract_nutrients:
        nutrients_img = NutritionExtractor.find_image(brand_dir)
        if nutrients_img:
            extractor = NutritionExtractor(provider=provider, model=model)
            extraction = extractor.extract(nutrients_img, f"{brand_name}_nutrients")
            result.nutrients = extraction.model_dump()
    
    # Extract amino acids if requested
    if extract_aminoacids:
        amino_img = AminoacidExtractor.find_image(brand_dir)
        if amino_img:
            extractor = AminoacidExtractor(provider=provider, model=model)
            extraction = extractor.extract(amino_img, f"{brand_name}_aminoacid")
            result.aminoacids = extraction.model_dump()
    
    return result


__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "ProductInfo",
    "BrandExtractionResult",
    "NutritionExtractor",
    "AminoacidExtractor",
    "get_extractor",
    "extract_brand",
    "detect_profile_type",
    "get_brand_from_path",
    "EXTRACTORS",
]
