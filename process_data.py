import pandas as pd
import re

# Load location mapping
location_map_df = pd.read_csv('location_mapping.csv')
location_map = dict(zip(location_map_df['raw_name'], location_map_df['display_name']))

# Load SKU map with cost data
sku_map = pd.read_csv('Product SKU Map.csv').drop_duplicates(subset=['Master_SKU'])
sku_name_map = dict(zip(sku_map['Master_SKU'], sku_map['Master_Name']))
sku_family_map = dict(zip(sku_map['Master_SKU'], sku_map['Product_Family']))

# Clean cost column - remove $ and convert to numeric
if 'Cost' in sku_map.columns:
    sku_map['Cost_Clean'] = sku_map['Cost'].astype(str).str.replace('$', '').str.replace(',', '')
    sku_cost_map = dict(zip(sku_map['Master_SKU'], pd.to_numeric(sku_map['Cost_Clean'], errors='coerce').fillna(0)))
else:
    sku_cost_map = {sku: 0 for sku in sku_map['Master_SKU']}

# Create mapping rules for all three sources
haha_map = sku_map.dropna(subset=['Haha_AI_Name']).set_index('Haha_AI_Name')['Master_SKU'].to_dict()
usat_map = sku_map.dropna(subset=['Cantaloupe_Name']).set_index('Cantaloupe_Name')['Master_SKU'].to_dict()
nayax_map = sku_map.dropna(subset=['Nayax_Name']).set_index('Nayax_Name')['Master_SKU'].to_dict()

# Initialize unmapped products tracking
unmapped_products = []

# === PROCESS HAHA DATA ===
haha_sales = pd.read_excel('Product Sales Details_2026-02-02 20_55_04_4313.xlsx')
haha_sales['date'] = pd.to_datetime(haha_sales['Payment time']).dt.date
haha_sales['location'] = haha_sales['Device number'].map(location_map).fillna(haha_sales['Device number'])
haha_sales['Master_SKU'] = haha_sales['Product'].map(haha_map)
haha_sales['revenue'] = haha_sales['Amount Received']
haha_sales['quantity'] = haha_sales['Sales volume']

# Track unmapped HAHA products
haha_unmapped = haha_sales[(pd.to_datetime(haha_sales['Payment time']).dt.year == 2026) &
                            (pd.to_datetime(haha_sales['Payment time']).dt.month == 1) &
                            (haha_sales['Master_SKU'].isna())]
if len(haha_unmapped) > 0:
    unmapped_summary = haha_unmapped.groupby('Product').agg({
        'Amount Received': ['sum', 'count'],
        'date': ['min', 'max']
    }).reset_index()
    unmapped_summary.columns = ['raw_product_name', 'total_revenue', 'transaction_count', 'first_seen_date', 'last_seen_date']
    unmapped_summary['pos_system'] = 'Haha AI'
    unmapped_products.append(unmapped_summary)

# Filter to January 2026 and keep only mapped products
haha_sales = haha_sales[(pd.to_datetime(haha_sales['Payment time']).dt.year == 2026) &
                        (pd.to_datetime(haha_sales['Payment time']).dt.month == 1) &
                        (haha_sales['Master_SKU'].notna())]

haha_transactions = haha_sales[['date', 'location', 'Master_SKU', 'revenue', 'quantity']].copy()

# === PROCESS CANTALOUPE/USAT DATA ===
usat_raw = pd.read_excel('usat-transaction-log_(1).xlsx', header=None)
usat_sales = usat_raw.iloc[2:].copy()
usat_sales.columns = ['Timestamp', 'Location', 'Machine', 'Product', 'Slot', 'Price', 'Quantity', 'Total', 'CC']
usat_sales['date'] = pd.to_datetime(usat_sales['Timestamp'], errors='coerce').dt.date
usat_sales['location'] = usat_sales['Location'].map(location_map).fillna(usat_sales['Location'])
usat_sales['Master_SKU'] = usat_sales['Product'].map(usat_map)
usat_sales['revenue'] = pd.to_numeric(usat_sales['Total'], errors='coerce')
usat_sales['quantity'] = pd.to_numeric(usat_sales['Quantity'], errors='coerce').fillna(1)

# Track unmapped Cantaloupe products
usat_unmapped = usat_sales[(pd.to_datetime(usat_sales['Timestamp'], errors='coerce').dt.year == 2026) &
                            (pd.to_datetime(usat_sales['Timestamp'], errors='coerce').dt.month == 1) &
                            (usat_sales['Master_SKU'].isna())]
if len(usat_unmapped) > 0:
    unmapped_summary = usat_unmapped.groupby('Product').agg({
        'revenue': ['sum', 'count'],
        'date': ['min', 'max']
    }).reset_index()
    unmapped_summary.columns = ['raw_product_name', 'total_revenue', 'transaction_count', 'first_seen_date', 'last_seen_date']
    unmapped_summary['pos_system'] = 'Cantaloupe'
    unmapped_products.append(unmapped_summary)

# Filter to January 2026 and keep only mapped products
usat_sales = usat_sales[(pd.to_datetime(usat_sales['Timestamp'], errors='coerce').dt.year == 2026) &
                        (pd.to_datetime(usat_sales['Timestamp'], errors='coerce').dt.month == 1) &
                        (usat_sales['Master_SKU'].notna())]

usat_transactions = usat_sales[['date', 'location', 'Master_SKU', 'revenue', 'quantity']].copy()

