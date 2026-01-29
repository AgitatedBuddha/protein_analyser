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

interface NutrientsChartProps {
  data: NutrientData[];
}

export default function NutrientsChart({ data }: NutrientsChartProps) {
  const chartData = data
    .filter((d) => d.protein_g !== null)
    .map((d) => ({
      name: d.brand,
      Protein: d.protein_g || 0,
      Carbs: d.carbohydrates_g || 0,
      Fat: d.total_fat_g || 0,
    }))
    .sort((a, b) => b.Protein - a.Protein);

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
            formatter={(value) => [`${value ?? ''}g`, '']}
          />
          <Legend />
          <Bar dataKey="Protein" fill="#22c55e" radius={[0, 2, 2, 0]} stackId="stack" />
          <Bar dataKey="Carbs" fill="#3b82f6" radius={[0, 2, 2, 0]} stackId="stack" />
          <Bar dataKey="Fat" fill="#f97316" radius={[0, 2, 2, 0]} stackId="stack" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
