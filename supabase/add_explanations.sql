-- Add explanations table for pre-generated AI summaries
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    mode VARCHAR(10) NOT NULL CHECK (mode IN ('cut', 'bulk', 'clean')),
    explanation TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(brand_id, mode)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_explanations_brand_mode ON explanations(brand_id, mode);

-- Enable RLS
ALTER TABLE explanations ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read access for explanations"
    ON explanations FOR SELECT
    USING (true);
