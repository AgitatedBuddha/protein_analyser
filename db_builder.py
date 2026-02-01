"""
Database Builder for Protein Analyser - Supabase Edition

Converts JSON output files to Supabase PostgreSQL database.
Creates normalized tables: brands, nutrients, aminoacids, scores
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

from scorer import Scorer


# Load environment variables
load_dotenv()

OUTPUT_DIR = Path("output")

# Supabase client setup
def get_supabase_client() -> Client:
    """Create and return Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")  # Use secret key for write access
    
    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SECRET_KEY environment variables.\n"
            "Copy .env.example to .env and fill in your Supabase credentials."
        )
    
    return create_client(url, key)


def load_brand_json(brand_name: str) -> Optional[dict]:
    """Load brand JSON file."""
    json_path = OUTPUT_DIR / brand_name / f"{brand_name}.json"
    if not json_path.exists():
        return None
    with open(json_path) as f:
        return json.load(f)


def insert_brand(supabase: Client, data: dict) -> int:
    """Insert brand data and return brand_id."""
    brand_name = data.get("brand")
    product_info = data.get("product_info", {}) or {}
    
    # Upsert brand (insert or update if exists)
    brand_data = {
        "name": brand_name,
        "weight_kg": product_info.get("weight_kg"),
        "price_inr": product_info.get("price_inr"),
        "price_per_kg": product_info.get("price_per_kg"),
        "servings_per_pack": product_info.get("servings_per_pack"),
        "price_per_serving": product_info.get("price_per_serving"),
        "extraction_timestamp": data.get("extraction_timestamp"),
    }
    
    # Try to get existing brand
    existing = supabase.table("brands").select("id").eq("name", brand_name).execute()
    
    if existing.data:
        # Update existing
        brand_id = existing.data[0]["id"]
        supabase.table("brands").update(brand_data).eq("id", brand_id).execute()
    else:
        # Insert new
        result = supabase.table("brands").insert(brand_data).execute()
        brand_id = result.data[0]["id"]
    
    return brand_id


def insert_nutrients(supabase: Client, brand_id: int, data: dict):
    """Insert nutrients data."""
    nutrients = data.get("nutrients", {})
    if not nutrients:
        return
    
    fields = nutrients.get("extracted_fields", {})
    quality = nutrients.get("quality", {})
    
    nutrients_data = {
        "brand_id": brand_id,
        "serving_size_g": fields.get("serving_size_g"),
        "energy_kcal": fields.get("energy_kcal_per_serving"),
        "protein_g": fields.get("protein_g_per_serving"),
        "carbohydrates_g": fields.get("carbohydrates_g_per_serving"),
        "total_fat_g": fields.get("total_fat_g_per_serving"),
        "sodium_mg": fields.get("sodium_mg_per_serving"),
        "added_sugar_g": fields.get("added_sugar_g_per_serving"),       # NEW
        "heavy_metals_tested": fields.get("heavy_metals_tested"),       # NEW
        "extraction_confidence": quality.get("extraction_confidence"),
    }
    
    # Delete existing and insert new
    supabase.table("nutrients").delete().eq("brand_id", brand_id).execute()
    supabase.table("nutrients").insert(nutrients_data).execute()