# === PROCESS NAYAX DATA ===
def extract_nayax_product(val):
    if pd.isna(val):
        return None
    match = re.match(r'^(.+?)\s*\(', str(val))
    if match:
        return match.group(1).strip()
    return str(val).strip()

nayax_raw = pd.read_excel('../DynamicTransactionsMonitorMega_2026-02-04T044619.xlsx', engine='calamine', header=1)
nayax_sales = nayax_raw[nayax_raw['Currency  '] != 'Total'].copy()
nayax_sales['date'] = pd.to_datetime(nayax_sales['Machine Authorization Time  '], errors='coerce').dt.date
nayax_sales['location'] = nayax_sales['Machine Name'].map(location_map).fillna(nayax_sales['Machine Name'])
nayax_sales['Product'] = nayax_sales['Product Selection Info'].apply(extract_nayax_product)
nayax_sales['Master_SKU'] = nayax_sales['Product'].map(nayax_map)
nayax_sales['revenue'] = pd.to_numeric(nayax_sales['Settlement Value (Vend Price)  '], errors='coerce')
nayax_sales['quantity'] = 1  # Nayax doesn't have quantity, default to 1

# Track unmapped Nayax products
nayax_unmapped = nayax_sales[(pd.to_datetime(nayax_sales['Machine Authorization Time  '], errors='coerce').dt.year == 2026) &
                              (pd.to_datetime(nayax_sales['Machine Authorization Time  '], errors='coerce').dt.month == 1) &
                              (nayax_sales['Master_SKU'].isna())]
if len(nayax_unmapped) > 0:
    unmapped_summary = nayax_unmapped.groupby('Product').agg({
        'revenue': ['sum', 'count'],
        'date': ['min', 'max']
    }).reset_index()
    unmapped_summary.columns = ['raw_product_name', 'total_revenue', 'transaction_count', 'first_seen_date', 'last_seen_date']
    unmapped_summary['pos_system'] = 'Nayax'
    unmapped_products.append(unmapped_summary)

# Filter to January 2026 and keep only mapped products
nayax_sales = nayax_sales[(pd.to_datetime(nayax_sales['Machine Authorization Time  '], errors='coerce').dt.year == 2026) &
                          (pd.to_datetime(nayax_sales['Machine Authorization Time  '], errors='coerce').dt.month == 1) &
                          (nayax_sales['Master_SKU'].notna())]

nayax_transactions = nayax_sales[['date', 'location', 'Master_SKU', 'revenue', 'quantity']].copy()

# === COMBINE ALL TRANSACTIONS ===
all_transactions = pd.concat([haha_transactions, usat_transactions, nayax_transactions], ignore_index=True)

# Add Master_Name, Product_Family, and Cost
all_transactions['Master_Name'] = all_transactions['Master_SKU'].map(sku_name_map)
all_transactions['Product_Family'] = all_transactions['Master_SKU'].map(sku_family_map)
all_transactions['cost'] = all_transactions['Master_SKU'].map(sku_cost_map).fillna(0)

# Calculate profit and gross margin
all_transactions['profit'] = (all_transactions['revenue'] - (all_transactions['cost'] * all_transactions['quantity'])).round(2)
all_transactions['gross_margin_percent'] = all_transactions.apply(
    lambda row: round((row['profit'] / row['revenue']) * 100, 1) if row['revenue'] > 0 else 0,
    axis=1
)

# Reorder columns
all_transactions = all_transactions[['date', 'location', 'Master_SKU', 'Master_Name', 'Product_Family', 'revenue', 'cost', 'quantity', 'profit', 'gross_margin_percent']]

# Sort by date
all_transactions = all_transactions.sort_values('date')

# Save to CSV
all_transactions.to_csv('master_dashboard_data.csv', index=False)

# === CREATE UNMAPPED PRODUCTS REPORT ===
if unmapped_products:
    unmapped_report = pd.concat(unmapped_products, ignore_index=True)
    unmapped_report = unmapped_report[['pos_system', 'raw_product_name', 'transaction_count', 'total_revenue', 'first_seen_date', 'last_seen_date']]
    unmapped_report = unmapped_report.sort_values('transaction_count', ascending=False)
    unmapped_report.to_csv('unmapped_products_report.csv', index=False)
    unmapped_count = len(unmapped_report)
else:
    unmapped_count = 0

# === PRINT SUMMARY ===
total_revenue = all_transactions['revenue'].sum()
total_profit = all_transactions['profit'].sum()
avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
total_transactions = len(all_transactions)
unique_locations = all_transactions['location'].nunique()
unique_skus = all_transactions['Master_SKU'].nunique()
missing_cost = len(all_transactions[all_transactions['cost'] == 0])
date_range = f"{all_transactions['date'].min()} to {all_transactions['date'].max()}"

print(f"✓ Success! Transaction-level dashboard data generated.")
print(f"\n  Date Range: {date_range}")
print(f"  Total Revenue: ${total_revenue:,.2f}")
print(f"  Total Profit: ${total_profit:,.2f}")
print(f"  Average Margin: {avg_margin:.1f}%")
print(f"  Transactions: {total_transactions:,}")
print(f"  Unique Locations: {unique_locations}")
print(f"  Active SKUs: {unique_skus}")
print(f"  Products with missing cost: {missing_cost}")
print(f"  Unmapped products: {unmapped_count}" + (" (see unmapped_products_report.csv)" if unmapped_count > 0 else ""))
print(f"\n  Output: master_dashboard_data.csv")
