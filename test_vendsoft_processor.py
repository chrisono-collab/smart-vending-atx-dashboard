"""
Unit Tests for VendSoft Processor

Tests deduplication, product mapping (3-tier), and location cleanup.
"""

import unittest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from vendsoft_processor import VendSoftProcessor


class TestVendSoftProcessor(unittest.TestCase):
    """Test cases for VendSoftProcessor"""

    @classmethod
    def setUpClass(cls):
        """Create test data files"""
        cls.test_dir = Path(tempfile.mkdtemp())

        # Create test SKU mapping
        sku_data = {
            'Master_SKU': ['SKU001', 'SKU002', 'SKU003', 'SKU004'],
            'Master_Name': ['Coca Cola', 'Pepsi', 'Snickers', 'Legendary Bar'],
            'Product_Family': ['Beverage', 'Beverage', 'Candy', 'Legendary Variety'],
            'Type': ['Beverage - Soda', 'Beverage - Soda', 'Snack - Candy', 'Snack - Energy Bar'],
            'Cantaloupe_Name': ['Coca Cola 16.9oz', 'Pepsi 20oz', pd.NA, pd.NA],
            'Haha_AI_Name': ['Coke', pd.NA, 'Snickers Bar', pd.NA],
            'Nayax_Name': [pd.NA, 'Pepsi Cola', pd.NA, pd.NA],
            'Cost': [0.50, 0.60, 0.75, 1.00],
        }
        sku_df = pd.DataFrame(sku_data)
        cls.sku_mapping_path = cls.test_dir / 'sku_mapping.xlsx'
        sku_df.to_excel(cls.sku_mapping_path, index=False)

        # Create test location mapping
        location_data = {
            'raw_name': ['[21] West Bank 3743', 'The Met'],
            'display_name': ['West Bank', 'The Met']
        }
        location_df = pd.DataFrame(location_data)
        cls.location_mapping_path = cls.test_dir / 'location_mapping.csv'
        location_df.to_csv(cls.location_mapping_path, index=False)

        # Create test transaction log
        txn_data = {
            'row': [0, 1, 2, 3, 4, 5, 6, 7, 8],
            'col1': ['', '', 'Timestamp', '2026-01-15 10:00:27', '2026-01-15 10:00:27', '2026-01-15 10:05:00', '2026-01-15 11:00:00', '2026-01-15 12:00:00', '2026-01-15 13:00:00'],
            'col2': ['', '', 'Location', 'West Bank 3743', 'West Bank 3743', 'The Met', 'The Met', 'Unknown Location', 'The Met'],
            'col3': ['', '', 'Machine', '[21] West Bank 3743', '[21] West Bank 3743', '[6] The Met', '[6] The Met', '[99] Unknown', '[6] The Met'],
            'col4': ['', '', 'Product', 'Coca Cola 16.9oz', 'Coca Cola 16.9oz', 'Pepsi 20oz', 'Legendary Variety', 'Unknown Product', 'Snickers Bar'],
            'col5': ['', '', 'Slot', '1', '1', '2', '3', '4', '5'],
            'col6': ['', '', 'Price', '2.50', '2.50', '2.75', '3.00', '1.50', '1.75'],
            'col7': ['', '', 'Quantity', '1', '1', '1', '1', '1', '1'],
            'col8': ['', '', 'Total', '2.50', '2.50', '2.75', '3.00', '1.50', '1.75'],
            'col9': ['', '', 'CC', 'xxxx', 'xxxx', 'xxxx', 'xxxx', 'xxxx', 'xxxx'],
        }
        txn_df = pd.DataFrame(txn_data)
        cls.transaction_log_path = cls.test_dir / 'transactions.xlsx'
        txn_df.to_excel(cls.transaction_log_path, index=False, header=False)

    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Initialize processor for each test"""
        self.processor = VendSoftProcessor(
            transaction_log_path=self.transaction_log_path,
            sku_mapping_path=self.sku_mapping_path,
            location_mapping_path=self.location_mapping_path
        )

    def test_deduplication(self):
        """Test that duplicate transactions are removed"""
        df = self.processor.process_transactions()

        # We have 2 identical Coca Cola transactions (rows 3 and 4)
        # After deduplication, should only have 1
        coca_cola_txns = df[df['Master_Name'] == 'Coca Cola']
        self.assertEqual(len(coca_cola_txns), 1, "Should have exactly 1 Coca Cola transaction after deduplication")

        # Total transactions should be 5 (6 raw - 1 duplicate)
        self.assertEqual(len(df), 5, "Should have 5 transactions after removing 1 duplicate")

        # Check stats
        self.assertEqual(self.processor.stats['duplicates_removed'], 1, "Should report 1 duplicate removed")

    def test_product_mapping_direct(self):
        """Test direct product mapping (Tier 1)"""
        df = self.processor.process_transactions()

        # Coca Cola 16.9oz should map to SKU001 via Cantaloupe_Name
        coca_cola = df[df['Master_Name'] == 'Coca Cola'].iloc[0]
        self.assertEqual(coca_cola['Master_SKU'], 'SKU001')
        self.assertEqual(coca_cola['mapping_tier'], 'direct')
        self.assertEqual(coca_cola['cost'], 0.50)
        self.assertEqual(coca_cola['Type'], 'Beverage - Soda')

        # Pepsi 20oz should map to SKU002 via Cantaloupe_Name
        pepsi = df[df['Master_Name'] == 'Pepsi'].iloc[0]
        self.assertEqual(pepsi['Master_SKU'], 'SKU002')
        self.assertEqual(pepsi['mapping_tier'], 'direct')
        self.assertEqual(pepsi['cost'], 0.60)

    def test_product_mapping_family(self):
        """Test family product mapping (Tier 2) - average cost"""
        df = self.processor.process_transactions()

        # "Legendary Variety" is a Product_Family, should use average cost
        legendary = df[df['Master_Name'] == 'Legendary Variety'].iloc[0]
        self.assertEqual(legendary['mapping_tier'], 'family')
        self.assertEqual(legendary['cost'], 1.00, "Should use family average cost ($1.00)")
        self.assertTrue(legendary['Master_SKU'].startswith('FAMILY_'))

    def test_product_mapping_unmapped(self):
        """Test unmapped products (Tier 3)"""
        df = self.processor.process_transactions()

        # "Unknown Product" should be unmapped
        unmapped = df[df['Master_Name'] == 'Unknown Product']
        self.assertEqual(len(unmapped), 1, "Should have 1 unmapped product")
        self.assertEqual(unmapped.iloc[0]['Master_SKU'], 'UNMAPPED')
        self.assertEqual(unmapped.iloc[0]['mapping_tier'], 'unmapped')
        self.assertEqual(unmapped.iloc[0]['cost'], 0.0)
        self.assertEqual(unmapped.iloc[0]['Type'], 'Unknown')

    def test_location_cleanup(self):
        """Test location name cleanup"""
        df = self.processor.process_transactions()

        # "[21] West Bank 3743" should be cleaned to "West Bank"
        west_bank = df[df['location'] == 'West Bank']
        self.assertGreater(len(west_bank), 0, "Should have West Bank transactions")

        # "[6] The Met" should be cleaned to "The Met"
        the_met = df[df['location'] == 'The Met']
        self.assertGreater(len(the_met), 0, "Should have The Met transactions")

        # No raw location names with [ID] should remain
        locations_with_brackets = df[df['location'].str.contains(r'\[\d+\]', regex=True)]
        self.assertEqual(len(locations_with_brackets), 0, "Should not have any locations with [ID] brackets")

    def test_unmapped_report(self):
        """Test unmapped product report generation"""
        df = self.processor.process_transactions()
        unmapped_report = self.processor.generate_unmapped_report(df)

        # Should have 1 unmapped product
        self.assertEqual(len(unmapped_report), 1, "Should have 1 unmapped product")

        # Check report structure
        self.assertIn('product_name', unmapped_report.columns)
        self.assertIn('total_revenue', unmapped_report.columns)
        self.assertIn('transaction_count', unmapped_report.columns)
        self.assertIn('revenue_percent', unmapped_report.columns)

        # Unknown Product should be in report
        self.assertEqual(unmapped_report.iloc[0]['product_name'], 'Unknown Product')
        self.assertEqual(unmapped_report.iloc[0]['total_revenue'], 1.50)

    def test_profit_calculation(self):
        """Test that profit is calculated correctly"""
        df = self.processor.process_transactions()

        # Coca Cola: revenue $2.50, cost $0.50, quantity 1 → profit = $2.00
        coca_cola = df[df['Master_Name'] == 'Coca Cola'].iloc[0]
        self.assertEqual(coca_cola['profit'], 2.00)

        # Pepsi: revenue $2.75, cost $0.60, quantity 1 → profit = $2.15
        pepsi = df[df['Master_Name'] == 'Pepsi'].iloc[0]
        self.assertEqual(pepsi['profit'], 2.15)

    def test_gross_margin_calculation(self):
        """Test that gross margin % is calculated correctly"""
        df = self.processor.process_transactions()

        # Coca Cola: profit $2.00 / revenue $2.50 = 80%
        coca_cola = df[df['Master_Name'] == 'Coca Cola'].iloc[0]
        self.assertEqual(coca_cola['gross_margin_percent'], 80.0)

        # Pepsi: profit $2.15 / revenue $2.75 = 78.2%
        pepsi = df[df['Master_Name'] == 'Pepsi'].iloc[0]
        self.assertAlmostEqual(pepsi['gross_margin_percent'], 78.2, places=1)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
