"""
Setup Supabase database - create all tables and seed initial data
"""

import os
from supabase_client import supabase

def create_tables():
    """Create all database tables"""
    print("="*60)
    print("Setting up Supabase Database")
    print("="*60 + "\n")

    # Read and execute schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()

    # Split into individual statements
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

    print(f"Executing {len(statements)} SQL statements...\n")

    for i, statement in enumerate(statements, 1):
        if statement:
            try:
                # Execute using Supabase RPC
                supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✓ Statement {i}/{len(statements)} executed")
            except Exception as e:
                # Most statements will work, some might fail if tables already exist
                if 'already exists' in str(e).lower():
                    print(f"⚠ Statement {i}/{len(statements)} - Table already exists (skipping)")
                else:
                    print(f"✗ Statement {i}/{len(statements)} - Error: {str(e)[:100]}")

    print("\n" + "="*60)
    print("Database setup complete!")
    print("="*60)

def seed_mappings():
    """Seed SKU and location mappings from existing files"""
    print("\nSeeding initial data...")

    try:
        # Import existing SKU mappings
        import pandas as pd

        # SKU mappings
        print("\n1. Importing SKU mappings...")
        sku_df = pd.read_excel('data/vendsoft/sku-mapping-cleaned.xlsx')

        sku_records = []
        for _, row in sku_df.iterrows():
            sku_records.append({
                'master_sku': row['Master_SKU'],
                'master_name': row.get('Master_Name', ''),
                'product_family': row.get('Product_Family', ''),
                'type': row.get('Type', ''),
                'cost': float(row.get('Cost', 0)) if pd.notna(row.get('Cost')) else 0,
                'cantaloupe_name': row.get('Cantaloupe_Name') if pd.notna(row.get('Cantaloupe_Name')) else None,
                'haha_ai_name': row.get('Haha_AI_Name') if pd.notna(row.get('Haha_AI_Name')) else None,
                'nayax_name': row.get('Nayax_Name') if pd.notna(row.get('Nayax_Name')) else None,
            })

        # Insert in batches
        batch_size = 100
        for i in range(0, len(sku_records), batch_size):
            batch = sku_records[i:i+batch_size]
            supabase.table('sku_mappings').upsert(batch).execute()
            print(f"   Imported {min(i+batch_size, len(sku_records))}/{len(sku_records)} SKUs")

        print(f"✓ Imported {len(sku_records)} SKU mappings")

        # Location mappings
        print("\n2. Importing location mappings...")
        loc_df = pd.read_csv('location_mapping.csv')

        loc_records = []
        for _, row in loc_df.iterrows():
            loc_records.append({
                'raw_name': row['raw_name'],
                'display_name': row['display_name']
            })

        supabase.table('location_mappings').upsert(loc_records).execute()
        print(f"✓ Imported {len(loc_records)} location mappings")

        print("\n" + "="*60)
        print("Data seeding complete!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error seeding data: {e}")
        print("You can seed data manually later using the admin interface")

if __name__ == '__main__':
    create_tables()
    print("\nWould you like to seed initial mappings from existing files? (y/n)")
    response = input("> ").strip().lower()
    if response == 'y':
        seed_mappings()
