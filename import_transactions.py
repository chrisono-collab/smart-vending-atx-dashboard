#!/usr/bin/env python3
"""
Import transactions from POS exports into the database.
Handles Haha AI, Nayax, and Cantaloupe formats with deduplication.
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Database path
DB_PATH = Path(__file__).parent / "data" / "transactions.db"

# SKU mapping path
SKU_MAPPING_PATH = Path(__file__).parent / "data" / "sku_mapping.csv"


def get_db_connection():
    """Get database connection, creating tables if needed."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Create transactions table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            source_system TEXT NOT NULL,
            timestamp TEXT,
            machine_name TEXT,
            product_name_original TEXT,
            master_sku TEXT,
            master_name TEXT,
            product_family TEXT,
            quantity REAL,
            amount REAL,
            payment_method TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(transaction_id, source_system, product_name_original)
        )
    """)
    
    # Create index for faster lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_lookup 
        ON transactions(transaction_id, source_system)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_timestamp 
        ON transactions(timestamp)
    """)
    
    conn.commit()
    return conn


def load_sku_mapping() -> dict:
    """Load SKU mapping and create lookup dictionaries."""
    mapping = {
        "Haha_AI": {},
        "Nayax": {},
        "Cantaloupe": {},
    }
    
    if not SKU_MAPPING_PATH.exists():
        return mapping
    
    df = pd.read_csv(SKU_MAPPING_PATH, dtype=str).fillna("")
    
    for _, row in df.iterrows():
        master_sku = row.get("Master_SKU", "")
        master_name = row.get("Master_Name", "")
        product_family = row.get("Product_Family", "")
        
        # Build lookup for each POS system
        if row.get("Haha_AI_Name"):
            mapping["Haha_AI"][row["Haha_AI_Name"].lower().strip()] = {
                "master_sku": master_sku,
                "master_name": master_name,
                "product_family": product_family,
            }
        if row.get("Nayax_Name"):
            mapping["Nayax"][row["Nayax_Name"].lower().strip()] = {
                "master_sku": master_sku,
                "master_name": master_name,
                "product_family": product_family,
            }
        if row.get("Cantaloupe_Name"):
            mapping["Cantaloupe"][row["Cantaloupe_Name"].lower().strip()] = {
                "master_sku": master_sku,
                "master_name": master_name,
                "product_family": product_family,
            }
    
    return mapping


def _normalize_product_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def load_haha_product_sales_details() -> dict:
    """Load Haha AI Product Sales Details for per-item pricing/quantity."""
    data_dir = Path(__file__).parent / "data"
    uploads_dir = Path(__file__).parent / "uploads"
    candidates = (
        list(data_dir.glob("Product Sales Details*.xlsx"))
        + list(data_dir.glob("Product Sales Details*.csv"))
        + list(uploads_dir.glob("Product Sales Details*.xlsx"))
        + list(uploads_dir.glob("Product Sales Details*.csv"))
    )
    if not candidates:
        return {}

    path = candidates[0]
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        print(f"Error reading Product Sales Details: {e}")
        return {}

    cols = {c: str(c).lower().strip() for c in df.columns}
    product_col = next((c for c, lc in cols.items() if lc == "product"), None)
    order_col = next((c for c, lc in cols.items() if "order number" in lc), None)
    sales_col = next((c for c, lc in cols.items() if "sales volume" in lc), None)
    amount_col = next((c for c, lc in cols.items() if "amount received" in lc), None)

    if not all([product_col, order_col, sales_col, amount_col]):
        return {}

    df = df[[product_col, order_col, sales_col, amount_col]].copy()
    df[product_col] = df[product_col].astype(str)
    df[order_col] = df[order_col].astype(str)
    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)

    df["key"] = df[order_col].str.strip() + "||" + df[product_col].apply(_normalize_product_name)
    grouped = df.groupby("key", as_index=False).agg(
        Amount=(amount_col, "sum"),
        SalesVolume=(sales_col, "sum"),
    )
    return dict(zip(grouped["key"], zip(grouped["Amount"], grouped["SalesVolume"])))


