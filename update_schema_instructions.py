
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SECRET_KEY")
        return None
    return create_client(url, key)

def update_schema():
    supabase = get_supabase_client()
    if not supabase:
        return

    print("Updating schema...")

    # SQL to add columns to nutrients table
    add_columns_sql = """
    ALTER TABLE nutrients ADD COLUMN IF NOT EXISTS added_sugar_g REAL;
    ALTER TABLE nutrients ADD COLUMN IF NOT EXISTS heavy_metals_tested BOOLEAN;
    """

    # SQL to recreate leaderboard view with new columns
    recreate_view_sql = """
    DROP VIEW IF EXISTS leaderboard;
    
    CREATE OR REPLACE VIEW leaderboard AS
    SELECT 
        b.id,
        b.name AS brand,
        b.price_per_serving,
        b.price_per_kg,
        n.serving_size_g,       -- NEW: Serving size
        n.protein_g,
        n.energy_kcal,
        n.added_sugar_g,
        n.heavy_metals_tested,
        a.eaas_total_g,
        a.bcaas_total_g,
        a.leucine_g,            -- NEW: Key muscle builder
        a.glutamic_acid_g,      -- NEW: Recovery
        a.arginine_g,           -- NEW: Pump/Blood flow
        s.protein_pct,
        s.protein_per_100_kcal, -- NEW: Efficiency
        s.eaas_pct,
        s.non_protein_macros_g, -- NEW: Purity check
        s.amino_spiking_suspected,
        s.cut_score,
        s.cut_rejected,
        s.bulk_score,
        s.bulk_rejected,
        s.clean_score,
        s.clean_rejected
    FROM brands b
    LEFT JOIN nutrients n ON b.id = n.brand_id
    LEFT JOIN scores s ON b.id = s.brand_id
    LEFT JOIN aminoacids a ON b.id = a.brand_id
    ORDER BY s.cut_score DESC NULLS LAST;
    """

    try:
        # We can't execute multiple statements at once easily with RPC unless we wrap in a function,
        # but supabase-py might allow raw SQL via rpc if we had a function "exec_sql".
        # However, standard PostgREST doesn't expose raw SQL execution.
        # We might need to use the `postgres` library if we have connection string, 
        # OR hopefully the user has an RPC function for this?
        
        # Checking if we can execute raw SQL...
        # Many Supabase implementations don't allow raw SQL from client for security.
        # BUT, since we have the DB *Secret* Key (service role), we might be able to.
        # Actually, Supabase-js structured client doesn't support raw SQL query directly usually.
        
        # PLAN B: We can try creating an RPC function via the dashboard? No, I can't access dashboard.
        # Check if `db_builder.py` uses `execute`? No it uses `.table()...`
        
        # If I cannot execute SQL, I have to ask the user to run it in the SQL editor.
        pass
    except Exception as e:
        print(f"Error: {e}")

    # Wait, look at db_builder.py imports. `from supabase import create_client`.
    # It does NOT have psycopg2.
    
    print("---------------------------------------------------------")
    print("IMPORTANT: Automatic schema migration via Python client is restricted.")
    print("Please run the following SQL in your Supabase SQL Editor:")
    print("---------------------------------------------------------")
    print(add_columns_sql)
    print(recreate_view_sql)
    print("---------------------------------------------------------")

if __name__ == "__main__":
    update_schema()
