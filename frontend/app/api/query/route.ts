
import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client
// Service role key preferred for reliable fetching if RLS is strict, but using publishable for read-only is fine if RLS allows public read.
// We'll use the environment variables already set.
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!; 
const supabase = createClient(supabaseUrl, supabaseKey);


// --- PROMPT DEFINITIONS ---

// 1. INTENT CLASSIFIER & FILTER GENERATOR
const SCHEMA_DEFINITION = `
You are a data query assistant for a protein powder database. 
Your job is to classify the user's intent and output the corresponding JSON.

INTENT TYPES:
1. "filter": User wants to see a list of brands matching criteria (e.g. "high protein", "cheapest").
2. "comparison": User wants to compare specific brands or asks "Result X vs Result Y" (e.g. "Why is MuscleBlaze better than Oziva?", "Compare Truth vs Origin").

AVAILABLE FIELDS (number types) for Filtering:
- price_per_serving (in INR)
- protein_pct (0-100)
- protein_g (per serving)
- energy_kcal (per serving)
- added_sugar_g (per serving)
- sodium_mg (per serving)
- total_fat_g (per serving)
- carbohydrates_g (per serving)
- eaas_total_g (per serving)
- bcaas_total_g (per serving)
- leucine_g (per serving)
- glutamic_acid_g (per serving)
- arginine_g (per serving)
- protein_per_100_kcal (Protein efficiency)
- non_protein_macros_g (Carbs + Fat)
- amino_spiking_suspected (boolean: 0 or 1)
- heavy_metals_tested (boolean: 0 or 1)
- price_per_kg (for bulk value)
- serving_size_g
- cut_score (0-1.0)
- bulk_score (0-1.0)
- clean_score (0-1.0)

OUTPUT JSON FORMAT:
{
  "type": "filter" | "comparison",
  
  // IF type = "filter":
  "filters": [
    { "field": "string", "operator": "gt|lt|eq|gte|lte", "value": number }
  ],
  "sort_by": "string", "sort_order": "asc|desc", "limit": number,

  // IF type = "comparison":
  "brand_names": ["string", "string"], // Extract 2+ brand names mentioned
  "comparison_question": "string"      // The specific question to answer
}

EXAMPLES:
User: "Cheapest options"
JSON: { "type": "filter", "filters": [], "sort_by": "price_per_serving", "sort_order": "asc", "limit": 5 }

User: "Why is MuscleBlaze rated higher than Oziva?"
JSON: { "type": "comparison", "brand_names": ["MuscleBlaze", "Oziva"], "comparison_question": "Why is MuscleBlaze rated higher than Oziva?" }

User: "Compare Origin and Truth"
JSON: { "type": "comparison", "brand_names": ["Origin", "Truth"], "comparison_question": "Compare Origin and Truth" }
`;

// 2. STRICT COMPARISON PROMPT
const COMPARISON_SYSTEM_PROMPT = `
You are a strict data comparison engine for protein powders. 
You will be given JSON data for specific brands.
Your job is to answer the user's question based ONLY on this data.

RULES:
1. STRICT DATA ONLY: Do not use outside knowledge. If the answer isn't in the data, say "I cannot determine this from the available data."
2. NO OFF-TOPIC: If the user asks about politics, code, or general life, reply "I can only compare the protein data provided."
3. BE SPECIFIC: Cite numbers (e.g. "Brand A has 25g protein vs Brand B's 20g").
4. CONCISE: Keep the answer under 150 words.
5. FORMAT: Use Markdown (bolding key numbers).
`;


// --- HELPER FUNCTIONS ---

async function fetchBrandData(searchNames: string[]) {
  // We need to find the actual brand names in DB that match the user's search terms
  // Supabase textSearch or ilike is good, but for multiple brands, it's tricky.
  // Strategy: Fetch ALL brands (small dataset ~12 items) and fuzzy match in JS.
  // This is faster/cheaper than complex SQL for this scale.
  
  const { data: allBrands } = await supabase.from('leaderboard').select('*');
  
  if (!allBrands) return [];

  const matchedBrands = [];
  
  for (const searchName of searchNames) {
    const term = searchName.toLowerCase();
    // Simple containment match
    const match = allBrands.find(b => 
      b.brand.toLowerCase().includes(term) || 
      term.includes(b.brand.toLowerCase())
    );
    if (match) matchedBrands.push(match);
  }

  // Remove duplicates
  return Array.from(new Set(matchedBrands));
}


export async function POST(request: Request) {
  try {
    const { prompt } = await request.json();
    
    if (!prompt) return NextResponse.json({ error: "No prompt provided" }, { status: 400 });

    const apiKey = process.env.GOOGLE_API_KEY || process.env.NEXT_PUBLIC_GOOGLE_API_KEY;
    if (!apiKey) return NextResponse.json({ error: "Missing API Key" }, { status: 500 });

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ 
      model: "gemini-2.0-flash",
      generationConfig: { responseMimeType: "application/json" } 
    });

    // STEP 1: Classify Intent
    const planResult = await model.generateContent([
      SCHEMA_DEFINITION,
      `User Query: "${prompt}"\nJSON:`
    ]);
    
    const cmd = JSON.parse(planResult.response.text());

    // --- CASE A: FILTER ---
    if (cmd.type === 'filter') {
      return NextResponse.json(cmd);
    }

    // --- CASE B: COMPARISON ---
    if (cmd.type === 'comparison') {
      const brands = await fetchBrandData(cmd.brand_names);
      
      if (brands.length < 2) {
        return NextResponse.json({
          type: "comparison",
          markdown_explanation: `I couldn't find data for all the brands you mentioned. I found: ${brands.map(b => b.brand).join(", ") || "None"}. \nPlease try using exact brand names.`,
          filters: [], sort_by: null, sort_order: null, limit: 0 // Fallback to empty
        });
      }

      // Prepare context for Second LLM
      const context = `
USER QUESTION: "${cmd.comparison_question}"

BRAND DATA:
${JSON.stringify(brands, null, 2)}
`;
      
      // Strict Text Generation
      const analysisModel = genAI.getGenerativeModel({ model: "gemini-2.0-flash" }); // Text output
      const analysisResult = await analysisModel.generateContent([
        COMPARISON_SYSTEM_PROMPT,
        context
      ]);

      const explanation = analysisResult.response.text();

      return NextResponse.json({
        type: "comparison",
        markdown_explanation: explanation,
        // Also return the brands as the dataset so the UI can show the table below the text
        filters: [], // No filters needed, we show these specific rows
        force_ids: brands.map(b => b.id) // Special field to force UI to show these IDs
      });
    }

    return NextResponse.json({ error: "Unknown query type" }, { status: 400 });

  } catch (error) {
    console.error("Query Error:", error);
    return NextResponse.json({ error: "Failed to process query" }, { status: 500 });
  }
}
