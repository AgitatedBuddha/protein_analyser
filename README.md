# Protein Powder Analyser

Extract and compare nutrition data from protein powder labels using LLM-powered image analysis.
Deployed at - https://protein-analyser-kaol4j45z-agitatedbuddhas-projects.vercel.app/

## Features

- **Extract nutrition profiles** from label images (serving size, protein, carbs, fat, sodium)
- **Extract amino acid profiles** (EAAs, BCAAs, SEAAs, NEAAs with individual breakdowns)
- **Compute derived values** (BCAAs from individual amino acids, category totals)
- **Track pricing** (price per kg, price per serving)
- **Scoring engine** for comparing products across different goals (cut, bulk, clean)

## Setup

```bash
# Clone and enter directory
cd analyser

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set API key (Gemini recommended)
export GOOGLE_API_KEY=your_api_key
```

## Usage

### Extract nutrition profile
```bash
analyse nutrients images/BrandName
# Output: output/BrandName/nutrients.json
```

### Extract amino acid profile
```bash
analyse aminoacids images/BrandName
# Output: output/BrandName/aminoacids.json
```

### Extract both profiles with pricing
```bash
analyse all images/BrandName --weight 1.0 --price 2499
# Output: output/BrandName/BrandName.json
```

### Check API credentials
```bash
analyse check
```

## Project Structure

```
analyser/
├── cli.py                 # Command-line interface
├── extractors/            # Modular extractors
│   ├── base.py            # Base extractor with LLM logic
│   ├── nutrition.py       # Nutrition label extractor
│   └── aminoacid.py       # Amino acid profile extractor
├── skills/                # Extraction prompts and schemas
│   ├── extract_nutrition_label_v1.prompt.md
│   ├── extract_nutrition_label_v1.schema.json
│   ├── extract_aminoacid_profile_v1.prompt.md
│   ├── extract_aminoacid_profile_v1.schema.json
│   └── scoring_spec.yml   # Scoring specification
├── images/                # Source label images
│   └── <brand_name>/
│       ├── nutrients_profile.png
│       └── aminoacid_profile.png
├── output/                # Extracted JSON data
│   └── <brand_name>/
│       └── <brand_name>.json
└── tests/                 # Unit tests
```

## Output Format

```json
{
  "brand": "BrandName",
  "product_info": {
    "weight_kg": 1.0,
    "price_inr": 2499,
    "price_per_kg": 2499.0,
    "servings_per_pack": 30.8,
    "price_per_serving": 81.14
  },
  "nutrients": {
    "extracted_fields": {
      "serving_size_g": 32.5,
      "protein_g_per_serving": 25.0,
      "energy_kcal_per_serving": 121.44,
      ...
    }
  },
  "aminoacids": {
    "extracted_fields": {
      "eaas": {
        "total_g": 11.226,
        "bcaas": {
          "total_g": 4.738,
          "leucine_g": 2.269,
          ...
        }
      }
    }
  }
}
```

## Brands Analysed

| Brand | Price | Weight | Status |
|-------|-------|--------|--------|
| CosmixPlantProtein | ₹2,122 | 1.0kg | ✓ |
| happycultures | ₹999 | 0.505kg | ✓ |
| millePlantProtein | ₹1,436 | 0.5kg | ✓ |
| muscle_blaze | ₹2,299 | 1.0kg | ✓ |
| ON_vanilla | ₹3,199 | 0.907kg | ✓ |
| OriginPlantProtein | ₹2,379 | 0.975kg | ✓ |
| oziva | ₹1,299 | 0.5kg | ✓ |
| superyou | ₹2,249 | 1.0kg | ✓ |
| truebasics | ₹2,399 | 1.0kg | ✓ |
| trunativ | ₹2,799 | 0.907kg | ✓ |
| wellbeing | ₹2,398 | 1.0kg | ✓ |
| wholetruth | ₹2,538 | 1.0kg | ✓ |

## Testing

```bash
# Run unit tests
pytest tests/test_extractor.py -v
```

## License

MIT
