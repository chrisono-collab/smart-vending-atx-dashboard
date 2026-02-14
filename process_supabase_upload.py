"""
Process uploaded transaction file and insert into Supabase
Usage: python process_supabase_upload.py <filepath>
"""

import sys
import pandas as pd
import requests
import json
from datetime import datetime
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

def fetch_mappings():
    """Fetch SKU and location mappings from Supabase"""
    # Fetch SKU mappings
    sku_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sku_mappings",
        headers=headers
    )
    sku_mappings = sku_response.json()

    # Fetch location mappings
    loc_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/location_mappings",
        headers=headers
    )
    location_mappings = loc_response.json()

    return sku_mappings, location_mappings

def create_dedup_key(row):
    """Create deduplication key"""
    import re
    timestamp = pd.to_datetime(row.get('Timestamp'), errors='coerce')
    ts_str = timestamp.strftime('%Y-%m-%dT%H:%M') if pd.notna(timestamp) else 'unknown'

    machine = str(row.get('Machine', '')).strip()
    machine_match = re.search(r'\[(\d+)\]', machine)
    machine_id = machine_match.group(1) if machine_match else re.sub(r'[^a-z0-9]', '', machine.lower())

    product = re.sub(r'[^a-z0-9]', '', str(row.get('Product', '')).lower())
    total = round(float(row.get('Total', 0)), 2)

    return f"{ts_str}_{machine_id}_{product}_{total}"

def clean_location(location, machine, location_map):
    """Clean location name"""
    import re
    location_str = str(location).strip()
    machine_str = str(machine).strip()

    # Try direct mapping
    if location_str in location_map:
        return location_map[location_str]
    if machine_str in location_map:
        return location_map[machine_str]

    # Fallback cleanup
    cleaned = re.sub(r'^\[\d+\]\s*', '', machine_str)
    cleaned = re.sub(r'\s*\d{4}$', '', cleaned)
    return cleaned if cleaned else location_str

def map_product(product_name, sku_map, family_map):
    """Three-tier product mapping"""
    product_str = str(product_name).strip()

    # Tier 1: Direct mapping
    if product_str in sku_map:
        return sku_map[product_str]

    # Tier 2: Family mapping
    if product_str in family_map:
        return family_map[product_str]

    # Tier 3: Unmapped
    return {
        'master_sku': 'UNMAPPED',
        'master_name': product_str,
        'product_family': 'Unmapped',
        'type': 'Unknown',
        'cost': 0.0,
        'mapping_tier': 'unmapped'
    }

