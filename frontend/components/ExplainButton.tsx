'use client';

import { useState, useEffect } from 'react';
import type { LeaderboardRow, Explanation } from '@/lib/supabase';
import { supabase } from '@/lib/supabase';

type ScoreMode = 'cut' | 'bulk' | 'clean';

interface ExplainButtonProps {
  brand: LeaderboardRow;
  mode: ScoreMode;
}

export default function ExplainButton({ brand, mode }: ExplainButtonProps) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset explanation when brand or mode changes
  useEffect(() => {
    setExplanation(null);
    setError(null);
  }, [brand.id, mode]);

  const handleExplain = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch pre-generated explanation from Supabase
      const { data, error: dbError } = await supabase
        .from('explanations')
        .select('explanation')
        .eq('brand_id', brand.id)
        .eq('mode', mode)
        .single();

      if (dbError || !data) {
        setError('No explanation available. Run `analyse full` with --push to generate.');
        return;
      }

      setExplanation(data.explanation);
    } catch (err) {
      setError('Failed to fetch explanation. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const scoreKey = `${mode}_score` as keyof LeaderboardRow;
  const score = brand[scoreKey] as number | null;

  return (
    <div className="mt-4">
      <button
        onClick={handleExplain}
        disabled={loading}
        className={`px-4 py-2 rounded-lg font-medium transition-all ${
          loading
            ? 'bg-gray-700 text-gray-400 cursor-wait'
            : 'bg-purple-600 hover:bg-purple-700 text-white'
        }`}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Loading...
          </span>
        ) : (
          '✨ Explain This Score'
        )}
      </button>

      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {explanation && (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2 mb-2 text-purple-400">
            <span>✨</span>
            <span className="font-medium">AI Explanation</span>
          </div>
          <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
            {explanation}
          </p>
        </div>
      )}
    </div>
  );
}
