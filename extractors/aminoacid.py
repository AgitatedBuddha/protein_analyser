"""
Amino Acid Profile Extractor

Extracts amino acid composition from protein powder labels.
Computes category totals when individual values are available.
"""

from pathlib import Path
from typing import Optional

from .base import BaseExtractor, ExtractionResult


# Amino acid category definitions
# BCAAs are now nested under EAAs
BCAAS = ["leucine_g", "isoleucine_g", "valine_g"]

# Other EAAs (non-BCAA essential amino acids)
OTHER_EAAS = ["lysine_g", "methionine_g", "phenylalanine_g", 
              "threonine_g", "tryptophan_g", "histidine_g"]

SEAAS = ["arginine_g", "cysteine_g", "glycine_g", "proline_g", "tyrosine_g"]

NEAAS = ["serine_g", "alanine_g", "aspartic_acid_g", "glutamic_acid_g"]


class AminoacidExtractor(BaseExtractor):
    """
    Extractor for amino acid profile labels.
    
    Extracts: EAAs (with BCAAs nested), SEAAs, NEAAs with individual values where visible.
    Computes category totals locally when individual values are available.
    """
    
    PROFILE_TYPE = "aminoacid"
    PROMPT_FILE = "extract_aminoacid_profile_v1.prompt.md"
    SCHEMA_FILE = "extract_aminoacid_profile_v1.schema.json"
    
    # File patterns to search for
    FILE_PATTERNS = [
        "aminoacid_profile.*",
        "amino_acid_profile.*",
        "aminoacids_profile.*",
        "amino_profile.*",
        "amino*.*",
    ]
    
    @classmethod
    def find_image(cls, brand_dir: Path) -> Optional[Path]:
        """Find amino acid profile image in a brand directory."""
        for pattern in cls.FILE_PATTERNS:
            matches = list(brand_dir.glob(pattern))
            for match in matches:
                if match.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    return match
        return None
    
    def extract(self, image_path: str | Path, product_id: str) -> ExtractionResult:
        """
        Extract amino acid profile and compute category totals.
        
        Overrides base extract to add computation of totals from individual values.
        """
        # Get base extraction result
        result = super().extract(image_path, product_id)
        
        # Compute totals from individual values
        result = self._compute_totals(result)
        
        return result
    
    def _compute_totals(self, result: ExtractionResult) -> ExtractionResult:
        """
        Compute category totals from individual amino acid values.
        
        Only computes if:
        1. The total is currently null
        2. Individual values are available
        """
        fields = result.extracted_fields
        computed = []
        
        eaas = fields.get("eaas", {})
        bcaas = eaas.get("bcaas", {})
        
        # Compute BCAAs total (nested under EAAs)
        if bcaas.get("total_g") is None:
            bcaas_total = self._sum_values(bcaas, BCAAS)
            if bcaas_total is not None:
                bcaas["total_g"] = round(bcaas_total, 3)
                computed.append(f"eaas.bcaas.total_g={bcaas_total:.3f}")
        
        # Compute EAAs total (BCAAs + other EAAs)
        if eaas.get("total_g") is None:
            # Get BCAAs sum (either from computed or existing total)
            bcaas_sum = bcaas.get("total_g")
            if bcaas_sum is None:
                bcaas_sum = self._sum_values(bcaas, BCAAS)
            
            # Get other EAAs sum
            other_eaas_sum = self._sum_values(eaas, OTHER_EAAS)
            
            if bcaas_sum is not None and other_eaas_sum is not None:
                eaas_total = bcaas_sum + other_eaas_sum
                eaas["total_g"] = round(eaas_total, 3)
                computed.append(f"eaas.total_g={eaas_total:.3f}")
        
        # Compute SEAAs total
        seaas = fields.get("seaas", {})
        if seaas.get("total_g") is None:
            seaas_total = self._sum_values(seaas, SEAAS)
            if seaas_total is not None:
                seaas["total_g"] = round(seaas_total, 3)
                computed.append(f"seaas.total_g={seaas_total:.3f}")
        
        # Compute NEAAs total
        neaas = fields.get("neaas", {})
        if neaas.get("total_g") is None:
            neaas_total = self._sum_values(neaas, NEAAS)
            if neaas_total is not None:
                neaas["total_g"] = round(neaas_total, 3)
                computed.append(f"neaas.total_g={neaas_total:.3f}")
        
        # Update result with computed fields note
        quality = result.quality.copy()
        if computed:
            quality["computed_fields"] = computed
        
        # Return updated result
        return ExtractionResult(
            product_id=result.product_id,
            profile_type=result.profile_type,
            extracted_fields=fields,
            raw_evidence=result.raw_evidence,
            quality=quality,
            provider=result.provider,
            model=result.model,
            valid=result.valid,
            validation_errors=result.validation_errors,
        )
    
    def _sum_values(self, category: dict, keys: list[str]) -> Optional[float]:
        """
        Sum values for given keys if all are available.
        
        Returns None if any required value is missing.
        """
        values = []
        for key in keys:
            value = category.get(key)
            if value is None:
                # Can't compute if any value is missing
                return None
            values.append(value)
        
        return sum(values)