def insert_aminoacids(supabase: Client, brand_id: int, data: dict):
    """Insert amino acids data."""
    amino = data.get("aminoacids", {})
    if not amino:
        return
    
    fields = amino.get("extracted_fields", {})
    quality = amino.get("quality", {})
    
    eaas = fields.get("eaas", {})
    bcaas = eaas.get("bcaas", {})
    seaas = fields.get("seaas", {})
    neaas = fields.get("neaas", {})
    
    amino_data = {
        "brand_id": brand_id,
        "serving_basis": fields.get("serving_basis"),
        "eaas_total_g": eaas.get("total_g"),
        "bcaas_total_g": bcaas.get("total_g"),
        "leucine_g": bcaas.get("leucine_g"),
        "isoleucine_g": bcaas.get("isoleucine_g"),
        "valine_g": bcaas.get("valine_g"),
        "lysine_g": eaas.get("lysine_g"),
        "methionine_g": eaas.get("methionine_g"),
        "phenylalanine_g": eaas.get("phenylalanine_g"),
        "threonine_g": eaas.get("threonine_g"),
        "tryptophan_g": eaas.get("tryptophan_g"),
        "histidine_g": eaas.get("histidine_g"),
        "seaas_total_g": seaas.get("total_g"),
        "arginine_g": seaas.get("arginine_g"),
        "cysteine_g": seaas.get("cysteine_g"),
        "glycine_g": seaas.get("glycine_g"),
        "proline_g": seaas.get("proline_g"),
        "tyrosine_g": seaas.get("tyrosine_g"),
        "neaas_total_g": neaas.get("total_g"),
        "serine_g": neaas.get("serine_g"),
        "alanine_g": neaas.get("alanine_g"),
        "aspartic_acid_g": neaas.get("aspartic_acid_g"),
        "glutamic_acid_g": neaas.get("glutamic_acid_g"),
        "extraction_confidence": quality.get("extraction_confidence"),
    }
    
    # Delete existing and insert new
    supabase.table("aminoacids").delete().eq("brand_id", brand_id).execute()
    supabase.table("aminoacids").insert(amino_data).execute()


def insert_scores(supabase: Client, brand_id: int, scores):
    """Insert computed scores."""
    m = scores.metrics
    spiking = scores.amino_spiking
    
    scores_data = {
        "brand_id": brand_id,
        "protein_pct": m.protein_pct,
        "protein_per_100_kcal": m.protein_per_100_kcal,
        "eaas_pct": m.eaas_pct,
        "bcaas_pct_of_eaas": m.bcaas_pct_of_eaas,
        "non_protein_macros_g": m.non_protein_macros_g,
        "leucine_g_per_serving": m.leucine_g_per_serving,
        "amino_spiking_suspected": spiking.suspected,
        "spiking_rules_triggered": ",".join(spiking.triggered_rules) if spiking.triggered_rules else None,
        "cut_score": scores.cut_score.total_score if scores.cut_score else None,
        "cut_rejected": scores.cut_score.hard_rejected if scores.cut_score else False,
        "cut_rejection_reason": scores.cut_score.rejection_reason if scores.cut_score else None,
        "bulk_score": scores.bulk_score.total_score if scores.bulk_score else None,
        "bulk_rejected": scores.bulk_score.hard_rejected if scores.bulk_score else False,
        "bulk_rejection_reason": scores.bulk_score.rejection_reason if scores.bulk_score else None,
        "clean_score": scores.clean_score.total_score if scores.clean_score else None,
        "clean_rejected": scores.clean_score.hard_rejected if scores.clean_score else False,
        "clean_rejection_reason": scores.clean_score.rejection_reason if scores.clean_score else None,
    }
    
    # Delete existing and insert new
    supabase.table("scores").delete().eq("brand_id", brand_id).execute()
    supabase.table("scores").insert(scores_data).execute()


def brand_exists(supabase: Client, brand_name: str) -> Optional[int]:
    """Check if brand already exists in Supabase.
    
    Returns:
        brand_id if exists, None otherwise
    """
    existing = supabase.table("brands").select("id").eq("name", brand_name).execute()
    if existing.data:
        return existing.data[0]["id"]
    return None


def insert_explanations(supabase: Client, brand_id: int, explanations: dict):
    """Insert explanations for all modes.
    
    Args:
        supabase: Supabase client
        brand_id: ID of the brand
        explanations: Dict with {mode: explanation} for cut/bulk/clean
    """
    for mode, explanation in explanations.items():
        # Delete existing and insert new
        supabase.table("explanations").delete().eq("brand_id", brand_id).eq("mode", mode).execute()
        supabase.table("explanations").insert({
            "brand_id": brand_id,
            "mode": mode,
            "explanation": explanation
        }).execute()


