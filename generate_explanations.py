"""
Generate AI explanations for all brands and store in Supabase.

Run this after populating the database with brands/nutrients/scores.
"""

import os
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Import Supabase client
from db_builder import get_supabase_client

# Scoring context for the LLM
SCORING_CONTEXT = """
You are analyzing protein powder scores based on this scoring specification:

SCORING MODES:
1. CUT MODE - Optimizes for cutting (weight loss while preserving muscle)
   - Hard reject if: protein_per_100_kcal < 18 OR leucine_g_per_serving < 2.2
   - Weights: protein_per_100_kcal (40%), leucine (30%), protein_pct (20%), EAAs (10%)
   - Penalties: high sodium, high non-protein macros

2. BULK MODE - Optimizes for muscle building
   - No hard rejects
   - Weights: protein_pct (35%), EAAs (30%), leucine (25%), protein_g (10%)
   - Minimal penalties

3. CLEAN MODE - Optimizes for purity and avoiding additives
   - Hard reject if: sodium > 250mg OR added sugar OR amino spiking suspected
   - Weights: low sodium (35%), low non-protein macros (30%), EAAs (15%), leucine (10%), protein_pct (10%)

AMINO SPIKING DETECTION:
- Suspected if 2+ of: glycine > 5% of protein, EAAs < 40%, BCAAs > 60% of EAAs, or EAAs exceed protein

KEY METRICS:
- protein_pct: protein_g / serving_size_g (higher = more protein per scoop)
- protein_per_100_kcal: efficiency metric for cutting
- eaas_pct: essential amino acids as % of protein (higher = better quality)
- leucine: key amino acid for muscle protein synthesis (need 2.7g+ per serving)
"""


def generate_explanation_from_data(brand_name: str, brand_data: dict, scores, mode: str) -> str:
    """Generate AI explanation from in-memory data (no DB required).
    
    Args:
        brand_name: Name of the brand
        brand_data: Brand extraction data dict (with nutrients, aminoacids, product_info)
        scores: BrandScores object from scorer
        mode: 'cut', 'bulk', or 'clean'
    
    Returns:
        Generated explanation string
    """
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Extract data from brand_data
    product_info = brand_data.get("product_info", {}) or {}
    nutrients = brand_data.get("nutrients", {}).get("extracted_fields", {}) or {}
    
    # Get score info
    mode_score = getattr(scores, f"{mode}_score", None)
    score_val = mode_score.total_score if mode_score else 0
    rejected = mode_score.hard_rejected if mode_score else False
    
    # Build prompt with available data
    prompt = f"""{SCORING_CONTEXT}

Now explain the {mode.upper()} score for this protein powder brand:

Brand: {brand_name}
Price per serving: ₹{product_info.get('price_per_serving', 'N/A')}
Protein per serving: {nutrients.get('protein_g_per_serving', 'N/A')}g
Energy per serving: {nutrients.get('energy_kcal_per_serving', 'N/A')} kcal
Protein %: {scores.metrics.protein_pct:.1f}% if scores.metrics.protein_pct else 'N/A'
Protein per 100 kcal: {scores.metrics.protein_per_100_kcal:.1f}g if scores.metrics.protein_per_100_kcal else 'N/A'
EAAs %: {scores.metrics.eaas_pct * 100:.1f}% if scores.metrics.eaas_pct else 'N/A'
Leucine per serving: {scores.metrics.leucine_g_per_serving or 'N/A'}g
Amino spiking suspected: {'Yes' if scores.amino_spiking.suspected else 'No'}

Score: {round(score_val * 100)}%
Rejected: {'Yes' if rejected else 'No'}

Provide a concise 2-3 sentence explanation of why this brand got this {mode} score. Focus on the key factors that influenced the score. Be specific about what's good or bad about this product for someone in {mode} mode. Use plain language."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_brand_explanations(brand_name: str, brand_data: dict, scores) -> dict:
    """Generate explanations for all modes (cut/bulk/clean).
    
    Args:
        brand_name: Name of the brand
        brand_data: Brand extraction data dict
        scores: BrandScores object from scorer
    
    Returns:
        Dict with {mode: explanation} for each mode
    """
    explanations = {}
    modes = ['cut', 'bulk', 'clean']
    
    for mode in modes:
        try:
            explanation = generate_explanation_from_data(brand_name, brand_data, scores, mode)
            explanations[mode] = explanation
            # Rate limiting - Gemini has quotas
            time.sleep(0.5)
        except Exception as e:
            explanations[mode] = f"Error generating explanation: {e}"
    
    return explanations


def get_leaderboard_data(supabase):
    """Fetch leaderboard data from Supabase."""
    result = supabase.table("leaderboard").select("*").execute()
    return result.data


def generate_explanation(brand: dict, mode: str) -> str:
    """Generate AI explanation for a brand's score in a specific mode."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    score_key = f"{mode}_score"
    rejected_key = f"{mode}_rejected"
    
    prompt = f"""{SCORING_CONTEXT}

Now explain the {mode.upper()} score for this protein powder brand:

Brand: {brand['brand']}
Price per serving: ₹{brand.get('price_per_serving', 'N/A')}
Protein per serving: {brand.get('protein_g', 'N/A')}g
Energy per serving: {brand.get('energy_kcal', 'N/A')} kcal
Protein %: {brand.get('protein_pct', 'N/A')}%
Protein per 100 kcal: {brand.get('protein_per_100_kcal', 'N/A')}g
EAAs %: {brand.get('eaas_pct', 'N/A')}%
Leucine per serving: {brand.get('leucine_g_per_serving', 'N/A')}g
Amino spiking suspected: {'Yes' if brand.get('amino_spiking_suspected') else 'No'}

Score: {round(brand.get(score_key, 0) * 100)}%
Rejected: {'Yes' if brand.get(rejected_key) else 'No'}

Provide a concise 2-3 sentence explanation of why this brand got this {mode} score. Focus on the key factors that influenced the score. Be specific about what's good or bad about this product for someone in {mode} mode. Use plain language."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_all_explanations():
    """Generate and store explanations for all brands and modes."""
    supabase = get_supabase_client()
    
    # Get all brands from leaderboard
    brands = get_leaderboard_data(supabase)
    modes = ['cut', 'bulk', 'clean']
    
    print(f"Generating explanations for {len(brands)} brands × {len(modes)} modes = {len(brands) * len(modes)} total")
    
    for brand in brands:
        brand_id = brand['id']
        brand_name = brand['brand']
        
        for mode in modes:
            # Check if explanation already exists
            existing = supabase.table("explanations").select("id").eq("brand_id", brand_id).eq("mode", mode).execute()
            
            if existing.data:
                print(f"  ⏭️  {brand_name} ({mode}): already exists")
                continue
            
            try:
                print(f"  🤖 {brand_name} ({mode}): generating...", end=" ", flush=True)
                explanation = generate_explanation(brand, mode)
                
                # Store in database
                supabase.table("explanations").insert({
                    "brand_id": brand_id,
                    "mode": mode,
                    "explanation": explanation
                }).execute()
                
                print("✅")
                
                # Rate limiting - Gemini has quotas
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    print("\n✅ Done generating explanations!")


if __name__ == "__main__":
    generate_all_explanations()
