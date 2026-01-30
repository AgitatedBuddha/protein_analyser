"""
Scoring Engine for Protein Powder Analysis

Implements the scoring_spec.yml logic to score brands across different goals:
- cut: Optimize for cutting (high protein efficiency, low calories)
- bulk: Optimize for bulking (high protein, good amino profile)
- clean: Optimize for clean eating (low sodium, low additives)
"""

import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


# Load scoring spec
SKILLS_DIR = Path(__file__).parent / "skills"
SCORING_SPEC_PATH = SKILLS_DIR / "scoring_spec.yml"


@dataclass
class ComputedMetrics:
    """Computed metrics from brand data."""
    protein_pct: Optional[float] = None
    protein_per_100_kcal: Optional[float] = None
    eaas_pct_raw: Optional[float] = None
    eaas_pct: Optional[float] = None
    bcaas_pct_of_eaas: Optional[float] = None
    non_protein_macros_g: Optional[float] = None
    leucine_g_per_serving: Optional[float] = None
    protein_g_per_serving: Optional[float] = None
    protein_g_per_serving: Optional[float] = None
    sodium_mg: Optional[float] = None
    added_sugar_g: Optional[float] = None
    taurine_g: Optional[float] = None
    heavy_metals_tested: Optional[bool] = None
    missing_macros: bool = False
    sodium_reported_zero: bool = False


@dataclass
class AminoSpikingResult:
    """Result of amino spiking detection."""
    suspected: bool = False
    triggered_rules: list = field(default_factory=list)
    glycine_ratio: Optional[float] = None


@dataclass
class ModeScore:
    """Score for a specific mode (cut/bulk/clean)."""
    mode: str
    total_score: float
    hard_rejected: bool = False
    rejection_reason: Optional[str] = None
    component_scores: dict = field(default_factory=dict)
    penalty_deduction: float = 0.0


@dataclass
class BrandScores:
    """Complete scoring result for a brand."""
    brand: str
    metrics: ComputedMetrics
    amino_spiking: AminoSpikingResult
    cut_score: Optional[ModeScore] = None
    bulk_score: Optional[ModeScore] = None
    clean_score: Optional[ModeScore] = None


