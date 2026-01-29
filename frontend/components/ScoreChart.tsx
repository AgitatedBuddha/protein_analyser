'use client';

import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { LeaderboardRow } from '@/lib/supabase';

type ScoreMode = 'cut' | 'bulk' | 'clean';

interface ScoreChartProps {
  data: LeaderboardRow[];
  mode: ScoreMode;
  onSelectBrand?: (brand: LeaderboardRow) => void;
}

const modeColors = {
  cut: '#f97316',    // orange
  bulk: '#3b82f6',   // blue
  clean: '#22c55e',  // green
};

export default function ScoreChart({ data, mode, onSelectBrand }: ScoreChartProps) {
  const scoreKey = `${mode}_score` as keyof LeaderboardRow;
  const rejectedKey = `${mode}_rejected` as keyof LeaderboardRow;

  // Prepare chart data
  const chartData = data
    .filter((row) => row[scoreKey] !== null)
    .map((row) => ({
      name: row.brand,
      score: ((row[scoreKey] as number) * 100).toFixed(1),
      rejected: row[rejectedKey] as boolean,
      fullData: row,
    }))
    .sort((a, b) => parseFloat(b.score) - parseFloat(a.score));

  const handleBarClick = (data: any) => {
    if (onSelectBrand && data?.fullData) {
      onSelectBrand(data.fullData);
    }
  };

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: '#9ca3af' }}
            tickFormatter={(value) => `${value}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            width={95}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f9fafb' }}
            formatter={(value) => [`${value ?? ''}%`, 'Score']}
          />
          <Bar 
            dataKey="score" 
            radius={[0, 4, 4, 0]}
            onClick={handleBarClick}
            style={{ cursor: onSelectBrand ? 'pointer' : 'default' }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.rejected ? '#6b7280' : modeColors[mode]}
                opacity={entry.rejected ? 0.5 : 1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

