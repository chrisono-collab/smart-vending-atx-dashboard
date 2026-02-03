#!/usr/bin/env python3
"""
Extract unique product names from Excel files in the uploads folder.
Creates a SKU mapping CSV with columns for each POS system.
"""

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd

# Configuration: Map file name patterns to POS system column names
# Use \s* to match spaces (filenames like "Product Sales Details" not "Product_Sales_Details")
FILE_TO_SYSTEM = {
    # Note: Order details excluded - it has multi-item transactions, not individual products
    r"(?i)haha|product\s*sales\s*details|product\s*sales\s*ranking|device\s*sales\s*ranking": "Haha_AI_Name",
    r"(?i)nayax|salessummary|dynamic.*mega": "Nayax_Name",
    r"(?i)cantaloupe|usat-transaction": "Cantaloupe_Name",
}

# Column name patterns to search for product names (in order of preference)
PRODUCT_COLUMN_PATTERNS = [
    r"product\s*name",
    r"item\s*name",
    r"^product$",
    r"product\s*details",
    r"^item$",
    r"description",
    r"sku",
    r"product_description",
    r"item_description",
]


def find_product_column(df: pd.DataFrame) -> Optional[str]:
    """Find the best column containing product names in a DataFrame."""
    cols_lower = {c: c.lower() for c in df.columns}
    for pattern in PRODUCT_COLUMN_PATTERNS:
        for col, col_lower in cols_lower.items():
            if re.search(pattern, col_lower) and df[col].dtype in ["object", "string"]:
                # Basic sanity check: column has reasonable string content
                non_null = df[col].dropna().astype(str)
                if len(non_null) > 0 and non_null.str.len().mean() > 2:
                    return col
    return None


def get_system_from_filename(filename: str) -> Optional[str]:
    """Determine which POS system a file belongs to based on filename."""
    name_lower = filename.lower()
    for pattern, system_col in FILE_TO_SYSTEM.items():
        if re.search(pattern, name_lower):
            return system_col
    return None


def _read_excel_safe(filepath: Path):
    """Load Excel file. Some Nayax files have malformed styles; open them in Excel and re-save if needed."""
    return pd.ExcelFile(filepath, engine="openpyxl")


def _extract_from_usat_transaction_log(filepath: Path) -> set[str]:
    """usat-transaction-log has headers in row 2, product names in column 3 (0-indexed)."""
    products = set()
    try:
        df = pd.read_excel(filepath, sheet_name=0, header=2)
        if len(df.columns) >= 4:
            # Product names are in the 4th column (index 3)
            col = df.iloc[:, 3]
            vals = col.dropna().astype(str).str.strip().str[:200]
            products.update(vals[vals.str.len() > 2].tolist())
    except Exception:
        pass
    return products


def extract_products_from_csv(filepath: Path) -> set[str]:
    """Extract unique product names from a CSV file."""
    products = set()
    name_lower = filepath.name.lower()
    
    # Skip SalesSummary - it's machine-level totals, no product names
    if "salessummary" in name_lower:
        return products
    
    try:
        # Nayax CSVs have headers on row 3 (skip first 2 rows)
        if "dynamic" in name_lower or "mega" in name_lower:
            df = pd.read_csv(filepath, skiprows=2)
            # Product column is "Product Selection Info" with format "ProductName(slot  price)"
            for col in df.columns:
                if "product" in col.lower() or "selection" in col.lower():
                    vals = df[col].dropna().astype(str)
                    # Clean: remove "(number  price)\n" suffix
                    vals = vals.str.replace(r"\([^)]+\)\s*$", "", regex=True).str.strip()
                    products.update(vals[vals.str.len() > 1].tolist())
                    break
        else:
            df = pd.read_csv(filepath)
            if df.empty:
                return products
            product_col = find_product_column(df)
            if product_col:
                vals = df[product_col].dropna().astype(str).str.strip().str[:200]
                products.update(vals[vals.str.len() > 1].tolist())
    except Exception as e:
        print(f"  Warning: Could not read {filepath.name}: {e}")
    return products


def extract_products_from_excel(filepath: Path, system_col: str) -> set[str]:
    """Extract unique product names from an Excel file."""
    products = set()

    # Special handling for usat-transaction-log (Cantaloupe/Vendsoft format)
    if "usat-transaction-log" in filepath.name.lower():
        products = _extract_from_usat_transaction_log(filepath)
        return products

    try:
        xl = _read_excel_safe(filepath)
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                if df.empty or len(df.columns) == 0:
                    continue
                product_col = find_product_column(df)
                if product_col:
                    vals = (
                        df[product_col]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .str[:200]  # Limit length
                    )
                    products.update(vals[vals.str.len() > 1].tolist())
            except Exception:
                continue
    except Exception as e:
        print(f"  Warning: Could not read {filepath.name}: {e}")
    return products