def lookup_sku(product_name: str, source_system: str, mapping: dict) -> dict:
    """Look up SKU info for a product name."""
    if not product_name:
        return {"master_sku": "", "master_name": "", "product_family": ""}
    
    key = product_name.lower().strip()
    system_mapping = mapping.get(source_system, {})
    
    if key in system_mapping:
        return system_mapping[key]
    
    # Try partial match
    for mapped_name, info in system_mapping.items():
        if mapped_name in key or key in mapped_name:
            return info
    
    return {"master_sku": "", "master_name": product_name, "product_family": ""}


def parse_haha_ai_order_details(filepath: Path, mapping: dict, psd_map: dict | None = None) -> list[dict]:
    """Parse Haha AI Order details file."""
    transactions = []
    
    try:
        df = pd.read_excel(filepath, engine="openpyxl")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return transactions
    
    for _, row in df.iterrows():
        order_num = str(row.get("Order number", ""))
        if not order_num or order_num == "nan":
            continue
        
        # Product details contains comma-separated items
        product_details = str(row.get("Product details", ""))
        
        timestamp = row.get("Payment time") or row.get("Creation time")
        if pd.notna(timestamp):
            timestamp = str(timestamp)
        else:
            timestamp = ""
        
        amount_received = row.get("Amount Received", 0)
        if pd.isna(amount_received):
            amount_received = 0
        
        # Parse multi-item transactions
        items = [item.strip() for item in product_details.split(",") if item.strip()]
        
        # Handle orders with no product details
        if not items:
            items = ["Unknown Item"]
        
        matched_items = []
        unmatched_items = []
        used_keys = set()

        for item in items:
            if psd_map:
                key = order_num.strip() + "||" + _normalize_product_name(item)
                if key in psd_map and key not in used_keys:
                    amount, qty = psd_map[key]
                    matched_items.append((item, amount, qty))
                    used_keys.add(key)
                    continue
            unmatched_items.append(item)

        matched_total = sum(m[1] for m in matched_items)
        remaining_total = max(float(amount_received) - matched_total, 0)
        unmatched_amount = remaining_total / len(unmatched_items) if unmatched_items else 0

        item_rows = []
        for item, amount, qty in matched_items:
            item_rows.append((item, amount, qty if qty else 1))
        for item in unmatched_items:
            item_rows.append((item, unmatched_amount, 1))

        for i, (item, amount, qty) in enumerate(item_rows):
            txn_id = f"{order_num}_{i}"
            sku_info = lookup_sku(item, "Haha_AI", mapping)
            transactions.append({
                "transaction_id": txn_id,
                "source_system": "Haha_AI",
                "timestamp": timestamp,
                "machine_name": str(row.get("Device number", "")),
                "product_name_original": item,
                "master_sku": sku_info["master_sku"],
                "master_name": sku_info["master_name"],
                "product_family": sku_info["product_family"],
                "quantity": float(qty),
                "amount": float(amount),
                "payment_method": "",
            })
    
    return transactions


def parse_nayax_dynamic(filepath: Path, mapping: dict) -> list[dict]:
    """Parse Nayax DynamicTransactionsMonitorMega CSV."""
    transactions = []
    
    try:
        # Try skiprows=1 first (newer format), then skiprows=2 (older format)
        df = pd.read_csv(filepath, skiprows=1)
        if 'Settlement Value (Vend Price)' not in [c.strip() for c in df.columns]:
            df = pd.read_csv(filepath, skiprows=2)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return transactions
    
    # Clean column names
    df.columns = [c.strip() for c in df.columns]
    
    for _, row in df.iterrows():
        txn_id = str(row.get("Transaction ID", ""))
        if not txn_id or txn_id == "nan":
            continue
        
        # Parse product from "Product Selection Info" - format: "ProductName(slot  price)"
        product_info = str(row.get("Product Selection Info", ""))
        product_name = re.sub(r"\([^)]+\)\s*$", "", product_info).strip()
        
        if not product_name:
            continue
        
        # Get amount
        amount = row.get("Settlement Value (Vend Price)", 0)
        if pd.isna(amount):
            amount = row.get("Authorization Value", 0)
        if pd.isna(amount):
            amount = 0
        
        timestamp = row.get("Machine Authorization Time", "")
        if pd.notna(timestamp):
            timestamp = str(timestamp)
        else:
            timestamp = ""
        
        sku_info = lookup_sku(product_name, "Nayax", mapping)
        
        transactions.append({
            "transaction_id": txn_id,
            "source_system": "Nayax",
            "timestamp": timestamp,
            "machine_name": str(row.get("Machine Name", "")),
            "product_name_original": product_name,
            "master_sku": sku_info["master_sku"],
            "master_name": sku_info["master_name"],
            "product_family": sku_info["product_family"],
            "quantity": 1,
            "amount": float(amount) if amount else 0,
            "payment_method": str(row.get("Payment Method (Source)", "")),
        })
    
    return transactions


