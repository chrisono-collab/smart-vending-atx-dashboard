"""
Seed initial SKU and Location mappings into Supabase
"""

import pandas as pd
import requests
import json

# Supabase configuration
SUPABASE_URL = "https://iqcokafrtqnemalwhdmf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY29rYWZydHFuZW1hbHdoZG1mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTA4NTAxNCwiZXhwIjoyMDg2NjYxMDE0fQ.OB4FZSoi02IdGqKFO_xpkwF5woxlFmJK-W4dcRLZ7BY"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def seed_sku_mappings():
    """Import SKU mappings from cleaned Excel file"""
    print("="*60)
    print("Seeding SKU Mappings")
    print("="*60 + "\n")

    try:
        df = pd.read_excel('data/vendsoft/sku-mapping-cleaned.xlsx')
        print(f"Loaded {len(df)} SKU mappings from file")

        records = []
        for _, row in df.iterrows():
            record = {
                'master_sku': str(row['Master_SKU']),
                'master_name': str(row.get('Master_Name', '')),
                'product_family': str(row.get('Product_Family', '')) if pd.notna(row.get('Product_Family')) else None,
                'type': str(row.get('Type', '')) if pd.notna(row.get('Type')) else None,
                'cost': float(row.get('Cost', 0)) if pd.notna(row.get('Cost')) else 0,
                'cantaloupe_name': str(row.get('Cantaloupe_Name')) if pd.notna(row.get('Cantaloupe_Name')) else None,
                'haha_ai_name': str(row.get('Haha_AI_Name')) if pd.notna(row.get('Haha_AI_Name')) else None,
                'nayax_name': str(row.get('Nayax_Name')) if pd.notna(row.get('Nayax_Name')) else None,
            }
            records.append(record)

        # Insert in batches using REST API
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/sku_mappings",
                headers=headers,
                data=json.dumps(batch)
            )
            if response.status_code in [200, 201]:
                print(f"  Inserted batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}")
            else:
                print(f"  Error in batch {i//batch_size + 1}: {response.text}")

        print(f"\n✓ Successfully imported {len(records)} SKU mappings")
        return True

    except Exception as e:
        print(f"\n✗ Error seeding SKU mappings: {e}")
        return False

def seed_location_mappings():
    """Import location mappings from CSV file"""
    print("\n" + "="*60)
    print("Seeding Location Mappings")
    print("="*60 + "\n")

    try:
        df = pd.read_csv('location_mapping.csv')
        print(f"Loaded {len(df)} location mappings from file")

        records = []
        for _, row in df.iterrows():
            record = {
                'raw_name': str(row['raw_name']),
                'display_name': str(row['display_name'])
            }
            records.append(record)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/location_mappings",
            headers=headers,
            data=json.dumps(records)
        )
        if response.status_code in [200, 201]:
            print(f"\n✓ Successfully imported {len(records)} location mappings")
        else:
            print(f"\n✗ Error: {response.text}")
            return False
        return True

    except Exception as e:
        print(f"\n✗ Error seeding location mappings: {e}")
        return False

if __name__ == '__main__':
    print("\n🌱 Seeding Supabase Database\n")

    sku_success = seed_sku_mappings()
    loc_success = seed_location_mappings()

    print("\n" + "="*60)
    if sku_success and loc_success:
        print("✅ All data seeded successfully!")
    else:
        print("⚠️  Some errors occurred during seeding")
    print("="*60 + "\n")
