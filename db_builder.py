"""
Database Builder for Protein Analyser

Converts JSON output files to SQLite database for Datasette.
Creates normalized tables: brands, nutrients, aminoacids, scores
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from scorer import Scorer, score_all_brands


OUTPUT_DIR = Path("output")
DB_PATH = Path("protein_analyser.db")


def create_tables(conn: sqlite3.Connection):
    """Create database tables."""
    conn.executescript("""
        -- Brands table (main)
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            weight_kg REAL,
            price_inr REAL,
            price_per_kg REAL,
            servings_per_pack REAL,
            price_per_serving REAL,
            extraction_timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Nutrients table
        CREATE TABLE IF NOT EXISTS nutrients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            serving_size_g REAL,
            energy_kcal REAL,
            protein_g REAL,
            carbohydrates_g REAL,
            total_fat_g REAL,
            sodium_mg REAL,
            extraction_confidence REAL,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        );
        
        -- Amino acids table
        CREATE TABLE IF NOT EXISTS aminoacids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            serving_basis TEXT,
            -- EAAs
            eaas_total_g REAL,
            bcaas_total_g REAL,
            leucine_g REAL,
            isoleucine_g REAL,
            valine_g REAL,
            lysine_g REAL,
            methionine_g REAL,
            phenylalanine_g REAL,
            threonine_g REAL,
            tryptophan_g REAL,
            histidine_g REAL,
            -- SEAAs
            seaas_total_g REAL,
            arginine_g REAL,
            cysteine_g REAL,
            glycine_g REAL,
            proline_g REAL,
            tyrosine_g REAL,
            -- NEAAs
            neaas_total_g REAL,
            serine_g REAL,
            alanine_g REAL,
            aspartic_acid_g REAL,
            glutamic_acid_g REAL,
            extraction_confidence REAL,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        );
        
        -- Scores table
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            -- Computed metrics
            protein_pct REAL,
            protein_per_100_kcal REAL,
            eaas_pct REAL,
            bcaas_pct_of_eaas REAL,
            non_protein_macros_g REAL,
            leucine_g_per_serving REAL,
            -- Amino spiking
            amino_spiking_suspected BOOLEAN,
            spiking_rules_triggered TEXT,
            -- Mode scores
            cut_score REAL,
            cut_rejected BOOLEAN,
            cut_rejection_reason TEXT,
            bulk_score REAL,
            bulk_rejected BOOLEAN,
            bulk_rejection_reason TEXT,
            clean_score REAL,
            clean_rejected BOOLEAN,
            clean_rejection_reason TEXT,
            computed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id)
        );
        
        -- Leaderboard view for easy querying
        CREATE VIEW IF NOT EXISTS leaderboard AS
        SELECT 
            b.name as brand,
            b.price_per_serving,
            b.price_per_kg,
            n.protein_g,
            n.energy_kcal,
            s.protein_pct,
            s.protein_per_100_kcal,
            s.eaas_pct,
            s.leucine_g_per_serving,
            s.amino_spiking_suspected,
            s.cut_score,
            s.cut_rejected,
            s.bulk_score,
            s.bulk_rejected,
            s.clean_score,
            s.clean_rejected
        FROM brands b
        LEFT JOIN nutrients n ON b.id = n.brand_id
        LEFT JOIN scores s ON b.id = s.brand_id
        ORDER BY s.cut_score DESC;
    """)
    conn.commit()


def load_brand_json(brand_name: str) -> Optional[dict]:
    """Load brand JSON file."""
    json_path = OUTPUT_DIR / brand_name / f"{brand_name}.json"
    if not json_path.exists():
        return None
    with open(json_path) as f:
        return json.load(f)


def insert_brand(conn: sqlite3.Connection, data: dict) -> int:
    """Insert brand data and return brand_id."""
    brand_name = data.get("brand")
    product_info = data.get("product_info", {}) or {}
    
    cursor = conn.execute("""
        INSERT OR REPLACE INTO brands (name, weight_kg, price_inr, price_per_kg, 
                                        servings_per_pack, price_per_serving, extraction_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_name,
        product_info.get("weight_kg"),
        product_info.get("price_inr"),
        product_info.get("price_per_kg"),
        product_info.get("servings_per_pack"),
        product_info.get("price_per_serving"),
        data.get("extraction_timestamp"),
    ))
    
    # Get the brand_id
    cursor = conn.execute("SELECT id FROM brands WHERE name = ?", (brand_name,))
    return cursor.fetchone()[0]