def parse_cantaloupe_usat(filepath: Path, mapping: dict) -> list[dict]:
    """Parse Cantaloupe usat-transaction-log Excel file."""
    transactions = []
    
    try:
        df = pd.read_excel(filepath, sheet_name=0, header=2)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return transactions
    
    # Detect payment method and cash/card amount columns when available
    col_map = {c: str(c).lower().strip() for c in df.columns}
    payment_method_col = next(
        (c for c, lc in col_map.items() if any(k in lc for k in ["payment", "tender", "method", "type"])),
        None
    )
    cash_amount_cols = [
        c for c, lc in col_map.items()
        if "cash" in lc and any(k in lc for k in ["amount", "total", "value"])
    ]
    card_amount_cols = [
        c for c, lc in col_map.items()
        if any(k in lc for k in ["card", "credit", "debit"]) and any(k in lc for k in ["amount", "total", "value"])
    ]

    for idx, row in df.iterrows():
        timestamp = row.iloc[0] if len(row) > 0 else ""
        if pd.isna(timestamp) or str(timestamp).strip() == "":
            continue
        
        timestamp_str = str(timestamp)
        
        # Skip header-like rows
        if "timestamp" in timestamp_str.lower():
            continue
        
        location = row.iloc[1] if len(row) > 1 else ""
        machine = row.iloc[2] if len(row) > 2 else ""
        product_name = row.iloc[3] if len(row) > 3 else ""
        price = row.iloc[5] if len(row) > 5 else 0
        quantity = row.iloc[6] if len(row) > 6 else 1
        total = row.iloc[7] if len(row) > 7 else 0
        
        if pd.isna(product_name) or str(product_name).strip() == "":
            continue
        
        product_name = str(product_name).strip()
        
        # Create composite transaction ID
        txn_id = f"{timestamp_str}_{machine}_{product_name}_{total}"
        
        sku_info = lookup_sku(product_name, "Cantaloupe", mapping)
        
        # Determine payment method
        payment_method = ""
        if payment_method_col:
            payment_value = row.get(payment_method_col, "")
            if pd.notna(payment_value) and str(payment_value).strip():
                payment_method = str(payment_value).strip()

        if not payment_method and cash_amount_cols:
            cash_total = 0
            for c in cash_amount_cols:
                val = pd.to_numeric(row.get(c, 0), errors="coerce")
                if pd.notna(val):
                    cash_total += float(val)
            if cash_total > 0:
                payment_method = "Cash"

        if not payment_method and card_amount_cols:
            card_total = 0
            for c in card_amount_cols:
                val = pd.to_numeric(row.get(c, 0), errors="coerce")
                if pd.notna(val):
                    card_total += float(val)
            if card_total > 0:
                payment_method = "Card"

        if not payment_method:
            payment_method = "Card"

        transactions.append({
            "transaction_id": txn_id,
            "source_system": "Cantaloupe",
            "timestamp": timestamp_str,
            "machine_name": f"{location} - {machine}" if pd.notna(location) else str(machine),
            "product_name_original": product_name,
            "master_sku": sku_info["master_sku"],
            "master_name": sku_info["master_name"],
            "product_family": sku_info["product_family"],
            "quantity": float(quantity) if pd.notna(quantity) else 1,
            "amount": float(total) if pd.notna(total) else 0,
            "payment_method": payment_method,
        })
    
    return transactions