def main():
    uploads_dir = Path(__file__).parent / "uploads"
    output_path = Path(__file__).parent / "data" / "sku_mapping.csv"
    output_path.parent.mkdir(exist_ok=True)

    if not uploads_dir.exists():
        print(f"Error: uploads directory not found at {uploads_dir}")
        return 1

    # Load existing mapping if it exists (to preserve user edits)
    existing_df = None
    existing_source_names = set()  # All names in Haha_AI_Name, Nayax_Name, Cantaloupe_Name columns
    if output_path.exists():
        existing_df = pd.read_csv(output_path, dtype=str).fillna("")
        for col in ["Haha_AI_Name", "Nayax_Name", "Cantaloupe_Name"]:
            if col in existing_df.columns:
                existing_source_names.update(existing_df[col][existing_df[col] != ""].tolist())
        print(f"Loaded existing mapping with {len(existing_df)} rows")

    # Collect products by system from source files
    systems: dict[str, set[str]] = {
        "Haha_AI_Name": set(),
        "Nayax_Name": set(),
        "Cantaloupe_Name": set(),
    }

    excel_files = list(uploads_dir.glob("*.xlsx")) + list(uploads_dir.glob("*.xls"))
    csv_files = list(uploads_dir.glob("*.csv"))
    all_files = excel_files + csv_files
    
    if not all_files:
        print(f"No Excel or CSV files found in {uploads_dir}")
        print("Please add files to the uploads folder and run again.")
        return 1

    print(f"Found {len(all_files)} file(s) in uploads/")
    for filepath in all_files:
        system_col = get_system_from_filename(filepath.name)
        if system_col:
            if filepath.suffix.lower() == ".csv":
                products = extract_products_from_csv(filepath)
            else:
                products = extract_products_from_excel(filepath, system_col)
            systems[system_col].update(products)
            print(f"  {filepath.name} -> {system_col}: {len(products)} products")
        else:
            print(f"  {filepath.name} -> (skipped, no system match)")

    # Find NEW products not already in existing mapping
    all_source_products = (
        systems["Haha_AI_Name"] | systems["Nayax_Name"] | systems["Cantaloupe_Name"]
    )
    all_source_products = {p for p in all_source_products if p and not p.isspace()}
    
    new_products = all_source_products - existing_source_names
    new_products = sorted(new_products)

    if existing_df is not None:
        # Preserve existing mapping, only add new products
        if new_products:
            # Find next SKU number
            existing_skus = existing_df["Master_SKU"].tolist()
            max_sku_num = 0
            for sku in existing_skus:
                try:
                    num = int(sku.replace("SKU", ""))
                    max_sku_num = max(max_sku_num, num)
                except:
                    pass
            
            # Create rows for new products
            new_rows = []
            for i, product_name in enumerate(new_products):
                sku_num = max_sku_num + i + 1
                row = {
                    "Master_SKU": f"SKU{sku_num:04d}",
                    "Master_Name": product_name,
                    "Product_Family": "",
                    "Status": "New",
                    "Haha_AI_Name": product_name if product_name in systems["Haha_AI_Name"] else "",
                    "Nayax_Name": product_name if product_name in systems["Nayax_Name"] else "",
                    "Cantaloupe_Name": product_name if product_name in systems["Cantaloupe_Name"] else "",
                }
                new_rows.append(row)
            
            # Add Status column to existing if not present
            if "Status" not in existing_df.columns:
                existing_df["Status"] = ""
            
            # Append new rows
            new_df = pd.DataFrame(new_rows)
            df = pd.concat([existing_df, new_df], ignore_index=True)
            print(f"\n✅ Added {len(new_products)} NEW products (marked as 'New')")
        else:
            df = existing_df
            if "Status" not in df.columns:
                df["Status"] = ""
            print("\n✅ No new products found. Existing mapping unchanged.")
    else:
        # First run - create new mapping
        all_products = sorted(all_source_products)
        if not all_products:
            print("No products found. Check that your Excel files have product name columns.")
            return 1
            
        df = pd.DataFrame(
            {
                "Master_SKU": [f"SKU{i+1:04d}" for i in range(len(all_products))],
                "Master_Name": all_products,
                "Product_Family": "",
                "Status": "New",
                "Haha_AI_Name": "",
                "Nayax_Name": "",
                "Cantaloupe_Name": "",
            }
        )
        # Pre-populate mappings where product name matches
        for i, master_name in enumerate(all_products):
            for sys_col, products in systems.items():
                if master_name in products:
                    df.at[i, sys_col] = master_name
        print(f"\n✅ Created new mapping with {len(df)} products (all marked as 'New')")

    # Reorder columns
    col_order = ["Master_SKU", "Master_Name", "Product_Family", "Status", "Haha_AI_Name", "Nayax_Name", "Cantaloupe_Name"]
    df = df[[c for c in col_order if c in df.columns]]
    
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path} ({len(df)} total rows)")
    return 0


if __name__ == "__main__":
    exit(main())
