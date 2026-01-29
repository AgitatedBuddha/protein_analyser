import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

// Scoring spec embedded for context
const SCORING_CONTEXT = `
You are analyzing protein powder scores based on this scoring specification:

SCORING MODES:
1. CUT MODE - Optimizes for cutting (weight loss while preserving muscle)
   - Hard reject if: protein_per_100_kcal < 18 OR leucine_g_per_serving < 2.2
   - Weights: protein_per_100_kcal (40%), leucine (30%), protein_pct (20%), EAAs (10%)
   - Penalties: high sodium, high non-protein macros

2. BULK MODE - Optimizes for muscle building
   - No hard rejects
   - Weights: protein_pct (35%), EAAs (30%), leucine (25%), protein_g (10%)
   - Minimal penalties

3. CLEAN MODE - Optimizes for purity and avoiding additives
   - Hard reject if: sodium > 250mg OR added sugar OR amino spiking suspected
   - Weights: low sodium (35%), low non-protein macros (30%), EAAs (15%), leucine (10%), protein_pct (10%)

AMINO SPIKING DETECTION:
- Suspected if 2+ of: glycine > 5% of protein, EAAs < 40%, BCAAs > 60% of EAAs, or EAAs exceed protein

KEY METRICS:
- protein_pct: protein_g / serving_size_g (higher = more protein per scoop)
- protein_per_100_kcal: efficiency metric for cutting
- eaas_pct: essential amino acids as % of protein (higher = better quality)
- leucine: key amino acid for muscle protein synthesis (need 2.7g+ per serving)
`;

export async function POST(request: NextRequest) {
  try {
    const { brand, mode } = await request.json();

    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json(
        { error: 'GEMINI_API_KEY not configured' },
        { status: 500 }
      );
    }

    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

    const scoreKey = `${mode}_score`;
    const rejectedKey = `${mode}_rejected`;
    const reasonKey = `${mode}_rejection_reason`;

    const prompt = `${SCORING_CONTEXT}

Now explain the ${mode.toUpperCase()} score for this protein powder brand:

Brand: ${brand.brand}
Price per serving: ₹${brand.price_per_serving?.toFixed(0) || 'N/A'}
Protein per serving: ${brand.protein_g || 'N/A'}g
Energy per serving: ${brand.energy_kcal || 'N/A'} kcal
Protein %: ${brand.protein_pct ? (brand.protein_pct * 100).toFixed(1) : 'N/A'}%
Protein per 100 kcal: ${brand.protein_per_100_kcal?.toFixed(1) || 'N/A'}g
EAAs %: ${brand.eaas_pct ? (brand.eaas_pct * 100).toFixed(1) : 'N/A'}%
Leucine per serving: ${brand.leucine_g_per_serving?.toFixed(2) || 'N/A'}g
Amino spiking suspected: ${brand.amino_spiking_suspected ? 'Yes' : 'No'}

Score: ${brand[scoreKey] ? (brand[scoreKey] * 100).toFixed(0) : 'N/A'}%
Rejected: ${brand[rejectedKey] ? 'Yes' : 'No'}
${brand[reasonKey] ? `Rejection reason: ${brand[reasonKey]}` : ''}

Provide a concise 2-3 sentence explanation of why this brand got this ${mode} score. Focus on the key factors that influenced the score. Be specific about what's good or bad about this product for someone in ${mode} mode. Use plain language.`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const explanation = response.text();

    return NextResponse.json({ explanation });
  } catch (error) {
    console.error('Explain API error:', error);
    return NextResponse.json(
      { error: 'Failed to generate explanation' },
      { status: 500 }
    );
  }
}