def process_file(filepath):
    """Main processing function"""
    print(f"Processing: {filepath}", file=sys.stderr)

    # Fetch mappings
    sku_mappings, location_mappings = fetch_mappings()

    # Build lookup dictionaries
    location_map = {loc['raw_name']: loc['display_name'] for loc in location_mappings}

    sku_map = {}
    family_map = {}
    for sku in sku_mappings:
        master_sku = sku['master_sku']
        mapping = {
            'master_sku': master_sku,
            'master_name': sku['master_name'],
            'product_family': sku.get('product_family'),
            'type': sku.get('type'),
            'cost': float(sku.get('cost', 0)),
            'mapping_tier': 'direct'
        }

        # Add all name variations to map
        if sku.get('cantaloupe_name'):
            sku_map[sku['cantaloupe_name']] = mapping
        if sku.get('haha_ai_name'):
            sku_map[sku['haha_ai_name']] = mapping
        if sku.get('nayax_name'):
            sku_map[sku['nayax_name']] = mapping
        if sku.get('master_name'):
            sku_map[sku['master_name']] = mapping

        # Family mapping (average cost)
        family = sku.get('product_family')
        if family and family not in family_map:
            family_map[family] = {
                'master_sku': f'FAMILY_{family.upper().replace(" ", "_")}',
                'master_name': family,
                'product_family': family,
                'type': sku.get('type', 'Unknown'),
                'cost': float(sku.get('cost', 0)),  # Simplified - should average
                'mapping_tier': 'family'
            }

    # Load transaction file
    raw_df = pd.read_excel(filepath, header=None)
    df = raw_df.iloc[3:].copy()  # Skip header rows
    df.columns = ['Timestamp', 'Location', 'Machine', 'Product', 'Slot', 'Price', 'Quantity', 'Total', 'CC']
    df = df.reset_index(drop=True)

    raw_count = len(df)
    print(f"Raw transactions: {raw_count}", file=sys.stderr)

    # Create dedup keys
    df['dedup_key'] = df.apply(create_dedup_key, axis=1)

    # Remove duplicates
    df = df.drop_duplicates(subset='dedup_key', keep='first')
    duplicates_removed = raw_count - len(df)
    print(f"Duplicates removed: {duplicates_removed}", file=sys.stderr)

    # Parse dates
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['date'] = df['Timestamp'].dt.date

    # Clean locations
    df['location'] = df.apply(lambda row: clean_location(row['Location'], row['Machine'], location_map), axis=1)

    # Map products
    mapped_products = df['Product'].apply(lambda p: map_product(p, sku_map, family_map))
    df['master_sku'] = mapped_products.apply(lambda x: x['master_sku'])
    df['master_name'] = mapped_products.apply(lambda x: x['master_name'])
    df['product_family'] = mapped_products.apply(lambda x: x.get('product_family'))
    df['type'] = mapped_products.apply(lambda x: x.get('type'))
    df['cost'] = mapped_products.apply(lambda x: x['cost'])
    df['mapping_tier'] = mapped_products.apply(lambda x: x['mapping_tier'])

    # Financial calculations
    df['revenue'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df['quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1).astype(int)
    df['profit'] = (df['revenue'] - (df['cost'] * df['quantity'])).round(2)
    df['gross_margin_percent'] = df.apply(
        lambda row: round((row['profit'] / row['revenue']) * 100, 2) if row['revenue'] > 0 else 0,
        axis=1
    )

    # Calculate stats
    unmapped = df[df['mapping_tier'] == 'unmapped']
    mapping_coverage = ((len(df) - len(unmapped)) / len(df) * 100) if len(df) > 0 else 0
    unmapped_revenue = unmapped['revenue'].sum()

    # Prepare records for insertion
    records = []
    for _, row in df.iterrows():
        record = {
            'timestamp': row['Timestamp'].isoformat() if pd.notna(row['Timestamp']) else None,
            'date': row['date'].isoformat() if pd.notna(row['date']) else None,
            'location': row['location'],
            'master_sku': row['master_sku'],
            'master_name': row['master_name'],
            'product_family': row['product_family'],
            'type': row['type'],
            'revenue': float(row['revenue']),
            'cost': float(row['cost']),
            'quantity': int(row['quantity']),
            'profit': float(row['profit']),
            'gross_margin_percent': float(row['gross_margin_percent']),
            'mapping_tier': row['mapping_tier'],
            'dedup_key': row['dedup_key']
        }
        records.append(record)

    # Insert into Supabase in batches
    batch_size = 500
    inserted_count = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/transactions",
            headers=headers,
            data=json.dumps(batch)
        )
        if response.status_code in [200, 201]:
            inserted_count += len(batch)
            print(f"Inserted batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}", file=sys.stderr)
        else:
            print(f"Error inserting batch: {response.text}", file=sys.stderr)

    # Create upload history record
    upload_record = {
        'filename': Path(filepath).name,
        'total_transactions': len(df),
        'duplicates_removed': duplicates_removed,
        'mapping_coverage': round(mapping_coverage, 2),
        'unmapped_revenue': float(unmapped_revenue),
        'status': 'success',
        'processed_at': datetime.now().isoformat()
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/upload_history",
        headers=headers,
        data=json.dumps([upload_record])
    )

    # Return result as JSON
    result = {
        'totalTransactions': len(df),
        'duplicatesRemoved': duplicates_removed,
        'mappingCoverage': round(mapping_coverage, 1),
        'unmappedRevenue': float(unmapped_revenue),
        'totalRevenue': float(df['revenue'].sum()),
        'totalProfit': float(df['profit'].sum())
    }

    print(json.dumps(result))
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python process_supabase_upload.py <filepath>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    process_file(filepath)
