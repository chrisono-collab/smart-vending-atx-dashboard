"""
Create Supabase database schema
Run this script to set up all tables
"""

from supabase_client import supabase

def create_schema():
    """Execute schema.sql to create all tables"""
    print("Creating Supabase database schema...")

    # Read schema file
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()

    # Execute SQL (Note: Supabase Python client doesn't support raw SQL directly)
    # You need to run this in Supabase SQL Editor or use psycopg2
    print("\n" + "="*60)
    print("IMPORTANT: Run the SQL in schema.sql manually")
    print("="*60)
    print("\n1. Go to: https://supabase.com/dashboard/project/iqcokafrtqnemalwhdmf/sql")
    print("2. Copy the contents of schema.sql")
    print("3. Paste into SQL Editor")
    print("4. Click 'RUN'")
    print("\nOr use the Supabase CLI:")
    print("  supabase db push")
    print("\n" + "="*60)

if __name__ == '__main__':
    create_schema()