def import_file(filepath: Path) -> dict:
    """Import a file and return stats."""
    stats = {
        "filename": filepath.name,
        "source_system": "",
        "total_parsed": 0,
        "imported": 0,
        "duplicates": 0,
        "errors": [],
    }
    
    # Load SKU mapping
    mapping = load_sku_mapping()
    
    # Determine file type and parse
    name_lower = filepath.name.lower()
    
    if "order" in name_lower and "details" in name_lower:
        stats["source_system"] = "Haha_AI"
        psd_map = load_haha_product_sales_details()
        transactions = parse_haha_ai_order_details(filepath, mapping, psd_map)
    elif "dynamic" in name_lower or "mega" in name_lower:
        stats["source_system"] = "Nayax"
        transactions = parse_nayax_dynamic(filepath, mapping)
    elif "usat" in name_lower or "transaction-log" in name_lower:
        stats["source_system"] = "Cantaloupe"
        transactions = parse_cantaloupe_usat(filepath, mapping)
    else:
        stats["errors"].append(f"Unknown file format: {filepath.name}")
        return stats
    
    stats["total_parsed"] = len(transactions)
    
    if not transactions:
        stats["errors"].append("No transactions found in file")
        return stats
    
    # Insert into database with deduplication
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for txn in transactions:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO transactions 
                (transaction_id, source_system, timestamp, machine_name, 
                 product_name_original, master_sku, master_name, product_family,
                 quantity, amount, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn["transaction_id"],
                txn["source_system"],
                txn["timestamp"],
                txn["machine_name"],
                txn["product_name_original"],
                txn["master_sku"],
                txn["master_name"],
                txn["product_family"],
                txn["quantity"],
                txn["amount"],
                txn["payment_method"],
            ))
            
            if cursor.rowcount > 0:
                stats["imported"] += 1
            else:
                stats["duplicates"] += 1
                
        except Exception as e:
            stats["errors"].append(f"Error inserting transaction: {e}")
    
    conn.commit()
    conn.close()
    
    return stats


def get_transaction_summary() -> dict:
    """Get summary of all transactions in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    summary = {
        "total_transactions": 0,
        "total_revenue": 0,
        "by_source": {},
        "date_range": {"min": None, "max": None},
    }
    
    # Total count and revenue
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions")
    row = cursor.fetchone()
    summary["total_transactions"] = row[0] or 0
    summary["total_revenue"] = row[1] or 0
    
    # By source
    cursor.execute("""
        SELECT source_system, COUNT(*), SUM(amount) 
        FROM transactions 
        GROUP BY source_system
    """)
    for row in cursor.fetchall():
        summary["by_source"][row[0]] = {
            "count": row[1],
            "revenue": row[2] or 0,
        }
    
    # Date range
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM transactions")
    row = cursor.fetchone()
    summary["date_range"]["min"] = row[0]
    summary["date_range"]["max"] = row[1]
    
    conn.close()
    return summary


if __name__ == "__main__":
    # Test with files in uploads
    uploads_dir = Path(__file__).parent / "uploads"
    
    for filepath in uploads_dir.iterdir():
        if filepath.suffix.lower() in [".xlsx", ".xls", ".csv"]:
            print(f"\nImporting {filepath.name}...")
            stats = import_file(filepath)
            print(f"  Source: {stats['source_system']}")
            print(f"  Parsed: {stats['total_parsed']}")
            print(f"  Imported: {stats['imported']}")
            print(f"  Duplicates: {stats['duplicates']}")
            if stats["errors"]:
                print(f"  Errors: {stats['errors']}")
    
    print("\n" + "="*50)
    summary = get_transaction_summary()
    print(f"Total transactions: {summary['total_transactions']}")
    print(f"Total revenue: ${summary['total_revenue']:.2f}")
    print(f"Date range: {summary['date_range']['min']} to {summary['date_range']['max']}")
