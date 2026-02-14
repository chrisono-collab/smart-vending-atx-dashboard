"""
Revenue Validation Script

Validates VendSoft processing against expected metrics and data quality checks.
"""

import pandas as pd
from pathlib import Path
import sys


def validate_vendsoft_data():
    """Validate VendSoft processed data"""
    print("="*60)
    print("VENDSOFT DATA VALIDATION")
    print("="*60 + "\n")

    # Check if processed data exists
    csv_path = Path('data/processed/master_dashboard_data.csv')
    if not csv_path.exists():
        print("❌ ERROR: master_dashboard_data.csv not found")
        print("   Run process_data.py first to generate the data")
        return False

    # Load data
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df):,} transactions from {csv_path.name}\n")

    # Validation checks
    all_passed = True

    # Check 1: Schema validation (12 columns)
    print("1. Schema Validation")
    expected_columns = [
        'date', 'location', 'Master_SKU', 'Master_Name', 'Product_Family', 'Type',
        'revenue', 'cost', 'quantity', 'profit', 'gross_margin_percent', 'mapping_tier'
    ]
    if list(df.columns) == expected_columns:
        print("   ✓ Schema matches expected 12-column format")
    else:
        print(f"   ❌ Schema mismatch")
        print(f"      Expected: {expected_columns}")
        print(f"      Got: {list(df.columns)}")
        all_passed = False

    # Check 2: Date range
    print("\n2. Date Range Validation")
    df['date'] = pd.to_datetime(df['date'])
    date_min = df['date'].min()
    date_max = df['date'].max()
    print(f"   Date range: {date_min.date()} to {date_max.date()}")

    # Check for January 2026
    jan_2026 = df[(df['date'] >= '2026-01-01') & (df['date'] <= '2026-01-31')]
    if len(jan_2026) > 0:
        print(f"   ✓ Contains January 2026 data: {len(jan_2026):,} transactions")
    else:
        print(f"   ⚠️  No January 2026 data found")

    # Check 3: Revenue totals
    print("\n3. Revenue Validation")
    total_revenue = df['revenue'].sum()
    total_profit = df['profit'].sum()
    avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    print(f"   Total Revenue: ${total_revenue:,.2f}")
    print(f"   Total Profit: ${total_profit:,.2f}")
    print(f"   Average Margin: {avg_margin:.1f}%")

    if total_revenue > 0:
        print("   ✓ Revenue calculations complete")
    else:
        print("   ❌ Zero revenue - data issue")
        all_passed = False

    # Check 4: Mapping coverage
    print("\n4. Mapping Coverage Validation")
    total_txns = len(df)
    direct_mapped = len(df[df['mapping_tier'] == 'direct'])
    family_mapped = len(df[df['mapping_tier'] == 'family'])
    unmapped = len(df[df['mapping_tier'] == 'unmapped'])

    mapping_coverage = ((direct_mapped + family_mapped) / total_txns * 100) if total_txns > 0 else 0

    print(f"   Direct mappings: {direct_mapped:,} ({direct_mapped/total_txns*100:.1f}%)")
    print(f"   Family mappings: {family_mapped:,} ({family_mapped/total_txns*100:.1f}%)")
    print(f"   Unmapped: {unmapped:,} ({unmapped/total_txns*100:.1f}%)")
    print(f"   Total coverage: {mapping_coverage:.1f}%")

    if mapping_coverage >= 85:
        print(f"   ✓ Mapping coverage ≥85% (target met)")
    else:
        print(f"   ⚠️  Mapping coverage <85% (target: ≥85%)")

    # Check 5: Unmapped revenue
    print("\n5. Unmapped Revenue Validation")
    unmapped_revenue = df[df['mapping_tier'] == 'unmapped']['revenue'].sum()
    unmapped_percent = (unmapped_revenue / total_revenue * 100) if total_revenue > 0 else 0
    print(f"   Unmapped revenue: ${unmapped_revenue:,.2f} ({unmapped_percent:.1f}%)")

    if unmapped_percent < 15:
        print(f"   ✓ Unmapped revenue <15% (target met)")
    else:
        print(f"   ⚠️  Unmapped revenue ≥15% (target: <15%)")

    # Check 6: Location mapping
    print("\n6. Location Mapping Validation")
    unique_locations = df['location'].nunique()
    print(f"   Unique locations: {unique_locations}")

    # Check for locations with [ID] brackets (should be cleaned)
    locations_with_brackets = df[df['location'].str.contains(r'\[\d+\]', regex=True, na=False)]
    if len(locations_with_brackets) == 0:
        print("   ✓ All locations cleaned (no [ID] brackets)")
    else:
        print(f"   ⚠️  {len(locations_with_brackets)} transactions with uncleaned location names")
        all_passed = False

    # Check 7: Type field population
    print("\n7. Product Type Validation")
    unknown_types = len(df[df['Type'] == 'Unknown'])
    unknown_percent = (unknown_types / total_txns * 100) if total_txns > 0 else 0
    print(f"   Transactions with Type='Unknown': {unknown_types:,} ({unknown_percent:.1f}%)")

    if unknown_percent < 5:
        print("   ✓ Type field well-populated (<5% unknown)")
    else:
        print(f"   ⚠️  High unknown type percentage (>5%)")

    # Check 8: Top unmapped products
    if unmapped > 0:
        print("\n8. Top Unmapped Products")
        unmapped_products = df[df['mapping_tier'] == 'unmapped'].groupby('Master_Name').agg({
            'revenue': 'sum',
            'quantity': 'sum'
        }).sort_values('revenue', ascending=False).head(5)

        print("   Top 5 by revenue:")
        for idx, (product, row) in enumerate(unmapped_products.iterrows(), 1):
            print(f"   {idx}. {product}: ${row['revenue']:,.2f} ({row['quantity']} units)")

    # Check 9: Data quality checks
    print("\n9. Data Quality Checks")
    missing_cost = len(df[df['cost'] == 0])
    negative_profit = len(df[df['profit'] < 0])
    zero_revenue = len(df[df['revenue'] == 0])

    print(f"   Products with missing/zero cost: {missing_cost:,} ({missing_cost/total_txns*100:.1f}%)")
    print(f"   Transactions with negative profit: {negative_profit:,}")
    print(f"   Transactions with zero revenue: {zero_revenue:,}")

    if zero_revenue == 0:
        print("   ✓ No zero-revenue transactions")
    else:
        print(f"   ⚠️  {zero_revenue} zero-revenue transactions found")

    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("VALIDATION RESULT: ✓ ALL CRITICAL CHECKS PASSED")
    else:
        print("VALIDATION RESULT: ⚠️  SOME CHECKS FAILED (see above)")
    print("="*60 + "\n")

    return all_passed


if __name__ == '__main__':
    success = validate_vendsoft_data()
    sys.exit(0 if success else 1)
