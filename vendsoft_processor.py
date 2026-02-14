"""
VendSoft Transaction Processor
Single Source of Truth for Smart Vending ATX Dashboard

Features:
- Three-tier product mapping (Direct → Product_Family → Unmapped)
- Composite key deduplication
- Location cleanup and standardization
- Unmapped product reporting
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re


class VendSoftProcessor:
    """Process VendSoft transaction logs with enhanced mapping and deduplication."""

    def __init__(self, transaction_log_path, sku_mapping_path, location_mapping_path):
        """
        Initialize VendSoft processor.

        Args:
            transaction_log_path: Path to VendSoft/USAT transaction log Excel file
            sku_mapping_path: Path to cleaned SKU mapping Excel file
            location_mapping_path: Path to location mapping CSV file
        """
        self.transaction_log_path = Path(transaction_log_path)
        self.sku_mapping_path = Path(sku_mapping_path)
        self.location_mapping_path = Path(location_mapping_path)

        # Load mapping files
        self._load_mappings()

        # Statistics tracking
        self.stats = {
            'raw_transactions': 0,
            'duplicates_removed': 0,
            'direct_mapped': 0,
            'family_mapped': 0,
            'unmapped': 0,
            'total_revenue': 0,
            'unmapped_revenue': 0
        }

    def _load_mappings(self):
        """Load all mapping files into memory."""
        # Load location mapping
        location_df = pd.read_csv(self.location_mapping_path)
        self.location_map = dict(zip(location_df['raw_name'], location_df['display_name']))

        # Load SKU mapping with cost data
        sku_df = pd.read_excel(self.sku_mapping_path)

        # Create direct product name mappings (Tier 1)
        # Map all four POS name columns to Master_SKU
        self.direct_mapping = {}

        for _, row in sku_df.iterrows():
            master_sku = row['Master_SKU']
            # Cantaloupe/USAT names
            if pd.notna(row.get('Cantaloupe_Name')):
                self.direct_mapping[row['Cantaloupe_Name']] = master_sku
            # Master names
            if pd.notna(row.get('Master_Name')):
                self.direct_mapping[row['Master_Name']] = master_sku
            # Haha AI names
            if pd.notna(row.get('Haha_AI_Name')):
                self.direct_mapping[row['Haha_AI_Name']] = master_sku
            # Nayax names
            if pd.notna(row.get('Nayax_Name')):
                self.direct_mapping[row['Nayax_Name']] = master_sku

        # Create SKU detail mappings
        self.sku_details = {}
        for _, row in sku_df.iterrows():
            master_sku = row['Master_SKU']
            self.sku_details[master_sku] = {
                'Master_Name': row.get('Master_Name', ''),
                'Product_Family': row.get('Product_Family', ''),
                'Type': row.get('Type', ''),
                'Cost': self._parse_cost(row.get('Cost', 0))
            }

        # Create Product_Family mapping (Tier 2)
        # Map family name to average cost of all products in that family
        self.family_mapping = {}
        family_groups = sku_df.groupby('Product_Family')

        for family, group in family_groups:
            if pd.notna(family):
                costs = [self._parse_cost(cost) for cost in group['Cost']]
                valid_costs = [c for c in costs if c > 0]
                avg_cost = np.mean(valid_costs) if valid_costs else 0

                self.family_mapping[family] = {
                    'avg_cost': round(avg_cost, 2),
                    'type': group['Type'].mode()[0] if len(group['Type'].mode()) > 0 else 'Unknown'
                }

    def _parse_cost(self, cost_value):
        """Parse cost value from string or numeric format."""
        if pd.isna(cost_value):
            return 0.0
        if isinstance(cost_value, (int, float)):
            return float(cost_value)
        # Remove $ and commas, convert to float
        cost_str = str(cost_value).replace('$', '').replace(',', '').strip()
        try:
            return float(cost_str)
        except ValueError:
            return 0.0

    def _create_dedup_key(self, row):
        """
        Create composite deduplication key.
        Format: {timestamp_normalized}_{machine_id}_{product_normalized}_{total_rounded}
        """
        # Normalize timestamp to minute precision
        timestamp = pd.to_datetime(row['Timestamp'], errors='coerce')
        if pd.isna(timestamp):
            ts_str = 'unknown'
        else:
            ts_str = timestamp.strftime('%Y-%m-%dT%H:%M')

        # Extract machine ID
        machine = str(row.get('Machine', '')).strip()
        # Extract [ID] if present, otherwise use full string
        machine_match = re.search(r'\[(\d+)\]', machine)
        machine_id = machine_match.group(1) if machine_match else re.sub(r'[^a-z0-9]', '', machine.lower())

        # Normalize product name (lowercase, remove spaces/special chars)
        product = re.sub(r'[^a-z0-9]', '', str(row.get('Product', '')).lower())

        # Round total to 2 decimal places
        total = round(float(row.get('Total', 0)), 2)

        return f"{ts_str}_{machine_id}_{product}_{total}"

    def _clean_location(self, location, machine):
        """
        Clean and standardize location names.

        Args:
            location: Raw location string
            machine: Raw machine string (may contain [ID] prefix)

        Returns:
            Cleaned location display name
        """
        # Try location mapping first
        location_str = str(location).strip()
        if location_str in self.location_map:
            return self.location_map[location_str]

        # Try machine mapping
        machine_str = str(machine).strip()
        if machine_str in self.location_map:
            return self.location_map[machine_str]

        # Fallback: Apply cleanup rules
        # Remove [ID] prefix
        cleaned = re.sub(r'^\[\d+\]\s*', '', machine_str)
        # Remove trailing 4-digit numbers (machine IDs)
        cleaned = re.sub(r'\s*\d{4}$', '', cleaned)

        return cleaned if cleaned else location_str

    def _map_product(self, product_name):
        """
        Three-tier product mapping.

        Tier 1 (Direct): Match to Cantaloupe_Name, Master_Name, Haha_AI_Name, or Nayax_Name
        Tier 2 (Family): Match to Product_Family and use average family cost
        Tier 3 (Unmapped): No match, assign UNMAPPED with $0 cost

        Args:
            product_name: Product name from transaction log

        Returns:
            dict with keys: Master_SKU, Master_Name, Product_Family, Type, Cost, mapping_tier
        """
        product_str = str(product_name).strip()

        # Tier 1: Direct mapping
        if product_str in self.direct_mapping:
            master_sku = self.direct_mapping[product_str]
            details = self.sku_details.get(master_sku, {})
            self.stats['direct_mapped'] += 1
            return {
                'Master_SKU': master_sku,
                'Master_Name': details.get('Master_Name', product_str),
                'Product_Family': details.get('Product_Family', ''),
                'Type': details.get('Type', ''),
                'Cost': details.get('Cost', 0),
                'mapping_tier': 'direct'
            }

        # Tier 2: Family mapping
        if product_str in self.family_mapping:
            family_details = self.family_mapping[product_str]
            self.stats['family_mapped'] += 1
            return {
                'Master_SKU': f'FAMILY_{product_str.upper().replace(" ", "_")}',
                'Master_Name': product_str,
                'Product_Family': product_str,
                'Type': family_details.get('type', 'Unknown'),
                'Cost': family_details['avg_cost'],
                'mapping_tier': 'family'
            }

        # Tier 3: Unmapped
        self.stats['unmapped'] += 1
        return {
            'Master_SKU': 'UNMAPPED',
            'Master_Name': product_str,
            'Product_Family': 'Unmapped',
            'Type': 'Unknown',
            'Cost': 0.0,
            'mapping_tier': 'unmapped'
        }

    def process_transactions(self, date_filter=None):
        """
        Main processing pipeline.

        Args:
            date_filter: Optional tuple (start_date, end_date) to filter transactions

        Returns:
            DataFrame with processed transactions
        """
        print(f"Loading VendSoft transaction log: {self.transaction_log_path.name}")

        # Load transaction log (skip first 3 rows: title, date range, and header)
        raw_df = pd.read_excel(self.transaction_log_path, header=None)
        df = raw_df.iloc[3:].copy()  # Skip rows 0, 1, 2 (title, date range, header)
        df.columns = ['Timestamp', 'Location', 'Machine', 'Product', 'Slot', 'Price', 'Quantity', 'Total', 'CC']
        df = df.reset_index(drop=True)  # Reset index after slicing

        self.stats['raw_transactions'] = len(df)

        # Parse dates
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['date'] = df['Timestamp'].dt.date

        # Apply date filter if provided
        if date_filter:
            start_date, end_date = date_filter
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # Deduplication: Create composite key
        print("Creating deduplication keys...")
        df['dedup_key'] = df.apply(self._create_dedup_key, axis=1)

        # Remove duplicates (keep first occurrence)
        before_dedup = len(df)
        df = df.drop_duplicates(subset='dedup_key', keep='first')
        after_dedup = len(df)
        self.stats['duplicates_removed'] = before_dedup - after_dedup

        print(f"  Removed {self.stats['duplicates_removed']} duplicate transactions")

        # Location cleanup
        print("Cleaning location names...")
        df['location'] = df.apply(lambda row: self._clean_location(row['Location'], row['Machine']), axis=1)

        # Product mapping (three-tier)
        print("Mapping products (3-tier system)...")
        mapping_results = df['Product'].apply(self._map_product)

        df['Master_SKU'] = mapping_results.apply(lambda x: x['Master_SKU'])
        df['Master_Name'] = mapping_results.apply(lambda x: x['Master_Name'])
        df['Product_Family'] = mapping_results.apply(lambda x: x['Product_Family'])
        df['Type'] = mapping_results.apply(lambda x: x['Type'])
        df['cost'] = mapping_results.apply(lambda x: x['Cost'])
        df['mapping_tier'] = mapping_results.apply(lambda x: x['mapping_tier'])

        # Parse financial columns
        df['revenue'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1)

        # Calculate profit and margin
        df['profit'] = (df['revenue'] - (df['cost'] * df['quantity'])).round(2)
        df['gross_margin_percent'] = df.apply(
            lambda row: round((row['profit'] / row['revenue']) * 100, 1) if row['revenue'] > 0 else 0,
            axis=1
        )

        # Update statistics
        self.stats['total_revenue'] = df['revenue'].sum()
        self.stats['unmapped_revenue'] = df[df['mapping_tier'] == 'unmapped']['revenue'].sum()

        # Select and order final columns
        output_df = df[[
            'date', 'location', 'Master_SKU', 'Master_Name', 'Product_Family', 'Type',
            'revenue', 'cost', 'quantity', 'profit', 'gross_margin_percent', 'mapping_tier'
        ]].copy()

        # Sort by date
        output_df = output_df.sort_values('date')

        print(f"\n  Direct mappings: {self.stats['direct_mapped']:,}")
        print(f"  Family mappings: {self.stats['family_mapped']:,}")
        print(f"  Unmapped: {self.stats['unmapped']:,}")
        print(f"  Mapping coverage: {((self.stats['direct_mapped'] + self.stats['family_mapped']) / len(output_df) * 100):.1f}%")

        return output_df

    def generate_unmapped_report(self, df):
        """
        Generate report of unmapped products.

        Args:
            df: Processed transactions DataFrame

        Returns:
            DataFrame with unmapped product summary
        """
        unmapped = df[df['mapping_tier'] == 'unmapped'].copy()

        if len(unmapped) == 0:
            return pd.DataFrame()

        # Aggregate by product
        report = unmapped.groupby('Master_Name').agg({
            'revenue': ['sum', 'count'],
            'date': ['min', 'max']
        }).reset_index()

        report.columns = ['product_name', 'total_revenue', 'transaction_count', 'first_seen', 'last_seen']
        report['revenue_percent'] = (report['total_revenue'] / self.stats['total_revenue'] * 100).round(2)

        # Sort by revenue (descending)
        report = report.sort_values('total_revenue', ascending=False)

        return report

    def print_summary(self):
        """Print processing summary statistics."""
        print("\n" + "="*60)
        print("VendSoft Processing Summary")
        print("="*60)
        print(f"Raw transactions: {self.stats['raw_transactions']:,}")
        print(f"Duplicates removed: {self.stats['duplicates_removed']:,}")
        print(f"Final transactions: {self.stats['raw_transactions'] - self.stats['duplicates_removed']:,}")
        print(f"\nMapping Statistics:")
        print(f"  Direct mapped: {self.stats['direct_mapped']:,}")
        print(f"  Family mapped: {self.stats['family_mapped']:,}")
        print(f"  Unmapped: {self.stats['unmapped']:,}")
        print(f"\nRevenue Statistics:")
        print(f"  Total revenue: ${self.stats['total_revenue']:,.2f}")
        print(f"  Unmapped revenue: ${self.stats['unmapped_revenue']:,.2f} ({self.stats['unmapped_revenue']/self.stats['total_revenue']*100:.1f}%)")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Example usage
    processor = VendSoftProcessor(
        transaction_log_path='data/vendsoft/usat-transaction-log.xlsx',
        sku_mapping_path='data/vendsoft/sku-mapping-cleaned.xlsx',
        location_mapping_path='location_mapping.csv'
    )

    # Process transactions
    transactions = processor.process_transactions()

    # Generate unmapped report
    unmapped_report = processor.generate_unmapped_report(transactions)

    # Print summary
    processor.print_summary()

    # Save outputs
    transactions.to_csv('data/processed/master_dashboard_data.csv', index=False)
    if len(unmapped_report) > 0:
        unmapped_report.to_csv('data/processed/unmapped_products_report.csv', index=False)
