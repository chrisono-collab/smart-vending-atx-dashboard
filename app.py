import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Smart Vending ATX Dashboard",
    page_icon="🏢",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("🏢 Smart Vending ATX")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Upload Data", "SKU Mapper"],
    index=0
)

# Upload Data page
if page == "Upload Data":
    st.title("📤 Upload Sales Data")
    st.markdown("Import transaction data from your POS systems.")
    st.markdown("---")
    
    from import_transactions import import_file, get_transaction_summary
    
    # File upload
    st.subheader("Upload POS Export Files")
    st.markdown("""
    **Supported files:**
    - **Haha AI:** Order details (.xlsx)
    - **Nayax:** DynamicTransactionsMonitorMega (.csv)
    - **Cantaloupe:** usat-transaction-log (.xlsx)
    """)
    
    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("🚀 Import Files", type="primary"):
            results = []
            progress = st.progress(0)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Save to temp location
                temp_path = Path(__file__).parent / "uploads" / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Import
                stats = import_file(temp_path)
                results.append(stats)
                
                progress.progress((i + 1) / len(uploaded_files))
            
            # Show results
            st.subheader("Import Results")
            
            total_imported = sum(r["imported"] for r in results)
            total_duplicates = sum(r["duplicates"] for r in results)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files Processed", len(results))
            with col2:
                st.metric("Transactions Imported", total_imported)
            with col3:
                st.metric("Duplicates Skipped", total_duplicates)
            
            # Details per file
            for stats in results:
                with st.expander(f"📄 {stats['filename']}"):
                    st.write(f"**Source:** {stats['source_system']}")
                    st.write(f"**Parsed:** {stats['total_parsed']} transactions")
                    st.write(f"**Imported:** {stats['imported']} new")
                    st.write(f"**Duplicates:** {stats['duplicates']} skipped")
                    if stats["errors"]:
                        st.error(f"Errors: {', '.join(stats['errors'])}")
    
    # Current database summary
    st.markdown("---")
    st.subheader("📊 Database Summary")
    
    summary = get_transaction_summary()
    
    if summary["total_transactions"] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", f"{summary['total_transactions']:,}")
        with col2:
            st.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
        with col3:
            avg = summary['total_revenue'] / summary['total_transactions'] if summary['total_transactions'] else 0
            st.metric("Avg Transaction", f"${avg:.2f}")
        
        st.write(f"**Date Range:** {summary['date_range']['min']} to {summary['date_range']['max']}")
        
        # By source
        st.markdown("**By POS System:**")
        source_data = []
        for source, data in summary["by_source"].items():
            source_data.append({
                "Source": source,
                "Transactions": data["count"],
                "Revenue": f"${data['revenue']:,.2f}"
            })
        if source_data:
            st.dataframe(pd.DataFrame(source_data), hide_index=True)
    else:
        st.info("No transactions imported yet. Upload your POS export files above to get started.")

