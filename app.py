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
    ["Dashboard", "SKU Mapper"],
    index=0
)

# SKU Mapper page
if page == "SKU Mapper":
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

    st.info("✨ Dashboard is being built! Check back soon.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue", "$0.00", "0%")
    with col2:
        st.metric("Total Transactions", "0", "0")
    with col3:
        st.metric("Avg Transaction", "$0.00", "0%")
