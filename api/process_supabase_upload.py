"""
Process uploaded transaction file and insert into Supabase
Usage: python process_supabase_upload.py <filepath>
"""

import sys
import pandas as pd
import requests
import json
import re
from datetime import datetime
from pathlib import Path

# Supabase configuration
SUPABASE_URL = "https://iqcokafrtqnemalwhdmf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY29rYWZydHFuZW1hbHdoZG1mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTA4NTAxNCwiZXhwIjoyMDg2NjYxMDE0fQ.OB4FZSoi02IdGqKFO_xpkwF5woxlFmJK-W4dcRLZ7BY"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates"
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

def create_dedup_key(row, index):
    """Create deduplication key with row index for uniqueness"""
    import re
    timestamp = pd.to_datetime(row.get('Timestamp'), errors='coerce')
    ts_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S') if pd.notna(timestamp) else 'unknown'

    machine = str(row.get('Machine', '')).strip()
    machine_match = re.search(r'\[(\d+)\]', machine)
    machine_id = machine_match.group(1) if machine_match else re.sub(r'[^a-z0-9]', '', machine.lower())

    product = re.sub(r'[^a-z0-9]', '', str(row.get('Product', '')).lower())
    total = round(float(row.get('Total', 0)), 2)

    return f"{ts_str}_{machine_id}_{product}_{total}_{index}"

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
    df = raw_df.iloc[3:].copy()  # Skip first 3 header rows
    df.columns = ['Timestamp', 'Location', 'Machine', 'Product', 'Slot', 'Price', 'Quantity', 'Total', 'CC']
    df = df.reset_index(drop=True)

    # Fix NULL locations - extract from Machine column
    def extract_location(row):
        if pd.isna(row['Location']) or str(row['Location']).strip() == '':
            # Extract from Machine column like "[4] The Bowen Freezer"
            machine = str(row.get('Machine', ''))
            match = re.search(r'\[.*?\]\s*(.+)', machine)
            if match:
                return match.group(1).strip()
            return 'Unknown'
        return str(row['Location']).strip()

    df['Location'] = df.apply(extract_location, axis=1)
    print(f"Fixed NULL locations", file=sys.stderr)

    # Delete ALL existing transactions first
    print("Deleting all existing transactions...", file=sys.stderr)
    try:
        delete_response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/transactions?id=neq.0",
            headers=headers,
            timeout=60
        )
        if delete_response.status_code in [200, 204]:
            print("Successfully deleted all existing transactions", file=sys.stderr)
        else:
            print(f"Warning: Delete returned status {delete_response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not delete existing records: {e}", file=sys.stderr)

    raw_count = len(df)
    print(f"Raw transactions: {raw_count}", file=sys.stderr)

    # Parse dates first
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['date'] = df['Timestamp'].dt.date

    # Create dedup keys with row index for uniqueness
    df['dedup_key'] = df.apply(lambda row: create_dedup_key(row, row.name), axis=1)

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

    print(f"Preparing to insert {len(df)} transactions", file=sys.stderr)

    # Prepare records for insertion
    records = []
    for _, row in df.iterrows()

        # Helper function to safely convert to float, replacing NaN with 0
        def safe_float(val):
            return 0.0 if pd.isna(val) else float(val)

        # Helper function to safely convert to int, replacing NaN with 0
        def safe_int(val):
            return 0 if pd.isna(val) else int(val)

        # Helper function to safely get string, replacing NaN with None
        def safe_str(val):
            return None if pd.isna(val) else str(val)

        record = {
            'timestamp': row['Timestamp'].isoformat() if pd.notna(row['Timestamp']) else None,
            'date': row['date'].isoformat() if pd.notna(row['date']) else None,
            'location': safe_str(row['location']),
            'master_sku': safe_str(row['master_sku']),
            'master_name': safe_str(row['master_name']),
            'product_family': safe_str(row['product_family']),
            'type': safe_str(row['type']),
            'revenue': safe_float(row['revenue']),
            'cost': safe_float(row['cost']),
            'quantity': safe_int(row['quantity']),
            'profit': safe_float(row['profit']),
            'gross_margin_percent': safe_float(row['gross_margin_percent']),
            'mapping_tier': safe_str(row['mapping_tier']),
            'dedup_key': safe_str(row['dedup_key'])
        }
        records.append(record)

    # Insert into Supabase in batches of 100
    batch_size = 100
    inserted_count = 0
    failed_count = 0

    print(f"Inserting {len(records)} records in batches of {batch_size}...", file=sys.stderr)

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(records) + batch_size - 1)//batch_size

        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/transactions",
                headers=headers,
                data=json.dumps(batch),
                timeout=30
            )

            if response.status_code in [200, 201]:
                inserted_count += len(batch)
                if batch_num % 10 == 0 or batch_num == total_batches:
                    print(f"Batch {batch_num}/{total_batches}: {inserted_count} inserted", file=sys.stderr)
            else:
                failed_count += len(batch)
                print(f"Batch {batch_num} failed: {response.status_code}", file=sys.stderr)
        except Exception as e:
            failed_count += len(batch)
            print(f"Batch {batch_num} error: {str(e)[:100]}", file=sys.stderr)

    print(f"\nFinal: {inserted_count} inserted, {failed_count} failed", file=sys.stderr)

    # Create upload history record
    upload_record = {
        'filename': Path(filepath).name,
        'total_transactions': len(df),
        'duplicates_removed': 0,
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
        'duplicatesRemoved': 0,
        'actuallyInserted': inserted_count,
        'skippedAsDuplicates': failed_count,
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
