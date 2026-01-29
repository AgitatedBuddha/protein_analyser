import { supabase, type LeaderboardRow } from '@/lib/supabase';
import Navigation from '@/components/Navigation';
import ClientPage from './ClientPage';

export const revalidate = 60; // Revalidate every 60 seconds

async function getLeaderboard(): Promise<LeaderboardRow[]> {
  const { data, error } = await supabase
    .from('leaderboard')
    .select('*')
    .order('cut_score', { ascending: false, nullsFirst: false });

  if (error) {
    console.error('Error fetching leaderboard:', error);
    return [];
  }

  return data || [];
}

export default async function Home() {
  const leaderboard = await getLeaderboard();

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            🥤 Protein Powder Analyser
          </h1>
          <p className="text-gray-400">
            Compare {leaderboard.length} protein powders across different fitness goals
          </p>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Client-side interactive content */}
        <ClientPage initialData={leaderboard} />
      </div>
    </main>
  );
}
