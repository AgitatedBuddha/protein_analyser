'use client';

import { useState } from 'react';
import type { LeaderboardRow } from '@/lib/supabase';
import ModeToggle from '@/components/ModeToggle';
import Leaderboard from '@/components/Leaderboard';
import ScoreChart from '@/components/ScoreChart';
import ExplainButton from '@/components/ExplainButton';

type ScoreMode = 'cut' | 'bulk' | 'clean';

interface ClientPageProps {
  initialData: LeaderboardRow[];
}

export default function ClientPage({ initialData }: ClientPageProps) {
  const [mode, setMode] = useState<ScoreMode>('cut');
  const [selectedBrand, setSelectedBrand] = useState<LeaderboardRow | null>(null);

  const handleSelectBrand = (brand: LeaderboardRow) => {
    setSelectedBrand(brand);
  };

  const scoreKey = `${mode}_score` as keyof LeaderboardRow;
  const rejectedKey = `${mode}_rejected` as keyof LeaderboardRow;

  return (
    <>
      {/* Mode Toggle */}
      <div className="mb-6 flex items-center justify-between">
        <ModeToggle mode={mode} onChange={setMode} />
        <div className="text-sm text-gray-500">
          Click any brand to see details
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart Section */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">
            {mode.charAt(0).toUpperCase() + mode.slice(1)} Score Comparison
          </h2>
          <ScoreChart data={initialData} mode={mode} onSelectBrand={handleSelectBrand} />
        </div>

        {/* Brand Detail Panel */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Brand Details</h2>
          
          {selectedBrand ? (
            <div>
              <h3 className="text-xl font-bold text-white mb-3">
                {selectedBrand.brand}
              </h3>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Price/Serving</span>
                  <span className="text-white">
                    ₹{selectedBrand.price_per_serving?.toFixed(0) || '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Protein</span>
                  <span className="text-white">
                    {selectedBrand.protein_g || '-'}g
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Protein %</span>
                  <span className="text-white">
                    {selectedBrand.protein_pct 
                      ? selectedBrand.protein_pct.toFixed(1) + '%' 
                      : '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">EAAs %</span>
                  <span className="text-white">
                    {selectedBrand.eaas_pct 
                      ? selectedBrand.eaas_pct.toFixed(1) + '%' 
                      : '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Leucine</span>
                  <span className="text-white">
                    {selectedBrand.leucine_g_per_serving?.toFixed(2) || '-'}g
                  </span>
                </div>
                
                <hr className="border-gray-700 my-3" />
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">
                    {mode.charAt(0).toUpperCase() + mode.slice(1)} Score
                  </span>
                  <span className={`text-xl font-bold ${
                    selectedBrand[rejectedKey]
                      ? 'text-gray-500'
                      : (selectedBrand[scoreKey] as number) >= 0.7
                      ? 'text-green-400'
                      : (selectedBrand[scoreKey] as number) >= 0.5
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  }`}>
                    {selectedBrand[scoreKey] 
                      ? ((selectedBrand[scoreKey] as number) * 100).toFixed(0) + '%'
                      : '-'}
                  </span>
                </div>

                {selectedBrand.amino_spiking_suspected && (
                  <div className="mt-2 p-2 bg-yellow-900/30 border border-yellow-700 rounded text-yellow-400 text-xs">
                    ⚠️ Amino spiking suspected
                  </div>
                )}
              </div>

              {/* LLM Explain Button */}
              <ExplainButton brand={selectedBrand} mode={mode} />
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Select a brand from the chart or table below
            </div>
          )}
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="mt-6 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Full Leaderboard</h2>
        </div>
        <Leaderboard 
          data={initialData} 
          mode={mode} 
          onSelectBrand={handleSelectBrand} 
        />
      </div>
    </>
  );
}