# SKU Mapper page
elif page == "SKU Mapper":
    st.title("📋 SKU Mapper")
    st.markdown("View and edit product mappings across POS systems.")
    st.markdown("---")

    mapping_path = Path(__file__).parent / "data" / "sku_mapping.csv"

    if mapping_path.exists():
        df = pd.read_csv(mapping_path, dtype=str).fillna("")
        
        # Add Status column if missing (for backward compatibility)
        if "Status" not in df.columns:
            df["Status"] = ""

        st.info(
            "💡 Run `python extract_products.py` to scan for new products. "
            "Your existing mappings are preserved, and new items are marked as 'New'."
        )
        
        # Filter options
        col_filter, col_stats, _ = st.columns([2, 2, 4])
        with col_filter:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "New (needs review)", "Mapped", "Blank status"],
                index=0
            )
        with col_stats:
            new_count = len(df[df["Status"] == "New"])
            mapped_count = len(df[df["Status"] == "Mapped"])
            st.metric("New items", new_count, delta=None)
        
        # Apply filter
        if status_filter == "New (needs review)":
            display_df = df[df["Status"] == "New"].copy()
        elif status_filter == "Mapped":
            display_df = df[df["Status"] == "Mapped"].copy()
        elif status_filter == "Blank status":
            display_df = df[df["Status"] == ""].copy()
        else:
            display_df = df.copy()

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Master_SKU": st.column_config.TextColumn("Master SKU"),
                "Master_Name": st.column_config.TextColumn("Master Name"),
                "Product_Family": st.column_config.TextColumn("Product Family", help="For inventory grouping (e.g., 'Alani Variety' for all Alani flavors)"),
                "Status": st.column_config.SelectboxColumn("Status", options=["New", "Mapped", ""], help="Mark as 'Mapped' when reviewed"),
                "Haha_AI_Name": st.column_config.TextColumn("Haha AI Name"),
                "Nayax_Name": st.column_config.TextColumn("Nayax Name"),
                "Cantaloupe_Name": st.column_config.TextColumn("Cantaloupe Name"),
            },
        )

        col1, col2, col3, _ = st.columns([1, 1, 2, 3])
        with col1:
            if st.button("💾 Save Changes"):
                # Merge edits back into full dataframe
                if status_filter != "All":
                    for idx, row in edited_df.iterrows():
                        mask = df["Master_SKU"] == row["Master_SKU"]
                        if mask.any():
                            df.loc[mask] = row
                        else:
                            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                    df.to_csv(mapping_path, index=False)
                else:
                    edited_df.to_csv(mapping_path, index=False)
                st.success("Changes saved!")
                st.rerun()
        with col2:
            if st.button("🔄 Reset"):
                st.rerun()
        with col3:
            if st.button("✅ Mark filtered as 'Mapped'"):
                if status_filter != "All":
                    for idx, row in display_df.iterrows():
                        mask = df["Master_SKU"] == row["Master_SKU"]
                        df.loc[mask, "Status"] = "Mapped"
                    df.to_csv(mapping_path, index=False)
                    st.success(f"Marked {len(display_df)} items as Mapped!")
                    st.rerun()
    else:
        st.warning(
            f"Mapping file not found at `{mapping_path}`. "
            "Run `python extract_products.py` to create it from your Excel files in the uploads folder."
        )
        st.code("python extract_products.py", language="bash")

# Dashboard page (default)
else:
    st.title("🏢 Smart Vending ATX Dashboard")
    st.markdown("---")
    
    from import_transactions import get_transaction_summary, get_db_connection
    
    summary = get_transaction_summary()
    
    if summary["total_transactions"] > 0:
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
        with col2:
            st.metric("Total Transactions", f"{summary['total_transactions']:,}")
        with col3:
            avg = summary['total_revenue'] / summary['total_transactions']
            st.metric("Avg Transaction", f"${avg:.2f}")
        
        st.markdown("---")
        
        # Revenue by source
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenue by POS System")
            source_data = []
            for source, data in summary["by_source"].items():
                source_data.append({
                    "Source": source,
                    "Revenue": data["revenue"],
                })
            if source_data:
                fig = px.pie(
                    pd.DataFrame(source_data), 
                    values="Revenue", 
                    names="Source",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Transactions by POS System")
            source_data = []
            for source, data in summary["by_source"].items():
                source_data.append({
                    "Source": source,
                    "Transactions": data["count"],
                })
            if source_data:
                fig = px.bar(
                    pd.DataFrame(source_data),
                    x="Source",
                    y="Transactions",
                    color="Source"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Top products
        st.subheader("Top 10 Products by Revenue")
        conn = get_db_connection()
        top_products = pd.read_sql_query("""
            SELECT 
                COALESCE(NULLIF(master_name, ''), product_name_original) as Product,
                SUM(quantity) as Quantity,
                SUM(amount) as Revenue
            FROM transactions
            GROUP BY Product
            ORDER BY Revenue DESC
            LIMIT 10
        """, conn)
        conn.close()
        
        if not top_products.empty:
            top_products["Revenue"] = top_products["Revenue"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(top_products, hide_index=True, use_container_width=True)
    else:
        st.info("✨ No data yet! Go to **Upload Data** to import your POS exports.")