def insert_nutrients(conn: sqlite3.Connection, brand_id: int, data: dict):
    """Insert nutrients data."""
    nutrients = data.get("nutrients", {})
    if not nutrients:
        return
    
    fields = nutrients.get("extracted_fields", {})
    quality = nutrients.get("quality", {})
    
    conn.execute("""
        INSERT OR REPLACE INTO nutrients (brand_id, serving_size_g, energy_kcal, protein_g,
                                          carbohydrates_g, total_fat_g, sodium_mg, extraction_confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_id,
        fields.get("serving_size_g"),
        fields.get("energy_kcal_per_serving"),
        fields.get("protein_g_per_serving"),
        fields.get("carbohydrates_g_per_serving"),
        fields.get("total_fat_g_per_serving"),
        fields.get("sodium_mg_per_serving"),
        quality.get("extraction_confidence"),
    ))


def insert_aminoacids(conn: sqlite3.Connection, brand_id: int, data: dict):
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
    
    conn.execute("""
        INSERT OR REPLACE INTO aminoacids (
            brand_id, serving_basis,
            eaas_total_g, bcaas_total_g, leucine_g, isoleucine_g, valine_g,
            lysine_g, methionine_g, phenylalanine_g, threonine_g, tryptophan_g, histidine_g,
            seaas_total_g, arginine_g, cysteine_g, glycine_g, proline_g, tyrosine_g,
            neaas_total_g, serine_g, alanine_g, aspartic_acid_g, glutamic_acid_g,
            extraction_confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_id,
        fields.get("serving_basis"),
        eaas.get("total_g"),
        bcaas.get("total_g"),
        bcaas.get("leucine_g"),
        bcaas.get("isoleucine_g"),
        bcaas.get("valine_g"),
        eaas.get("lysine_g"),
        eaas.get("methionine_g"),
        eaas.get("phenylalanine_g"),
        eaas.get("threonine_g"),
        eaas.get("tryptophan_g"),
        eaas.get("histidine_g"),
        seaas.get("total_g"),
        seaas.get("arginine_g"),
        seaas.get("cysteine_g"),
        seaas.get("glycine_g"),
        seaas.get("proline_g"),
        seaas.get("tyrosine_g"),
        neaas.get("total_g"),
        neaas.get("serine_g"),
        neaas.get("alanine_g"),
        neaas.get("aspartic_acid_g"),
        neaas.get("glutamic_acid_g"),
        quality.get("extraction_confidence"),
    ))


def insert_scores(conn: sqlite3.Connection, brand_id: int, scores):
    """Insert computed scores."""
    m = scores.metrics
    spiking = scores.amino_spiking
    
    conn.execute("""
        INSERT OR REPLACE INTO scores (
            brand_id,
            protein_pct, protein_per_100_kcal, eaas_pct, bcaas_pct_of_eaas,
            non_protein_macros_g, leucine_g_per_serving,
            amino_spiking_suspected, spiking_rules_triggered,
            cut_score, cut_rejected, cut_rejection_reason,
            bulk_score, bulk_rejected, bulk_rejection_reason,
            clean_score, clean_rejected, clean_rejection_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        brand_id,
        m.protein_pct,
        m.protein_per_100_kcal,
        m.eaas_pct,
        m.bcaas_pct_of_eaas,
        m.non_protein_macros_g,
        m.leucine_g_per_serving,
        spiking.suspected,
        ",".join(spiking.triggered_rules) if spiking.triggered_rules else None,
        scores.cut_score.total_score if scores.cut_score else None,
        scores.cut_score.hard_rejected if scores.cut_score else False,
        scores.cut_score.rejection_reason if scores.cut_score else None,
        scores.bulk_score.total_score if scores.bulk_score else None,
        scores.bulk_score.hard_rejected if scores.bulk_score else False,
        scores.bulk_score.rejection_reason if scores.bulk_score else None,
        scores.clean_score.total_score if scores.clean_score else None,
        scores.clean_score.hard_rejected if scores.clean_score else False,
        scores.clean_score.rejection_reason if scores.clean_score else None,
    ))


def build_database(db_path: Path = DB_PATH, output_dir: Path = OUTPUT_DIR):
    """Build SQLite database from JSON output files."""
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(db_path)
    
    # Create tables
    create_tables(conn)
    
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
        brand_id = insert_brand(conn, data)
        
        # Insert nutrients
        insert_nutrients(conn, brand_id, data)
        
        # Insert amino acids
        insert_aminoacids(conn, brand_id, data)
        
        # Compute and insert scores
        scores = scorer.score_brand(data)
        insert_scores(conn, brand_id, scores)
        
        brands_processed += 1
        print(f"  ✓ {brand_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Database created: {db_path}")
    print(f"  Brands: {brands_processed}")
    return db_path


if __name__ == "__main__":
    print("Building database from JSON output...\n")
    build_database()
