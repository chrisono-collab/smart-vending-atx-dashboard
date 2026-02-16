#!/usr/bin/env python3
"""
Local script to clear database and upload transactions
Usage: python upload_transactions_local.py <path-to-excel-file>

This script runs locally without serverless timeout constraints.
It will:
1. Delete all existing transactions
2. Process the Excel file
3. Insert all transactions into Supabase
"""

import sys
import os
from pathlib import Path

# Import the processing function
from process_supabase_upload import process_file, SUPABASE_URL, headers
import requests

def clear_database():
    """Delete all existing transactions from Supabase"""
    print("=" * 60)
    print("STEP 1: Clearing database")
    print("=" * 60)

    try:
        # First, get the count of existing transactions
        count_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/transactions?select=count",
            headers={**headers, "Prefer": "count=exact"}
        )

        if count_response.status_code == 200:
            # The count is in the Content-Range header
            content_range = count_response.headers.get('Content-Range', '')
            if content_range:
                existing_count = content_range.split('/')[-1]
                print(f"Found {existing_count} existing transactions")

        # Delete all records using a filter that matches everything
        print("Deleting all records...")
        delete_response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/transactions?timestamp=not.is.null",
            headers=headers,
            timeout=120  # Longer timeout for local execution
        )

        if delete_response.status_code in [200, 204]:
            print("✓ Successfully deleted all existing transactions")
            return True
        else:
            print(f"Warning: Delete returned status {delete_response.status_code}")
            print(f"Response: {delete_response.text[:500]}")

            # Try alternative delete method
            print("\nTrying alternative delete method...")
            delete_response2 = requests.delete(
                f"{SUPABASE_URL}/rest/v1/transactions?id=gte.0",
                headers=headers,
                timeout=120
            )

            if delete_response2.status_code in [200, 204]:
                print("✓ Successfully deleted with alternative method")
                return True
            else:
                print(f"⚠ Delete may have failed. Status: {delete_response2.status_code}")
                print("Continuing with upload anyway...")
                return False

    except Exception as e:
        print(f"⚠ Error deleting records: {e}")
        print("Continuing with upload anyway...")
        return False

def upload_transactions(filepath):
    """Process and upload transactions"""
    print("\n" + "=" * 60)
    print("STEP 2: Processing and uploading transactions")
    print("=" * 60)

    result = process_file(filepath)

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total Transactions:    {result['totalTransactions']}")
    print(f"Actually Inserted:     {result['actuallyInserted']}")
    print(f"Failed/Skipped:        {result['skippedAsDuplicates']}")
    print(f"Mapping Coverage:      {result['mappingCoverage']}%")
    print(f"Unmapped Revenue:      ${result['unmappedRevenue']:,.2f}")
    print(f"Total Revenue:         ${result['totalRevenue']:,.2f}")
    print(f"Total Profit:          ${result['totalProfit']:,.2f}")
    print("=" * 60)

    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_transactions_local.py <path-to-excel-file>")
        print("\nExample:")
        print('  python upload_transactions_local.py "/Users/chrisono/Downloads/usat-transaction-log.xlsx"')
        sys.exit(1)

    filepath = sys.argv[1]

    # Validate file exists
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Validate file type
    if not filepath.lower().endswith(('.xlsx', '.xls')):
        print("Error: File must be an Excel file (.xlsx or .xls)")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SMART VENDING ATX - LOCAL TRANSACTION UPLOAD")
    print("=" * 60)
    print(f"File: {filepath}")
    print(f"Target: {SUPABASE_URL}")
    print("=" * 60)

    # Step 1: Clear database
    clear_database()

    # Step 2: Upload transactions
    result = upload_transactions(filepath)

    # Check if upload was successful
    if result['actuallyInserted'] > 0:
        print("\n✓ Upload completed successfully!")
        print("\nRefresh your dashboard to see the updated data.")
    else:
        print("\n⚠ Upload completed but no records were inserted.")
        print("Check the output above for errors.")

    print()

if __name__ == '__main__':
    main()
