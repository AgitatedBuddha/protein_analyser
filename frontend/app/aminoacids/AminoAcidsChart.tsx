'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

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

interface AminoAcidsChartProps {
  data: AminoAcidData[];
}

export default function AminoAcidsChart({ data }: AminoAcidsChartProps) {
  const chartData = data
    .filter((d) => d.eaas_total_g !== null || d.bcaas_total_g !== null)
    .map((d) => ({
      name: d.brand,
      Leucine: d.leucine_g || 0,
      Isoleucine: d.isoleucine_g || 0,
      Valine: d.valine_g || 0,
      'Other EAAs': (d.eaas_total_g || 0) - (d.bcaas_total_g || 0),
    }))
    .sort((a, b) => b.Leucine - a.Leucine);

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            tick={{ fill: '#9ca3af' }}
            tickFormatter={(value) => `${value}g`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            width={95}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f9fafb' }}
            formatter={(value) => [`${(typeof value === 'number' ? value.toFixed(2) : value ?? '')}g`, '']}
          />
          <Legend />
          <Bar dataKey="Leucine" fill="#22c55e" radius={[0, 2, 2, 0]} stackId="stack" />
          <Bar dataKey="Isoleucine" fill="#3b82f6" radius={[0, 2, 2, 0]} stackId="stack" />
          <Bar dataKey="Valine" fill="#8b5cf6" radius={[0, 2, 2, 0]} stackId="stack" />
          <Bar dataKey="Other EAAs" fill="#f97316" radius={[0, 2, 2, 0]} stackId="stack" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
