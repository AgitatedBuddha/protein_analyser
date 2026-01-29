import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

export const supabase = createClient(supabaseUrl, supabasePublishableKey);

// Types matching our database schema
export interface Brand {
  id: number;
  name: string;
  weight_kg: number | null;
  price_inr: number | null;
  price_per_kg: number | null;
  servings_per_pack: number | null;
  price_per_serving: number | null;
  extraction_timestamp: string | null;
}

export interface Nutrient {
  id: number;
  brand_id: number;
  serving_size_g: number | null;
  energy_kcal: number | null;
  protein_g: number | null;
  carbohydrates_g: number | null;
  total_fat_g: number | null;
  sodium_mg: number | null;
  extraction_confidence: number | null;
}

export interface Score {
  id: number;
  brand_id: number;
  protein_pct: number | null;
  protein_per_100_kcal: number | null;
  eaas_pct: number | null;
  bcaas_pct_of_eaas: number | null;
  non_protein_macros_g: number | null;
  leucine_g_per_serving: number | null;
  amino_spiking_suspected: boolean | null;
  spiking_rules_triggered: string | null;
  cut_score: number | null;
  cut_rejected: boolean | null;
  cut_rejection_reason: string | null;
  bulk_score: number | null;
  bulk_rejected: boolean | null;
  bulk_rejection_reason: string | null;
  clean_score: number | null;
  clean_rejected: boolean | null;
  clean_rejection_reason: string | null;
}

export interface LeaderboardRow {
  id: number;
  brand: string;
  price_per_serving: number | null;
  price_per_kg: number | null;
  protein_g: number | null;
  energy_kcal: number | null;
  protein_pct: number | null;
  protein_per_100_kcal: number | null;
  eaas_pct: number | null;
  leucine_g_per_serving: number | null;
  amino_spiking_suspected: boolean | null;
  cut_score: number | null;
  cut_rejected: boolean | null;
  bulk_score: number | null;
  bulk_rejected: boolean | null;
  clean_score: number | null;
  clean_rejected: boolean | null;
}

export interface Explanation {
  id: number;
  brand_id: number;
  mode: 'cut' | 'bulk' | 'clean';
  explanation: string;
  generated_at: string;
}
