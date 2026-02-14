"""
Import/Update SKU Mappings from Excel file into Supabase
Usage: python import_sku_mappings.py <filepath>
"""

import sys
import pandas as pd
import requests
import json
from pathlib import Path

# Supabase configuration
SUPABASE_URL = "https://iqcokafrtqnemalwhdmf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY29rYWZydHFuZW1hbHdoZG1mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTA4NTAxNCwiZXhwIjoyMDg2NjYxMDE0fQ.OB4FZSoi02IdGqKFO_xpkwF5woxlFmJK-W4dcRLZ7BY"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def import_sku_mappings(filepath):
    """Import SKU mappings from Excel file"""
    print(f"Processing SKU mapping file: {filepath}", file=sys.stderr)

    # Load Excel file
    df = pd.read_excel(filepath)
    print(f"Loaded {len(df)} SKU mappings from file", file=sys.stderr)

    # Clean and prepare records
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

    # Count mappings by type
    cantaloupe_count = sum(1 for r in records if r['cantaloupe_name'])
    haha_count = sum(1 for r in records if r['haha_ai_name'])
    nayax_count = sum(1 for r in records if r['nayax_name'])

    # Upsert into Supabase in batches
    batch_size = 100
    updated_count = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sku_mappings",
            headers=headers,
            data=json.dumps(batch)
        )
        if response.status_code in [200, 201]:
            updated_count += len(batch)
            print(f"Processed batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}", file=sys.stderr)
        else:
            print(f"Error in batch: {response.text}", file=sys.stderr)

    # Return result as JSON
    result = {
        'totalSKUs': len(records),
        'cantaloupeMappings': cantaloupe_count,
        'hahaAIMappings': haha_count,
        'nayaxMappings': nayax_count,
        'updated': updated_count
    }

    print(json.dumps(result))
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_sku_mappings.py <filepath>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    import_sku_mappings(filepath)
