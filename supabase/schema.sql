-- ============================================
-- Protein Analyser - Supabase PostgreSQL Schema
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================

-- ============================================
-- BRANDS TABLE
-- ============================================
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    weight_kg REAL,
    price_inr REAL,
    price_per_kg REAL,
    servings_per_pack REAL,
    price_per_serving REAL,
    extraction_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- NUTRIENTS TABLE
-- ============================================
CREATE TABLE nutrients (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    serving_size_g REAL,
    energy_kcal REAL,
    protein_g REAL,
    carbohydrates_g REAL,
    total_fat_g REAL,
    sodium_mg REAL,
    extraction_confidence REAL
);

-- ============================================
-- AMINO ACIDS TABLE
-- ============================================
CREATE TABLE aminoacids (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
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
    extraction_confidence REAL
);

-- ============================================
-- SCORES TABLE
-- ============================================
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
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
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- LEADERBOARD VIEW
-- ============================================
CREATE OR REPLACE VIEW leaderboard AS
SELECT 
    b.id,
    b.name AS brand,
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
ORDER BY s.cut_score DESC NULLS LAST;

-- ============================================
-- PUBLIC ACCESS (no auth required)
-- ============================================
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrients ENABLE ROW LEVEL SECURITY;
ALTER TABLE aminoacids ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Public read access" ON brands FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nutrients FOR SELECT USING (true);
CREATE POLICY "Public read access" ON aminoacids FOR SELECT USING (true);
CREATE POLICY "Public read access" ON scores FOR SELECT USING (true);

-- Allow authenticated write access (for the Python script using secret key)
CREATE POLICY "Service write access" ON brands FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write access" ON nutrients FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write access" ON aminoacids FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write access" ON scores FOR ALL USING (true) WITH CHECK (true);
