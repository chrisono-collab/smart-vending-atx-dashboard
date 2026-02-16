#!/usr/bin/env python3
"""
Check what's actually in the database
"""

import requests
from process_supabase_upload import SUPABASE_URL, headers

def check_totals():
    # Get all transactions
    print("Fetching all transactions from database...")

    all_transactions = []
    offset = 0
    limit = 1000

    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/transactions?select=date,revenue&order=date.asc&limit={limit}&offset={offset}",
            headers=headers
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()
        if not data:
            break

        all_transactions.extend(data)
        offset += limit

        if len(data) < limit:
            break

    print(f"\nTotal records in database: {len(all_transactions)}")

    # Group by month
    from collections import defaultdict
    monthly_totals = defaultdict(float)

    for tx in all_transactions:
        date = tx['date']
        revenue = float(tx['revenue'])

        # Extract year-month
        if date:
            year_month = date[:7]  # "2026-01" or "2026-02"
            monthly_totals[year_month] += revenue

    print("\nMonthly totals:")
    print("-" * 40)
    for month in sorted(monthly_totals.keys()):
        print(f"{month}: ${monthly_totals[month]:,.2f}")
    print("-" * 40)
    print(f"TOTAL: ${sum(monthly_totals.values()):,.2f}")

    # Count transactions per month
    monthly_counts = defaultdict(int)
    for tx in all_transactions:
        date = tx['date']
        if date:
            year_month = date[:7]
            monthly_counts[year_month] += 1

    print("\nTransaction counts:")
    print("-" * 40)
    for month in sorted(monthly_counts.keys()):
        print(f"{month}: {monthly_counts[month]} transactions")

if __name__ == '__main__':
    check_totals()
