import { supabase } from '@/lib/supabase';
import Navigation from '@/components/Navigation';
import NutrientsChart from './NutrientsChart';

export const revalidate = 60;

interface NutrientData {
  id: number;
  brand: string;
  serving_size_g: number | null;
  energy_kcal: number | null;
  protein_g: number | null;
  carbohydrates_g: number | null;
  total_fat_g: number | null;
  sodium_mg: number | null;
}

async function getNutrients(): Promise<NutrientData[]> {
  const { data, error } = await supabase
    .from('brands')
    .select(`
      id,
      name,
      nutrients (
        serving_size_g,
        energy_kcal,
        protein_g,
        carbohydrates_g,
        total_fat_g,
        sodium_mg
      )
    `)
    .order('name');

  if (error) {
    console.error('Error fetching nutrients:', error);
    return [];
  }

  // Flatten the data
  return (data || []).map((item: any) => ({
    id: item.id,
    brand: item.name,
    serving_size_g: item.nutrients?.[0]?.serving_size_g ?? null,
    energy_kcal: item.nutrients?.[0]?.energy_kcal ?? null,
    protein_g: item.nutrients?.[0]?.protein_g ?? null,
    carbohydrates_g: item.nutrients?.[0]?.carbohydrates_g ?? null,
    total_fat_g: item.nutrients?.[0]?.total_fat_g ?? null,
    sodium_mg: item.nutrients?.[0]?.sodium_mg ?? null,
  }));
}

export default async function NutrientsPage() {
  const nutrients = await getNutrients();

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            🥤 Protein Powder Analyser
          </h1>
          <p className="text-gray-400">
            Nutrient breakdown comparison
          </p>
        </header>

        <Navigation />

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">
            🥗 Nutrient Breakdown per Serving
          </h2>
          <p className="text-gray-400 text-sm mb-6">
            Compare protein, carbs, fat, and calories across all brands
          </p>
          <NutrientsChart data={nutrients} />
        </div>
      </div>
    </main>
  );
}
