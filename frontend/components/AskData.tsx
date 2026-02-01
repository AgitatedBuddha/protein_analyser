'use client';

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import ReactMarkdown from 'react-markdown';

// Initialize Supabase client
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
);

type Filter = {
  field: string;
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  value: number;
};

type QueryResponse = {
  type?: 'filter' | 'comparison';
  markdown_explanation?: string;
  force_ids?: number[];
  filters: Filter[];
  sort_by: string | null;
  sort_order: 'asc' | 'desc' | null;
  limit: number;
};

const SUGGESTED_QUERIES = [
  "High protein (>75%) brands under ₹70",
  "Why is MuscleBlaze better than Oziva?",
  "Best for muscle building (High Leucine)",
  "Compare Origin and Truth",
  "Cheapest options for cutting",
  "Any brands with amino spiking?",
];

export default function AskData() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [filteredData, setFilteredData] = useState<any[]>([]);
  const [activeQuery, setActiveQuery] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load all data on mount
  useEffect(() => {
    const fetchData = async () => {
      const { data: brands, error } = await supabase
        .from('leaderboard')
        .select('*');
      
      if (error) {
        console.error('Error loading data:', error);
        setError('Failed to load protein data');
      } else {
        setData(brands || []);
        // Default view: Top 5 by cut score
        setFilteredData((brands || []).sort((a, b) => b.cut_score - a.cut_score).slice(0, 5));
      }
    };
    fetchData();
  }, []);

  const handleSearch = async (queryText: string = input) => {
    if (!queryText.trim()) return;
    
    setLoading(true);
    setError(null);
    setInput(queryText);
    setActiveQuery(null); // Clear previous

    try {
      // 1. Get filter/analysis instructions from LLM
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: queryText }),
      });

      if (!response.ok) throw new Error('Failed to interpret query');
      
      const queryInit: QueryResponse = await response.json();
      setActiveQuery(queryInit);

      // 2. Apply logic locally
      let result = [...data];

      if (queryInit.force_ids && queryInit.force_ids.length > 0) {
        // Comparison Mode: Show only specific brands
        result = result.filter(item => queryInit.force_ids!.includes(item.id));
      } else {
        // Filter Mode: Apply standard filters
        if (queryInit.filters) {
          queryInit.filters.forEach(filter => {
            result = result.filter(item => {
              const val = item[filter.field];
              if (val === null || val === undefined) return false;
              
              switch (filter.operator) {
                case 'gt': return val > filter.value;
                case 'gte': return val >= filter.value;
                case 'lt': return val < filter.value;
                case 'lte': return val <= filter.value;
                case 'eq': return val == filter.value;
                default: return true;
              }
            });
          });
        }

        // Sorting
        if (queryInit.sort_by) {
          result.sort((a, b) => {
            const valA = a[queryInit.sort_by!] ?? 0;
            const valB = b[queryInit.sort_by!] ?? 0;
            return queryInit.sort_order === 'asc' ? valA - valB : valB - valA;
          });
        }

        // Limiting
        if (queryInit.limit && queryInit.limit > 0) {
          result = result.slice(0, queryInit.limit);
        }
      }

      setFilteredData(result);

    } catch (err) {
      console.error(err);
      setError('Sorry, I couldn\'t understand that query. Try simpler terms.');
    } finally {
      setLoading(false);
    }
  };

  const getMetricLabel = (key: string) => {
    return key.replace(/_/g, ' ').replace(' pct', ' %').replace(' g', ' (g)');
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8">
      
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <span className="text-2xl">🔍</span>
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Ask a question about the data..."
          className="w-full pl-12 pr-4 py-4 bg-gray-900 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-lg text-white placeholder-gray-500 transition-all shadow-lg"
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="absolute inset-y-2 right-2 px-6 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>

      {/* Suggested Queries */}
      <div className="flex flex-wrap gap-2 justify-center">
        {SUGGESTED_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => handleSearch(q)}
            className="px-4 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-full text-sm text-gray-300 hover:text-white transition-all whitespace-nowrap"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-900/30 border border-red-900/50 rounded-lg text-red-200 text-center">
          {error}
        </div>
      )}

      {/* COMPARISON ANALYSIS CARD */}
      {activeQuery?.markdown_explanation && (
        <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-xl p-6 border border-blue-500/30 animate-in slide-in-from-top-4 duration-500">
          <div className="prose prose-invert max-w-none text-gray-200">
            <ReactMarkdown>{activeQuery.markdown_explanation}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Results */}
      {filteredData.length > 0 && (
        <div className="space-y-6 animate-in fade-in duration-500">
          
          {/* Active Filters Display (Only show in Filter Mode) */}
          {activeQuery && !activeQuery.force_ids && (
            <div className="flex gap-2 text-sm text-gray-400 bg-gray-900/50 p-3 rounded-lg border border-gray-800">
              <span className="font-semibold text-gray-300">Active logic:</span>
              {activeQuery.filters?.map((f, i) => (
                <span key={i} className="bg-gray-800 px-2 py-0.5 rounded text-xs border border-gray-700">
                  {getMetricLabel(f.field)} {f.operator} {f.value}
                </span>
              ))}
              {activeQuery.sort_by && (
                <span className="bg-gray-800 px-2 py-0.5 rounded text-xs border border-gray-700">
                  Sort: {getMetricLabel(activeQuery.sort_by)} ({activeQuery.sort_order})
                </span>
              )}
            </div>
          )}

          {/* Visualization - Only show for Filter Mode or if we have > 1 item in comparison */}
          {(!activeQuery?.force_ids || filteredData.length > 1) && (
             <div className="h-64 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filteredData} layout="vertical" margin={{ left: 20 }}>
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="brand" 
                    type="category" 
                    width={120} 
                    tick={{ fill: '#9ca3af', fontSize: 12 }} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar 
                    dataKey={activeQuery?.sort_by || 'cut_score'} 
                    radius={[0, 4, 4, 0]}
                  >
                    {filteredData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#3b82f6' : '#1f2937'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Data Table */}
          <div className="overflow-x-auto rounded-xl border border-gray-800 bg-gray-900">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-950/50">
                  <th className="p-4 font-semibold text-gray-400">Brand</th>
                  <th className="p-4 font-semibold text-gray-400 text-right">Price/Srv</th>
                  <th className="p-4 font-semibold text-gray-400 text-right">Protein %</th>
                  <th className="p-4 font-semibold text-gray-400 text-right">Leucine (g)</th>
                  <th className="p-4 font-semibold text-gray-400 text-right">Score (Cut)</th>
                  {activeQuery?.sort_by && !['price_per_serving','protein_pct','leucine_g','cut_score'].includes(activeQuery.sort_by) && (
                     <th className="p-4 font-semibold text-blue-400 text-right capitalize">
                       {getMetricLabel(activeQuery.sort_by)}
                     </th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filteredData.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="p-4 font-medium text-white">{item.brand}</td>
                    <td className="p-4 text-right text-gray-300">₹{item.price_per_serving}</td>
                    <td className="p-4 text-right text-gray-300">{Math.round(item.protein_pct)}%</td>
                    <td className="p-4 text-right text-gray-300">{item.leucine_g || '-'}</td>
                    <td className="p-4 text-right font-bold text-blue-400">
                      {item.cut_score ? (item.cut_score * 100).toFixed(0) + '%' : 'N/A'}
                    </td>
                    {activeQuery?.sort_by && !['price_per_serving','protein_pct','leucine_g','cut_score'].includes(activeQuery.sort_by) && (
                      <td className="p-4 text-right font-bold text-blue-400 bg-blue-900/10">
                         {typeof item[activeQuery.sort_by] === 'number' 
                           ? Number(item[activeQuery.sort_by]).toLocaleString(undefined, { maximumFractionDigits: 2 })
                           : String(item[activeQuery.sort_by])
                         }
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Empty State */}
      {!loading && filteredData.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">No brands match your criteria.</p>
          <p className="text-sm mt-2">Try relaxing filters or asking a different question.</p>
        </div>
      )}
    </div>
  );
}