def push_brand(brand_name: str, force: bool = False) -> tuple[bool, str]:
    """Push a single brand to Supabase.
    
    Args:
        brand_name: Name of the brand directory
        force: If True, overwrite existing brand
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    supabase = get_supabase_client()
    
    # Check if brand exists
    existing_id = brand_exists(supabase, brand_name)
    if existing_id and not force:
        return False, f"Brand '{brand_name}' already exists. Use --force to overwrite."
    
    # Load brand data
    data = load_brand_json(brand_name)
    if not data:
        return False, f"No JSON data found for '{brand_name}' in output directory."
    
    # Compute scores
    scorer = Scorer()
    scores = scorer.score_brand(data)
    
    # Insert brand
    brand_id = insert_brand(supabase, data)
    
    # Insert nutrients
    insert_nutrients(supabase, brand_id, data)
    
    # Insert amino acids
    insert_aminoacids(supabase, brand_id, data)
    
    # Insert scores
    insert_scores(supabase, brand_id, scores)
    
    # Insert explanations if present in data
    explanations = data.get("explanations")
    if explanations:
        insert_explanations(supabase, brand_id, explanations)
    
    return True, f"Successfully pushed '{brand_name}' to Supabase."


def build_database(output_dir: Path = OUTPUT_DIR):
    """Build Supabase database from JSON output files."""
    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    
    # Verify connection by checking if brands table exists
    try:
        supabase.table("brands").select("id").limit(1).execute()
        print("✓ Connected to Supabase\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print("\nMake sure you have:")
        print("  1. Run supabase/schema.sql in your Supabase SQL Editor")
        print("  2. Set SUPABASE_URL and SUPABASE_SECRET_KEY in .env")
        return
    
    # Score all brands
    scorer = Scorer()
    
    # Process each brand
    brands_processed = 0
    for brand_dir in output_dir.iterdir():
        if not brand_dir.is_dir() or brand_dir.name.startswith("."):
            continue
        
        brand_name = brand_dir.name
        data = load_brand_json(brand_name)
        if not data:
            continue
        
        # Insert brand
        brand_id = insert_brand(supabase, data)
        
        # Insert nutrients
        insert_nutrients(supabase, brand_id, data)
        
        # Insert amino acids
        insert_aminoacids(supabase, brand_id, data)
        
        # Compute and insert scores
        scores = scorer.score_brand(data)
        insert_scores(supabase, brand_id, scores)
        
        brands_processed += 1
        print(f"  ✓ {brand_name}")
    
    print(f"\n✓ Database updated in Supabase")
    print(f"  Brands: {brands_processed}")


def verify_database():
    """Verify the Supabase database has data."""
    print("Verifying Supabase database...\n")
    supabase = get_supabase_client()
    
    # Check counts
    brands = supabase.table("brands").select("id", count="exact").execute()
    nutrients = supabase.table("nutrients").select("id", count="exact").execute()
    aminoacids = supabase.table("aminoacids").select("id", count="exact").execute()
    scores = supabase.table("scores").select("id", count="exact").execute()
    
    print(f"  Brands: {brands.count}")
    print(f"  Nutrients: {nutrients.count}")
    print(f"  Amino acids: {aminoacids.count}")
    print(f"  Scores: {scores.count}")
    
    # Show leaderboard preview
    print("\nLeaderboard (top 5 by cut score):")
    leaderboard = supabase.table("leaderboard").select("*").limit(5).execute()
    for row in leaderboard.data:
        name = row.get("brand", "Unknown")
        cut_score = row.get("cut_score")
        cut_score_str = f"{cut_score:.2f}" if cut_score else "N/A"
        print(f"  {name}: {cut_score_str}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_database()
    else:
        print("Building database from JSON output...\n")
        build_database()
