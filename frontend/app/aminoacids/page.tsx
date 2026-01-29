import { supabase } from '@/lib/supabase';
import Navigation from '@/components/Navigation';
import AminoAcidsChart from './AminoAcidsChart';

export const revalidate = 60;

interface AminoAcidData {
  id: number;
  brand: string;
  eaas_total_g: number | null;
  bcaas_total_g: number | null;
  leucine_g: number | null;
  isoleucine_g: number | null;
  valine_g: number | null;
  lysine_g: number | null;
  seaas_total_g: number | null;
  neaas_total_g: number | null;
}

async function getAminoAcids(): Promise<AminoAcidData[]> {
  const { data, error } = await supabase
    .from('brands')
    .select(`
      id,
      name,
      aminoacids (
        eaas_total_g,
        bcaas_total_g,
        leucine_g,
        isoleucine_g,
        valine_g,
        lysine_g,
        seaas_total_g,
        neaas_total_g
      )
    `)
    .order('name');

  if (error) {
    console.error('Error fetching amino acids:', error);
    return [];
  }

  // Flatten the data
  return (data || []).map((item: any) => ({
    id: item.id,
    brand: item.name,
    eaas_total_g: item.aminoacids?.[0]?.eaas_total_g ?? null,
    bcaas_total_g: item.aminoacids?.[0]?.bcaas_total_g ?? null,
    leucine_g: item.aminoacids?.[0]?.leucine_g ?? null,
    isoleucine_g: item.aminoacids?.[0]?.isoleucine_g ?? null,
    valine_g: item.aminoacids?.[0]?.valine_g ?? null,
    lysine_g: item.aminoacids?.[0]?.lysine_g ?? null,
    seaas_total_g: item.aminoacids?.[0]?.seaas_total_g ?? null,
    neaas_total_g: item.aminoacids?.[0]?.neaas_total_g ?? null,
  }));
}

export default async function AminoAcidsPage() {
  const aminoAcids = await getAminoAcids();

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            🥤 Protein Powder Analyser
          </h1>
          <p className="text-gray-400">
            Amino acid profile comparison
          </p>
        </header>

        <Navigation />

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">
            🧬 Amino Acid Profile per Serving
          </h2>
          <p className="text-gray-400 text-sm mb-6">
            Compare EAAs, BCAAs (leucine, isoleucine, valine), and other amino acids
          </p>
          <AminoAcidsChart data={aminoAcids} />
        </div>
      </div>
    </main>
  );
}
