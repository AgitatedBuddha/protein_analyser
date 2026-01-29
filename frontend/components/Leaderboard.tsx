'use client';

import { useState } from 'react';
import type { LeaderboardRow } from '@/lib/supabase';

type ScoreMode = 'cut' | 'bulk' | 'clean';

interface LeaderboardProps {
  data: LeaderboardRow[];
  mode: ScoreMode;
  onSelectBrand: (brand: LeaderboardRow) => void;
}

export default function Leaderboard({ data, mode, onSelectBrand }: LeaderboardProps) {
  const [sortBy, setSortBy] = useState<string>(`${mode}_score`);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const scoreKey = `${mode}_score` as keyof LeaderboardRow;
  const rejectedKey = `${mode}_rejected` as keyof LeaderboardRow;

  // Sort data
  const sortedData = [...data].sort((a, b) => {
    const aVal = a[sortBy as keyof LeaderboardRow];
    const bVal = b[sortBy as keyof LeaderboardRow];
    
    if (aVal === null) return 1;
    if (bVal === null) return -1;
    
    const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    return sortDir === 'desc' ? -comparison : comparison;
  });

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('desc');
    }
  };

  const formatScore = (score: number | null) => {
    if (score === null) return '-';
    return (score * 100).toFixed(0) + '%';
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '-';
    return '₹' + price.toFixed(0);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-gray-400 uppercase bg-gray-800">
          <tr>
            <th className="px-4 py-3">#</th>
            <th 
              className="px-4 py-3 cursor-pointer hover:text-white"
              onClick={() => handleSort('brand')}
            >
              Brand {sortBy === 'brand' && (sortDir === 'asc' ? '↑' : '↓')}
            </th>
            <th 
              className="px-4 py-3 cursor-pointer hover:text-white"
              onClick={() => handleSort('price_per_serving')}
            >
              ₹/Serving {sortBy === 'price_per_serving' && (sortDir === 'asc' ? '↑' : '↓')}
            </th>
            <th 
              className="px-4 py-3 cursor-pointer hover:text-white"
              onClick={() => handleSort('protein_g')}
            >
              Protein {sortBy === 'protein_g' && (sortDir === 'asc' ? '↑' : '↓')}
            </th>
            <th 
              className="px-4 py-3 cursor-pointer hover:text-white"
              onClick={() => handleSort(scoreKey as string)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)} Score {sortBy === scoreKey && (sortDir === 'asc' ? '↑' : '↓')}
            </th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => {
            const isRejected = row[rejectedKey] as boolean;
            const score = row[scoreKey] as number | null;
            
            return (
              <tr
                key={row.id}
                onClick={() => onSelectBrand(row)}
                className={`border-b border-gray-700 cursor-pointer transition-colors ${
                  isRejected 
                    ? 'bg-gray-800/50 text-gray-500' 
                    : 'hover:bg-gray-800'
                }`}
              >
                <td className="px-4 py-3 font-medium">{index + 1}</td>
                <td className="px-4 py-3 font-medium text-white">{row.brand}</td>
                <td className="px-4 py-3">{formatPrice(row.price_per_serving)}</td>
                <td className="px-4 py-3">{row.protein_g ? `${row.protein_g}g` : '-'}</td>
                <td className="px-4 py-3">
                  <span className={`font-bold ${
                    !isRejected && score !== null
                      ? score >= 0.7 ? 'text-green-400' 
                      : score >= 0.5 ? 'text-yellow-400'
                      : 'text-red-400'
                      : 'text-gray-500'
                  }`}>
                    {formatScore(score)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {isRejected ? (
                    <span className="px-2 py-1 text-xs bg-red-900/50 text-red-400 rounded">
                      Rejected
                    </span>
                  ) : row.amino_spiking_suspected ? (
                    <span className="px-2 py-1 text-xs bg-yellow-900/50 text-yellow-400 rounded">
                      ⚠️ Spiking
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs bg-green-900/50 text-green-400 rounded">
                      ✓ Pass
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