class Scorer:
    """
    Scoring engine that implements scoring_spec.yml logic.
    """
    
    def __init__(self, spec_path: Path = SCORING_SPEC_PATH):
        """Load scoring specification."""
        with open(spec_path) as f:
            self.spec = yaml.safe_load(f)["scoring_spec"]
        
        self.normalization_ranges = self.spec["normalization_ranges"]
        self.penalties = self.spec["penalties"]
        self.modes = self.spec["modes"]
        self.spiking_rules = self.spec["amino_spiking_detection"]
    
    def load_brand_data(self, brand_json_path: Path) -> dict:
        """Load brand extraction data from JSON."""
        with open(brand_json_path) as f:
            return json.load(f)
    
    def compute_metrics(self, data: dict) -> ComputedMetrics:
        """Compute all metrics from brand data."""
        nutrients = data.get("nutrients", {}).get("extracted_fields", {})
        aminoacids = data.get("aminoacids", {}).get("extracted_fields", {})
        
        # Get base values
        serving_size_g = nutrients.get("serving_size_g")
        protein_g = nutrients.get("protein_g_per_serving")
        energy_kcal = nutrients.get("energy_kcal_per_serving")
        carbs_g = nutrients.get("carbohydrates_g_per_serving")
        fat_g = nutrients.get("total_fat_g_per_serving")
        sodium_mg = nutrients.get("sodium_mg_per_serving")
        added_sugar_g = nutrients.get("added_sugar_g_per_serving")
        heavy_metals_tested = nutrients.get("heavy_metals_tested")
        
        # Get amino acid values
        eaas = aminoacids.get("eaas", {})
        bcaas = eaas.get("bcaas", {})
        seaas = aminoacids.get("seaas", {})
        
        # Normalize amino acids to per_serving if needed
        serving_basis = aminoacids.get("serving_basis", "per_serving")
        normalization_factor = 1.0
        if serving_basis == "per_100g" and serving_size_g:
            normalization_factor = serving_size_g / 100
        
        eaas_g = eaas.get("total_g")
        bcaas_g = bcaas.get("total_g")
        leucine_g = bcaas.get("leucine_g")
        leucine_g = bcaas.get("leucine_g")
        glycine_g = seaas.get("glycine_g")
        taurine_g = seaas.get("taurine_g")
        
        # Apply normalization
        if eaas_g and normalization_factor != 1.0:
            eaas_g *= normalization_factor
        if bcaas_g and normalization_factor != 1.0:
            bcaas_g *= normalization_factor
        if leucine_g and normalization_factor != 1.0:
            leucine_g *= normalization_factor
        if glycine_g and normalization_factor != 1.0:
            glycine_g *= normalization_factor
        if taurine_g and normalization_factor != 1.0:
            taurine_g *= normalization_factor
        
        metrics = ComputedMetrics()
        
        # Compute core metrics
        if protein_g and serving_size_g:
            metrics.protein_pct = (protein_g / serving_size_g) * 100
        
        if protein_g and energy_kcal:
            metrics.protein_per_100_kcal = (protein_g / energy_kcal) * 100
        
        if eaas_g and protein_g:
            metrics.eaas_pct_raw = eaas_g / protein_g
            metrics.eaas_pct = min(metrics.eaas_pct_raw, 1.0)
        
        if bcaas_g and eaas_g:
            metrics.bcaas_pct_of_eaas = bcaas_g / eaas_g
        
        if carbs_g is not None and fat_g is not None:
            metrics.non_protein_macros_g = carbs_g + fat_g
        
        metrics.leucine_g_per_serving = leucine_g
        metrics.protein_g_per_serving = protein_g
        metrics.sodium_mg = sodium_mg
        metrics.added_sugar_g = added_sugar_g
        metrics.taurine_g = taurine_g
        metrics.heavy_metals_tested = heavy_metals_tested
        
        # Check label credibility flags
        if protein_g is None or carbs_g is None or fat_g is None:
            metrics.missing_macros = True
        
        if sodium_mg is not None and sodium_mg == 0:
            metrics.sodium_reported_zero = True
        
        return metrics
    
    def detect_amino_spiking(self, metrics: ComputedMetrics, data: dict) -> AminoSpikingResult:
        """Detect potential amino spiking based on rules."""
        result = AminoSpikingResult()
        
        # Get glycine for ratio calculation
        aminoacids = data.get("aminoacids", {}).get("extracted_fields", {})
        seaas = aminoacids.get("seaas", {})
        glycine_g = seaas.get("glycine_g")
        
        if glycine_g and metrics.protein_g_per_serving:
            result.glycine_ratio = glycine_g / metrics.protein_g_per_serving
            
            # Rule: glycine_disproportion
            if result.glycine_ratio > 0.05:
                result.triggered_rules.append("glycine_disproportion")
        
        # Rule: low_eaas
        if metrics.eaas_pct and metrics.eaas_pct < 0.40:
            result.triggered_rules.append("low_eaas")
        
        # Rule: bcaas_dominant
        if metrics.bcaas_pct_of_eaas and metrics.bcaas_pct_of_eaas > 0.60:
            result.triggered_rules.append("bcaas_dominant")
        
        # Rule: eaas_exceed_protein
        if metrics.eaas_pct_raw and metrics.eaas_pct_raw > 1.0:
            result.triggered_rules.append("eaas_exceed_protein")
            
        # Rule: taurine_present (NEW v1.4)
        if metrics.taurine_g and metrics.taurine_g > 0:
            result.triggered_rules.append("taurine_present")
        
        # Check trigger threshold
        min_rules = self.spiking_rules["trigger"]["min_rules_required"]
        result.suspected = len(result.triggered_rules) >= min_rules
        
        return result
    
    def normalize_value(self, metric_name: str, value: Optional[float]) -> float:
        """Normalize a value to 0-1 based on ranges."""
        if value is None:
            return 0.0
        
        ranges = self.normalization_ranges.get(metric_name, {})
        if not ranges:
            return 0.0
        
        # Parse ranges and find matching bucket
        for range_str, score in ranges.items():
            if self._value_matches_range(value, range_str):
                return score
        
        return 0.0
    
    def get_penalty_value(self, metric_name: str, value: Optional[float]) -> float:
        """Get penalty value for a metric."""
        if value is None:
            return 0.0
        
        penalty_ranges = self.penalties.get(metric_name, {})
        if not penalty_ranges:
            # Fallback: check normalization_ranges and invert (Score 1.0 = Penalty 0.0)
            norm_ranges = self.normalization_ranges.get(metric_name)
            if norm_ranges:
                score = self.normalize_value(metric_name, value)
                return 1.0 - score
            return 0.0
        
        for range_str, penalty in penalty_ranges.items():
            if self._value_matches_range(value, range_str):
                return penalty
        
        return 0.0
    
    def _value_matches_range(self, value: float, range_str: str) -> bool:
        """Check if value matches a range string like '<65', '65-72', '>80'."""
        range_str = range_str.replace("%", "")  # Remove percentage signs
        
        if range_str.startswith(">="):
            threshold = float(range_str[2:])
            return value >= threshold
        elif range_str.startswith(">"):
            threshold = float(range_str[1:])
            return value > threshold
        elif range_str.startswith("<="):
            threshold = float(range_str[2:])
            return value <= threshold
        elif range_str.startswith("<"):
            threshold = float(range_str[1:])
            return value < threshold
        elif "-" in range_str:
            low, high = range_str.split("-")
            return float(low) <= value <= float(high)
        else:
            return value == float(range_str)
    
    def _check_hard_reject(self, mode_spec: dict, metrics: ComputedMetrics, 
                          amino_spiking: AminoSpikingResult) -> tuple[bool, Optional[str]]:
        """Check if brand should be hard rejected for this mode."""
        hard_reject = mode_spec.get("hard_reject", {})
        
        for metric_name, threshold in hard_reject.items():
            if metric_name == "amino_spiking_suspected":
                if threshold and amino_spiking.suspected:
                    return True, "amino_spiking_suspected"
            elif metric_name == "added_sugar_present":
                # TODO: implement added sugar detection
                pass
            else:
                value = getattr(metrics, metric_name, None)
                if value is not None and self._value_matches_range(value, threshold):
                    return True, f"{metric_name} {threshold}"
        
        return False, None

    def _apply_label_credibility_penalties(self, mode: str, metrics: ComputedMetrics) -> float:
        """Calculate score deduction from label credibility issues."""
        spec = self.spec.get("label_credibility", {})
        effects = spec.get("effects", {}).get(mode, {})
        
        penalty = 0.0
        
        # Check credibility flags
        flags_triggered = []
        if metrics.missing_macros:
            flags_triggered.append("missing_macros")
        if metrics.sodium_reported_zero:
            flags_triggered.append("sodium_reported_zero")
        
        # Apply mode-specific effects
        if flags_triggered:
            # Check for hard reject in clean mode
            if effects.get("hard_reject") and flags_triggered:
                # This return logic needs to be handled in score_mode via a separate check
                # For now, we return 1.0 penalty to simulate hard reject if needed, 
                # but better to handle rejection explicitly. 
                # Let's just return the numeric penalty here.
                pass
                
            if "penalty" in effects:
                penalty += effects["penalty"]
                
        return penalty

    def _check_credibility_reject(self, mode: str, metrics: ComputedMetrics) -> bool:
        """Check if label credibility issues cause a hard reject."""
        spec = self.spec.get("label_credibility", {})
        effects = spec.get("effects", {}).get(mode, {})
        
        if effects.get("hard_reject"):
            if metrics.missing_macros or metrics.sodium_reported_zero:
                return True
        return False

    def _check_safety_reject(self, mode: str, metrics: ComputedMetrics) -> bool:
        """Check if safety flags cause a hard reject."""
        spec = self.spec.get("safety_flags", {})
        enforcement = spec.get("enforcement", {}).get(mode, {})
        
        if enforcement.get("hard_reject_if_unknown"):
            # If heavy metals tested is None (unknown) or False, reject
            if not metrics.heavy_metals_tested:
                return True
        return False
    
    def score_mode(self, mode: str, metrics: ComputedMetrics, 
                   amino_spiking: AminoSpikingResult) -> ModeScore:
        """Score a brand for a specific mode."""
        mode_spec = self.modes[mode]
        
        # Check hard rejection
        rejected, reason = self._check_hard_reject(mode_spec, metrics, amino_spiking)
        if rejected:
            return ModeScore(
                mode=mode,
                total_score=0.0,
                hard_rejected=True,
                rejection_reason=reason
            )
        
        # Check label credibility hard reject (NEW v1.4)
        if self._check_credibility_reject(mode, metrics):
             return ModeScore(
                mode=mode,
                total_score=0.0,
                hard_rejected=True,
                rejection_reason="label_credibility_issues"
            )

        # Check safety hard reject (NEW v1.4)
        if self._check_safety_reject(mode, metrics):
             return ModeScore(
                mode=mode,
                total_score=0.0,
                hard_rejected=True,
                rejection_reason="safety_flags_unmet"
            )
        
        # Calculate weighted score
        weights = mode_spec.get("weights", {})
        component_scores = {}
        total_score = 0.0
        
        for metric_name, weight in weights.items():
            value = getattr(metrics, metric_name, None)
            normalized = self.normalize_value(metric_name, value)
            component_scores[metric_name] = {
                "raw_value": value,
                "normalized": normalized,
                "weight": weight,
                "contribution": normalized * weight
            }
            total_score += normalized * weight
        
        # Apply penalties (for cut and bulk modes)
        penalty_weights = mode_spec.get("penalty_weights", {})
        total_penalty = 0.0
        
        for metric_name, weight in penalty_weights.items():
            value = getattr(metrics, metric_name, None)
            penalty = self.get_penalty_value(metric_name, value)
            component_scores[f"penalty_{metric_name}"] = {
                "raw_value": value,
                "penalty": penalty,
                "weight": weight,
                "deduction": penalty * weight
            }
            total_penalty += penalty * weight
            
        # Apply label credibility penalty (NEW v1.4)
        credibility_penalty = self._apply_label_credibility_penalties(mode, metrics)
        if credibility_penalty > 0:
            component_scores["penalty_label_credibility"] = {
                "raw_value": 1.0,
                "penalty": credibility_penalty,
                "weight": 1.0, 
                "deduction": credibility_penalty
            }
            total_penalty += credibility_penalty
        
        # Apply penalty deduction: final = base * (1 - penalty)
        final_score = total_score * (1 - total_penalty)
        
        return ModeScore(
            mode=mode,
            total_score=round(final_score, 4),
            component_scores=component_scores,
            penalty_deduction=round(total_penalty, 4)
        )
    
    def score_brand(self, data: dict) -> BrandScores:
        """Score a brand across all modes."""
        brand = data.get("brand", "unknown")
        
        # Compute metrics
        metrics = self.compute_metrics(data)
        
        # Detect amino spiking
        amino_spiking = self.detect_amino_spiking(metrics, data)
        
        # Score all modes
        cut_score = self.score_mode("cut", metrics, amino_spiking)
        bulk_score = self.score_mode("bulk", metrics, amino_spiking)
        clean_score = self.score_mode("clean", metrics, amino_spiking)
        
        return BrandScores(
            brand=brand,
            metrics=metrics,
            amino_spiking=amino_spiking,
            cut_score=cut_score,
            bulk_score=bulk_score,
            clean_score=clean_score,
        )
    
    def score_brand_from_file(self, json_path: Path) -> BrandScores:
        """Load and score a brand from JSON file."""
        data = self.load_brand_data(json_path)
        return self.score_brand(data)


def score_all_brands(output_dir: Path = Path("output")) -> list[BrandScores]:
    """Score all brands in the output directory."""
    scorer = Scorer()
    results = []
    
    for brand_dir in output_dir.iterdir():
        if not brand_dir.is_dir() or brand_dir.name.startswith("."):
            continue
        
        json_path = brand_dir / f"{brand_dir.name}.json"
        if json_path.exists():
            scores = scorer.score_brand_from_file(json_path)
            results.append(scores)
    
    return results


def get_leaderboard(results: list[BrandScores], mode: str = "cut") -> list[tuple[str, float, bool]]:
    """Get sorted leaderboard for a mode."""
    leaderboard = []
    
    for scores in results:
        mode_score = getattr(scores, f"{mode}_score")
        if mode_score:
            leaderboard.append((
                scores.brand,
                mode_score.total_score,
                mode_score.hard_rejected
            ))
    
    # Sort by score descending, rejected brands at bottom
    leaderboard.sort(key=lambda x: (not x[2], x[1]), reverse=True)
    
    return leaderboard
