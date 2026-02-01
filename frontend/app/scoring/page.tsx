'use client';

import React from 'react';
import Navigation from '../../components/Navigation';

export default function ScoringExplanation() {
  return (
    <div className="min-h-screen bg-gray-950 text-white p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">How We Score Protein Powders</h1>
          <p className="text-gray-400">Transparent, rigorous, and science-backed analysis.</p>
        </header>

        <Navigation />

        <div className="space-y-12">
          
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-semibold text-blue-400 mb-4">The Logic</h2>
            <p className="text-gray-300 leading-relaxed">
              Our scoring engine evaluates protein powders based on objectively measurable data extracted directly from their nutrition labels. 
              We don't rely on marketing claims. Instead, we analyze the raw numbers—protein content, amino acid profiles, and ingredient transparency—to 
              calculate scores tailored to specific fitness goals.
            </p>
          </section>

          {/* Research Reference */}
          <section className="bg-gray-900 border border-blue-900/30 p-6 rounded-lg">
            <h3 className="text-xl font-semibold text-blue-300 mb-3">🔬 Backed by Research</h3>
            <p className="text-gray-400 mb-4">
              Our strict criteria for <strong>Amino Spiking</strong> (Taurine detection), <strong>Added Sugars</strong>, and <strong>Heavy Metals testing</strong> are informed by findings such as those from "The Citizens Protein Project".
            </p>
            <a 
              href="https://www.researchgate.net/publication/397629327_The_Citizens_Protein_Project_2_The_first_publicly_crowd-funded_observational_study_on_exhaustive_analysis_of_popular_whey_protein_supplements_in_India_reveal_poor_quality_and_deceptive_marketing_claim"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-blue-400 hover:text-blue-300 underline transition-colors"
            >
              Read the Research Paper ↗
            </a>
          </section>

          {/* Critical Penalties */}
          <section>
            <h2 className="text-2xl font-semibold text-red-400 mb-4">Critical Penalties</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-gray-900 p-5 rounded-lg border border-red-900/20">
                <h3 className="font-bold text-lg mb-2 text-white">🍬 Added Sugar</h3>
                <p className="text-gray-400 text-sm">
                  We penalize products with added sugar.
                  <br/>
                  <span className="text-green-400">&lt; 0.5g</span> : No penalty
                  <br/>
                  <span className="text-yellow-400">0.5g - 2.0g</span> : Moderate penalty
                  <br/>
                  <span className="text-red-400">&gt; 2.0g</span> : <strong>Significant Score Deduction</strong>
                </p>
              </div>

              <div className="bg-gray-900 p-5 rounded-lg border border-red-900/20">
                <h3 className="font-bold text-lg mb-2 text-white">🧪 Amino Spiking (Taurine)</h3>
                <p className="text-gray-400 text-sm">
                  The presence of cheap amino acids like <strong>Taurine</strong> or Glycine is a red flag for "amino spiking"—artificially inflating protein count.
                  <br/>
                  Any detected Taurine (&gt; 0g) triggers a spiking warning.
                </p>
              </div>

              <div className="bg-gray-900 p-5 rounded-lg border border-red-900/20">
                <h3 className="font-bold text-lg mb-2 text-white">⚠️ Label Credibility</h3>
                <p className="text-gray-400 text-sm">
                  Trust is paramount. We apply penalties if a label:
                  <ul className="list-disc list-inside mt-2 space-y-1 text-gray-500">
                    <li>Fails to list core macros (Proteins/Carbs/Fats)</li>
                    <li>Reports exactly 0mg Sodium (chemically unlikely)</li>
                  </ul>
                </p>
              </div>

              <div className="bg-gray-900 p-5 rounded-lg border border-red-900/20">
                <h3 className="font-bold text-lg mb-2 text-white">☠️ Safety Flags</h3>
                <p className="text-gray-400 text-sm">
                  For our <strong>CLEAN</strong> score, we check for evidence of <strong>Heavy Metals Testing</strong>. 
                  <br/>
                  Unknown or untested status results in a <strong>Warning Flag</strong> (previously a hard reject).
                </p>
              </div>
            </div>
          </section>

          {/* Scoring Modes */}
          <section>
             <h2 className="text-2xl font-semibold text-green-400 mb-4">Scoring Modes</h2>
             <div className="space-y-4">
                <div className="border-l-4 border-blue-500 pl-4 py-1">
                  <h3 className="text-xl font-bold text-white">CUT</h3>
                  <p className="text-gray-400">Focuses on high protein efficiency and low calories. Heavy penalties for fats, carbs, and sugars.</p>
                </div>
                <div className="border-l-4 border-purple-500 pl-4 py-1">
                  <h3 className="text-xl font-bold text-white">BULK</h3>
                  <p className="text-gray-400">Prioritizes total protein and growth-promoting amino acids (BCAAs, Leucine). More tolerant of calories.</p>
                </div>
                <div className="border-l-4 border-green-500 pl-4 py-1">
                  <h3 className="text-xl font-bold text-white">CLEAN</h3>
                  <p className="text-gray-400">The strictest standard. Demands heavy metals testing, zero additives, and transparency. No compromises.</p>
                </div>
             </div>
          </section>

        </div>
      </div>
    </div>
  );
}
