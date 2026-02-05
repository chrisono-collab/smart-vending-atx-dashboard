import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# UI INITIALIZATION & CUSTOM COMPONENTS
# ============================================================

def initialize_ui():
    st.set_page_config(
        layout="wide", 
        page_title="Smart Vending ATX",
        page_icon="🏢",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for the dark card-based aesthetic
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600&display=swap');

    /* Background and Global Styles */
    .stApp {
        background-color: #0e1112;
        color: #f0f2f6;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161a1d;
        border-right: 1px solid #2d3135;
    }
    
    section[data-testid="stSidebar"] .stRadio > label {
        color: #f0f2f6;
    }
    
    section[data-testid="stSidebar"] * {
        font-family: 'Inter', sans-serif !important;
    }
    
    section[data-testid="stSidebar"] {
        font-size: 12px;
    }
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        font-size: 12px !important;
    }

    /* Metric Card Container */
    .metric-card {
        background-color: #161a1d;
        border: 1px solid #2d3135;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    /* Typography */
    h1 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: #f0f2f6 !important;
    }
    
    h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 600 !important;
        color: #f0f2f6 !important;
    }

    .metric-title {
        color: #808495;
        font-size: 0.8rem;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 600;
        color: white;
    }
    
    .metric-subtitle {
        color: #808495;
        font-size: 0.75rem;
        margin-top: 4px;
    }

    .metric-delta {
        font-size: 0.9rem;
        font-weight: 500;
        margin-left: 8px;
    }

    /* Plotly Chart Overrides */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
    
    /* Override Streamlit's default metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #f0f2f6;
    }
    
    [data-testid="stMetricLabel"] {
        color: #808495;
    }
    
    /* Data editor and tables */
    [data-testid="stDataFrame"] {
        background-color: #161a1d;
        border-radius: 12px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00cc6d);
        color: #0e1112;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00ff99, #00dd7d);
        border: none;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #161a1d;
        border: 2px dashed #2d3135;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        background-color: #161a1d;
        border: 1px solid #2d3135;
        border-radius: 12px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Dividers */
    hr {
        border-color: #2d3135;
        margin: 1.5rem 0;
    }
    
    /* Section header */
    .section-header {
        color: #f0f2f6;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def make_metric(title, value, delta=None, is_positive=True, subtitle=None):
    """Create a styled metric card"""
    delta_html = ""
    if delta:
        delta_color = "#00ff88" if is_positive else "#ff4b4b"
        arrow = "↓" if is_positive else "↑"
        delta_html = f'<span class="metric-delta" style="color: {delta_color};">{arrow} {delta}</span>'
    
    subtitle_html = f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ""
    
    html = f'<div class="metric-card"><div class="metric-title">{title}</div><div style="display: flex; align-items: baseline;"><span class="metric-value">{value}</span>{delta_html}</div>{subtitle_html}</div>'
    return st.markdown(html, unsafe_allow_html=True)




def apply_chart_styling(fig, height=400, show_legend=False):
    """Apply consistent dark theme styling to Plotly charts"""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        font_color="#808495",
        height=height,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=show_legend,
        legend=dict(
            font=dict(color='#808495', size=11),
            bgcolor='rgba(0,0,0,0)'
        )
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor='#2d3135',
        tickfont=dict(color='#808495')
    )
    fig.update_yaxes(
        gridcolor='#2d3135',
        linecolor='#2d3135',
        tickfont=dict(color='#808495')
    )
    return fig


# Color palette
COLORS = {
    'primary': '#00ff88',
    'secondary': '#00cc6d', 
    'tertiary': '#008044',
    'gradient': ['#008044', '#00cc6d', '#00ff88'],
    'discrete': ['#00ff88', '#00cc6d', '#008044', '#00aa55', '#006633']
}


def load_inventory_costs():
    """Load inventory cost data from supported files."""
    sku_path = Path(__file__).parent / "data" / "sku_mapping.csv"
    if sku_path.exists():
        sku_df = pd.read_csv(sku_path, dtype=str).fillna("")
        if "Unit_Cost" in sku_df.columns:
            sku_df["Unit_Cost"] = (
                sku_df["Unit_Cost"]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            sku_df["Unit_Cost"] = pd.to_numeric(sku_df["Unit_Cost"], errors="coerce")
            sku_df = sku_df.dropna(subset=["Unit_Cost"])
            sku_df = sku_df[sku_df["Unit_Cost"] > 0]
            if not sku_df.empty:
                sku_df["key"] = sku_df["Master_Name"].astype(str).str.lower().str.strip()
                return dict(zip(sku_df["key"], sku_df["Unit_Cost"]))

    data_dir = Path(__file__).parent / "data"
    candidates = [
        data_dir / "Inventory Pricing Sheet - on_hand.csv",
        data_dir / "inventory_pricing.csv",
        data_dir / "inventory_pricing.xlsx",
        data_dir / "inventory_pricing.xls",
    ]

    df = None
    for path in candidates:
        if path.exists():
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            break

    if df is None or df.empty:
        return None

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    columns = {c: str(c).lower().strip() for c in df.columns}
    name_candidates = [c for c, lc in columns.items() if lc in ["item", "product", "name"]]
    if not name_candidates:
        name_candidates = [c for c, lc in columns.items() if "product" in lc or "item" in lc or "name" in lc]
    cost_candidates = [c for c, lc in columns.items() if lc == "cost"]
    if not cost_candidates:
        cost_candidates = [
            c for c, lc in columns.items()
            if "cost" in lc or "unit cost" in lc or "unit_cost" in lc or "unit price" in lc
        ]

    if not name_candidates or not cost_candidates:
        return None

    name_col = name_candidates[0]
    cost_col = cost_candidates[0]

    cost_df = df[[name_col, cost_col]].copy()
    cost_df[name_col] = cost_df[name_col].astype(str).str.strip()
    cost_df[cost_col] = (
        cost_df[cost_col]
        .astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
    )
    cost_df[cost_col] = pd.to_numeric(cost_df[cost_col], errors="coerce")
    cost_df = cost_df.dropna(subset=[name_col, cost_col])
    cost_df = cost_df[cost_df[cost_col] > 0]

    if cost_df.empty:
        return None

    cost_df["key"] = cost_df[name_col].str.lower()
    return dict(zip(cost_df["key"], cost_df[cost_col]))


def load_product_tax_rates():
    """Load product-level tax rates from Product Sales Details."""
    data_dir = Path(__file__).parent / "data"
    candidates = list(data_dir.glob("Product Sales Details*.xlsx"))
    if not candidates:
        return {}
    path = candidates[0]
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        return {}

    cols = {c: str(c).lower().strip() for c in df.columns}
    product_col = next((c for c, lc in cols.items() if lc == "product"), None)
    tax_col = next((c for c, lc in cols.items() if "tax" in lc), None)
    subtotal_col = next((c for c, lc in cols.items() if "subtotal" in lc), None)

    if not product_col or not tax_col or not subtotal_col:
        return {}

    tax_df = df[[product_col, tax_col, subtotal_col]].copy()
    tax_df[product_col] = tax_df[product_col].astype(str).str.strip()
    tax_df[tax_col] = pd.to_numeric(tax_df[tax_col], errors="coerce").fillna(0)
    tax_df[subtotal_col] = pd.to_numeric(tax_df[subtotal_col], errors="coerce").fillna(0)

    grouped = tax_df.groupby(product_col, as_index=False).agg(
        Tax=(tax_col, "sum"),
        Subtotal=(subtotal_col, "sum"),
    )
    grouped = grouped[grouped["Subtotal"] > 0]
    grouped["Tax_Rate"] = grouped["Tax"] / grouped["Subtotal"]
    grouped["key"] = grouped[product_col].str.lower().str.strip()
    return dict(zip(grouped["key"], grouped["Tax_Rate"]))


def apply_quantity_adjustments(txn_df: pd.DataFrame) -> pd.DataFrame:
    """Adjust quantities for bundled transactions based on median unit price."""
    df = txn_df.copy()
    df["Unit_Price"] = df.apply(
        lambda r: (r["Revenue"] / r["Items"]) if r["Items"] and r["Items"] > 0 else None,
        axis=1
    )
    median_price = (
        df.dropna(subset=["Unit_Price"])
        .groupby("Product")["Unit_Price"]
        .median()
        .to_dict()
    )
    df["Median_Price"] = df["Product"].map(median_price)

    def adjust_qty(row):
        if not row["Median_Price"] or row["Median_Price"] <= 0:
            return row["Items"]
        if row["Revenue"] > row["Median_Price"] * 1.5:
            est = round(row["Revenue"] / row["Median_Price"])
            return max(int(est), 1)
        return int(row["Items"]) if row["Items"] and row["Items"] > 0 else 1

    df["Adj_Items"] = df.apply(adjust_qty, axis=1)
    return df


# ============================================================
# INITIALIZE UI
# ============================================================
initialize_ui()


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
show_sidebar = st.toggle("Show sidebar", value=True, key="show_sidebar")
if not show_sidebar:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stAppViewContainer"] {margin-left: 0 !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("""
    <div style="padding: 1rem 0; margin-bottom: 1rem;">
        <h2 style="color: #f0f2f6; font-size: 1.25rem; font-weight: 700; margin: 0; font-family: 'Playfair Display', serif;">
            Smart Vending ATX
        </h2>
    </div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Upload Data", "SKU Mapper"],
    index=0,
    label_visibility="collapsed"
)


# ============================================================
# UPLOAD DATA PAGE
# ============================================================
if page == "Upload Data":
    st.title("Upload Sales Data")
    st.markdown('<p style="color: #808495; margin-bottom: 2rem;">Import transaction data from your POS systems.</p>', unsafe_allow_html=True)
    
    from import_transactions import import_file, get_transaction_summary
    
    # Supported files card
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">Supported Files</div>
        <div style="color: #808495; font-size: 0.9rem; margin-top: 12px;">
            <p style="margin: 8px 0;"><span style="color: #00ff88;">●</span> Haha AI: Order details (.xlsx)</p>
            <p style="margin: 8px 0;"><span style="color: #00cc6d;">●</span> Nayax: DynamicTransactionsMonitorMega (.csv)</p>
            <p style="margin: 8px 0;"><span style="color: #008044;">●</span> Cantaloupe: usat-transaction-log (.xlsx)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Import Files", type="primary"):
            results = []
            progress = st.progress(0)
            
            for i, uploaded_file in enumerate(uploaded_files):
                temp_path = Path(__file__).parent / "uploads" / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                stats = import_file(temp_path)
                results.append(stats)
                progress.progress((i + 1) / len(uploaded_files))
            
            st.markdown('<div class="section-header">Import Results</div>', unsafe_allow_html=True)
            
            total_imported = sum(r["imported"] for r in results)
            total_duplicates = sum(r["duplicates"] for r in results)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                make_metric("Files Processed", len(results))
            with col2:
                make_metric("Transactions Imported", f"{total_imported:,}")
            with col3:
                make_metric("Duplicates Skipped", f"{total_duplicates:,}")
            
            for stats in results:
                with st.expander(f"{stats['filename']}"):
                    st.write(f"**Source:** {stats['source_system']}")
                    st.write(f"**Parsed:** {stats['total_parsed']} transactions")
                    st.write(f"**Imported:** {stats['imported']} new")
                    st.write(f"**Duplicates:** {stats['duplicates']} skipped")
                    if stats["errors"]:
                        st.error(f"Errors: {', '.join(stats['errors'])}")
    
    st.markdown("---")
    st.markdown('<div class="section-header">Database Summary</div>', unsafe_allow_html=True)
    
    summary = get_transaction_summary()
    
    if summary["total_transactions"] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            make_metric("Total Transactions", f"{summary['total_transactions']:,}")
        with col2:
            make_metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
        with col3:
            avg = summary['total_revenue'] / summary['total_transactions'] if summary['total_transactions'] else 0
            make_metric("Avg Transaction", f"${avg:.2f}")
        
        st.markdown(f"<p style='color: #808495; margin-top: 1rem;'>Date Range: {summary['date_range']['min']} to {summary['date_range']['max']}</p>", unsafe_allow_html=True)
        
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


# ============================================================
# SKU MAPPER PAGE
# ============================================================
elif page == "SKU Mapper":
    st.title("SKU Mapper")
    st.markdown('<p style="color: #808495; margin-bottom: 2rem;">View and edit product mappings across POS systems.</p>', unsafe_allow_html=True)

    mapping_path = Path(__file__).parent / "data" / "sku_mapping.csv"

    if mapping_path.exists():
        df = pd.read_csv(mapping_path, dtype=str).fillna("")
        
        if "Status" not in df.columns:
            df["Status"] = ""
        if "Unit_Cost" not in df.columns:
            df["Unit_Cost"] = ""

        st.caption(
            "Tip: Run `python extract_products.py` to scan for new products. "
            "Existing mappings are preserved; new items are marked as 'New'."
        )
        
        col_filter, col_order, col_sort, col_stats = st.columns([2, 2, 2, 2])
        with col_filter:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "New (needs review)", "Mapped", "Blank status"],
                index=0
            )
        with col_order:
            sort_dir = st.selectbox("Order", options=["Ascending", "Descending"], index=0)
        with col_sort:
            sort_by = st.selectbox(
                "Sort by",
                options=df.columns.tolist(),
                index=0
            )
        with col_stats:
            new_count = len(df[df["Status"] == "New"])
            st.metric("New Items", new_count)
        
        if status_filter == "New (needs review)":
            display_df = df[df["Status"] == "New"].copy()
        elif status_filter == "Mapped":
            display_df = df[df["Status"] == "Mapped"].copy()
        elif status_filter == "Blank status":
            display_df = df[df["Status"] == ""].copy()
        else:
            display_df = df.copy()

        if sort_by in display_df.columns:
            display_df = display_df.sort_values(
                by=sort_by,
                ascending=(sort_dir == "Ascending"),
                kind="stable",
                na_position="last"
            )

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Master_SKU": st.column_config.TextColumn("Master SKU"),
                "Master_Name": st.column_config.TextColumn("Master Name"),
                "Product_Family": st.column_config.TextColumn("Product Family"),
                "Unit_Cost": st.column_config.NumberColumn("Unit Cost", help="Your cost per item"),
                "Status": st.column_config.SelectboxColumn("Status", options=["New", "Mapped", ""]),
                "Haha_AI_Name": st.column_config.TextColumn("Haha AI Name"),
                "Nayax_Name": st.column_config.TextColumn("Nayax Name"),
                "Cantaloupe_Name": st.column_config.TextColumn("Cantaloupe Name"),
            },
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Changes", use_container_width=True):
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
            if st.button("Reset", use_container_width=True):
                st.rerun()
        with col3:
            if st.button("Mark filtered as Mapped", use_container_width=True):
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
            "Run `python extract_products.py` to create it."
        )


# ============================================================
# DASHBOARD PAGE
# ============================================================
else:
    st.title("Dashboard")
    
    from import_transactions import get_db_connection
    from datetime import datetime, timedelta
    
    # Load location mapping
    location_mapping = {}
    location_map_path = Path(__file__).parent / "data" / "location_mapping.csv"
    if location_map_path.exists():
        loc_df = pd.read_csv(location_map_path)
        location_mapping = dict(zip(loc_df["raw_name"], loc_df["display_name"]))
    
    def map_location(name):
        return location_mapping.get(name, name)
    
    conn = get_db_connection()
    
    total_check = pd.read_sql_query("SELECT COUNT(*) as cnt FROM transactions", conn)
    
    if total_check["cnt"].iloc[0] > 0:
        # Date filter in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown('<p style="color: #808495; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">Date Filter</p>', unsafe_allow_html=True)
        
        date_filter = st.sidebar.radio(
            "Period",
            ["All Time", "This Month", "Last 7 Days", "Custom"],
            index=0,
            label_visibility="collapsed"
        )
        
        date_clause = ""
        if date_filter == "This Month":
            first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-01")
            date_clause = f"AND timestamp >= '{first_of_month}'"
        elif date_filter == "Last 7 Days":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            date_clause = f"AND timestamp >= '{week_ago}'"
        elif date_filter == "Custom":
            col1, col2 = st.sidebar.columns(2)
            start_date = col1.date_input("From", datetime(2026, 1, 1))
            end_date = col2.date_input("To", datetime.now())
            date_clause = f"AND timestamp >= '{start_date}' AND timestamp <= '{end_date} 23:59:59'"

        # Location filter in sidebar
        st.sidebar.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color: #808495; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">Location Filter</p>', unsafe_allow_html=True)

        locations_df = pd.read_sql_query(
            "SELECT DISTINCT machine_name FROM transactions WHERE machine_name IS NOT NULL AND machine_name != ''",
            conn
        )
        if not locations_df.empty:
            locations_df["Location"] = locations_df["machine_name"].apply(map_location)
            location_options = sorted(locations_df["Location"].dropna().unique().tolist())
        else:
            location_options = []

        selected_locations = []
        if location_options:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Select all"):
                    for loc in location_options:
                        st.session_state[f"loc_{loc}"] = True
            with col2:
                if st.button("Clear all"):
                    for loc in location_options:
                        st.session_state[f"loc_{loc}"] = False

            st.sidebar.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            for loc in location_options:
                key = f"loc_{loc}"
                if key not in st.session_state:
                    st.session_state[key] = True
                checked = st.sidebar.checkbox(loc, value=st.session_state[key], key=key)
                if checked:
                    selected_locations.append(loc)

        location_clause = ""
        if location_options:
            if not selected_locations:
                location_clause = "AND 1=0"
            elif len(selected_locations) != len(location_options):
                selected_raw = locations_df[locations_df["Location"].isin(selected_locations)]["machine_name"].tolist()
                if selected_raw:
                    selected_raw = [name.replace("'", "''") for name in selected_raw]
                    quoted_names = ", ".join("'{}'".format(name) for name in selected_raw)
                    location_clause = f"AND machine_name IN ({quoted_names})"
                else:
                    location_clause = "AND 1=0"
        
        # Key Metrics Row
        metrics = pd.read_sql_query(f"""
            SELECT 
                COUNT(*) as total_items,
                SUM(amount) as total_revenue,
                AVG(amount) as avg_transaction,
                COUNT(DISTINCT SUBSTR(transaction_id, 1, INSTR(transaction_id, '_') - 1)) as total_orders
            FROM transactions
            WHERE 1=1 {date_clause} {location_clause}
        """, conn)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            make_metric("Total Revenue", f"${metrics['total_revenue'].iloc[0]:,.2f}")
        with col2:
            make_metric("Items Sold", f"{metrics['total_items'].iloc[0]:,}")
        with col3:
            make_metric("Avg Transaction", f"${metrics['avg_transaction'].iloc[0]:.2f}")
        with col4:
            make_metric("Total Orders", f"{metrics['total_orders'].iloc[0]:,}")
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 2: Revenue by Location + Revenue by Category
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Revenue by Location</p>', unsafe_allow_html=True)
            
            machine_revenue = pd.read_sql_query(f"""
                SELECT 
                    machine_name as Machine,
                    COUNT(*) as Items,
                    ROUND(SUM(amount), 2) as Revenue
                FROM transactions
                WHERE machine_name IS NOT NULL AND machine_name != ''
                {date_clause} {location_clause}
                GROUP BY machine_name
                ORDER BY Revenue DESC
            """, conn)
            
            if not machine_revenue.empty:
                machine_revenue["Location"] = machine_revenue["Machine"].apply(map_location)
                
                fig = go.Figure(go.Bar(
                    x=machine_revenue["Revenue"],
                    y=machine_revenue["Location"],
                    orientation='h',
                    marker=dict(
                        color=machine_revenue["Revenue"],
                        colorscale=[[0, '#008044'], [0.5, '#00cc6d'], [1, '#00ff88']],
                        cornerradius=4
                    ),
                    text=machine_revenue["Revenue"].apply(lambda x: f"${x:,.0f}"),
                    textposition='inside',
                    textfont=dict(color='#0e1112', size=11, weight='bold'),
                    hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>"
                ))
                fig = apply_chart_styling(fig, height=500)
                fig.update_layout(
                    yaxis=dict(categoryorder='total ascending', tickfont=dict(color='#808495', size=11)),
                    margin=dict(l=180, r=30, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Revenue by Category</p>', unsafe_allow_html=True)
            
            category_revenue = pd.read_sql_query(f"""
                SELECT 
                    COALESCE(NULLIF(product_family, ''), 'Uncategorized') as Category,
                    ROUND(SUM(amount), 2) as Revenue,
                    CAST(SUM(quantity) AS INTEGER) as Items
                FROM transactions
                WHERE 1=1 {date_clause} {location_clause}
                GROUP BY Category
                ORDER BY Revenue DESC
                LIMIT 20
            """, conn)
            
            if not category_revenue.empty:
                fig = go.Figure(go.Bar(
                    x=category_revenue["Revenue"],
                    y=category_revenue["Category"],
                    orientation='h',
                    marker=dict(
                        color=category_revenue["Revenue"],
                        colorscale=[[0, '#008044'], [0.5, '#00cc6d'], [1, '#00ff88']],
                        cornerradius=4
                    ),
                    text=category_revenue["Revenue"].apply(lambda x: f"${x:,.0f}"),
                    textposition='inside',
                    textfont=dict(color='#0e1112', size=11, weight='bold'),
                    hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<br>Items: %{customdata}<extra></extra>",
                    customdata=category_revenue["Items"]
                ))
                fig = apply_chart_styling(fig, height=450)
                fig.update_layout(
                    yaxis=dict(categoryorder='total ascending', tickfont=dict(color='#808495', size=11)),
                    margin=dict(l=180, r=30, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 3: Daily Revenue Trend (full width)
        st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Daily Revenue Trend</p>', unsafe_allow_html=True)
        
        date_expr = """
            CASE 
                WHEN INSTR(timestamp, '/') > 0 THEN 
                    DATE(SUBSTR(timestamp, 7, 4) || '-' || SUBSTR(timestamp, 1, 2) || '-' || SUBSTR(timestamp, 4, 2))
                ELSE DATE(timestamp)
            END
        """

        date_clause_daily = ""
        if date_filter == "This Month":
            first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-01")
            date_clause_daily = f"AND {date_expr} >= '{first_of_month}'"
        elif date_filter == "Last 7 Days":
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            date_clause_daily = f"AND {date_expr} >= '{week_ago}'"
        elif date_filter == "Custom":
            date_clause_daily = f"AND {date_expr} >= '{start_date}' AND {date_expr} <= '{end_date}'"
        
        daily_revenue = pd.read_sql_query(f"""
            SELECT 
                {date_expr} as Date,
                ROUND(SUM(amount), 2) as Revenue,
                COUNT(*) as Transactions
            FROM transactions
            WHERE timestamp IS NOT NULL AND timestamp != ''
            AND {date_expr} IS NOT NULL
            {date_clause_daily} {location_clause}
            GROUP BY {date_expr}
            ORDER BY Date
        """, conn)
        
        if not daily_revenue.empty and len(daily_revenue) > 1:
            fig = go.Figure(go.Scatter(
                x=daily_revenue["Date"],
                y=daily_revenue["Revenue"],
                mode='lines+markers',
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(color=COLORS['primary'], size=8),
                hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>"
            ))
            fig = apply_chart_styling(fig, height=320)
            fig.update_layout(
                yaxis=dict(range=[0, 2000], tickformat='$,.0f'),
                hovermode="x unified",
                margin=dict(l=70, r=20, t=10, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for trend chart")
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 4: Revenue vs Items (Bubble) + Revenue by POS
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Revenue vs Items (Bubble)</p>', unsafe_allow_html=True)
            
            product_scatter = pd.read_sql_query(f"""
                SELECT 
                    COALESCE(NULLIF(master_name, ''), product_name_original) as Product,
                    CAST(SUM(quantity) AS INTEGER) as Items,
                    ROUND(SUM(amount), 2) as Revenue
                FROM transactions
                WHERE 1=1 {date_clause} {location_clause}
                GROUP BY Product
                ORDER BY Revenue DESC
                LIMIT 50
            """, conn)
            
            if not product_scatter.empty:
                fig = go.Figure(go.Scatter(
                    x=product_scatter["Items"],
                    y=product_scatter["Revenue"],
                    mode='markers',
                    marker=dict(
                        size=product_scatter["Revenue"].clip(lower=1) ** 0.5,
                        sizemode='area',
                        color=COLORS['primary'],
                        opacity=0.7,
                        line=dict(width=0)
                    ),
                    text=product_scatter["Product"],
                    hovertemplate="<b>%{text}</b><br>Items: %{x}<br>Revenue: $%{y:,.2f}<extra></extra>"
                ))
                fig = apply_chart_styling(fig, height=420)
                fig.update_layout(
                    xaxis=dict(title="Items Sold"),
                    yaxis=dict(title="Revenue ($)"),
                    margin=dict(l=60, r=20, t=10, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Revenue by POS</p>', unsafe_allow_html=True)
            
            pos_revenue = pd.read_sql_query(f"""
                SELECT 
                    source_system as Source,
                    ROUND(SUM(amount), 2) as Revenue
                FROM transactions
                WHERE 1=1 {date_clause} {location_clause}
                GROUP BY source_system
            """, conn)
            
            if not pos_revenue.empty:
                fig = go.Figure(go.Pie(
                    values=pos_revenue["Revenue"],
                    labels=pos_revenue["Source"],
                    hole=0.5,
                    marker=dict(colors=COLORS['discrete'][:len(pos_revenue)]),
                    textinfo='value',
                    texttemplate='$%{value:,.0f}',
                    textfont=dict(color='#0e1112', size=12),
                    insidetextorientation='horizontal',
                    hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>"
                ))
                fig = apply_chart_styling(fig, height=280, show_legend=True)
                fig.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.25,
                        xanchor="center",
                        x=0.5
                    ),
                    margin=dict(l=20, r=20, t=10, b=60)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 5: Profit per Location (full width)
        st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Profit per Location (Known Costs)</p>', unsafe_allow_html=True)
        
        cost_map = load_inventory_costs()
        if cost_map:
            tax_map = load_product_tax_rates()
            margin_by_location = pd.read_sql_query(f"""
                SELECT 
                    machine_name as Machine,
                    COALESCE(NULLIF(master_name, ''), product_name_original) as Product,
                    CAST(quantity AS INTEGER) as Items,
                    ROUND(amount, 2) as Revenue
                FROM transactions
                WHERE machine_name IS NOT NULL AND machine_name != ''
                {date_clause} {location_clause}
            """, conn)
            
            if not margin_by_location.empty:
                margin_by_location = apply_quantity_adjustments(margin_by_location)
                margin_by_location = (
                    margin_by_location.groupby(["Machine", "Product"], as_index=False)
                    .agg({"Adj_Items": "sum", "Revenue": "sum"})
                    .rename(columns={"Adj_Items": "Items"})
                )
                margin_by_location["Location"] = margin_by_location["Machine"].apply(map_location)
                margin_by_location["key"] = margin_by_location["Product"].str.lower().str.strip()
                margin_by_location["Tax_Rate"] = margin_by_location["key"].map(tax_map).fillna(0)
                margin_by_location["Revenue_Net"] = margin_by_location["Revenue"] / (1 + margin_by_location["Tax_Rate"])
                margin_by_location["Unit_Cost"] = margin_by_location["key"].map(cost_map)
                margin_by_location = margin_by_location.dropna(subset=["Unit_Cost"])
                margin_by_location = margin_by_location[margin_by_location["Items"] > 0]
                margin_by_location["Total_Cost"] = margin_by_location["Items"] * margin_by_location["Unit_Cost"]
                margin_by_location["Profit"] = margin_by_location["Revenue_Net"] - margin_by_location["Total_Cost"]

                profit_summary = (
                    margin_by_location.groupby("Location", as_index=False)[["Profit", "Revenue_Net"]]
                    .sum()
                    .sort_values("Profit", ascending=False)
                    .head(15)
                )
                profit_summary["MarginPct"] = (
                    profit_summary["Profit"] / profit_summary["Revenue_Net"].replace(0, pd.NA)
                ) * 100

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=profit_summary["Location"],
                    y=profit_summary["Profit"],
                    name="Profit",
                    marker=dict(color="#00ff88"),
                    text=profit_summary["Location"],
                    textposition="inside",
                    textfont=dict(color="#0a0a0a", size=10),
                    hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.2f}<extra></extra>",
                    yaxis="y"
                ))
                fig.add_trace(go.Scatter(
                    x=profit_summary["Location"],
                    y=profit_summary["MarginPct"],
                    name="Gross Margin %",
                    mode="lines+markers",
                    line=dict(color="#f0f2f6", width=2),
                    marker=dict(color="#f0f2f6", size=6),
                    hovertemplate="<b>%{x}</b><br>Gross Margin: %{y:.1f}%<extra></extra>",
                    yaxis="y2"
                ))

                fig = apply_chart_styling(fig, height=460, show_legend=True)
                fig.update_layout(
                    xaxis=dict(
                        tickangle=-45,
                        tickfont=dict(color="#808495", size=9),
                        ticklabelposition="inside",
                        ticks="inside",
                        ticklabelstandoff=-6,
                        showticklabels=False
                    ),
                    yaxis=dict(
                        side="left",
                        title="Profit ($)",
                        tickformat="$,.0f",
                        tickfont=dict(color="#808495")
                    ),
                    yaxis2=dict(
                        overlaying="y",
                        side="right",
                        title="Gross Margin %",
                        tickformat=".0f",
                        ticksuffix="%",
                        range=[30, 80],
                        showgrid=False,
                        tickfont=dict(color="#808495")
                    ),
                    margin=dict(l=60, r=80, t=20, b=30),
                    legend=dict(
                        x=0.98,
                        y=0.98,
                        xanchor="right",
                        yanchor="top",
                        bgcolor="rgba(0,0,0,0.4)",
                        bordercolor="rgba(255,255,255,0.15)",
                        borderwidth=1,
                        font=dict(size=11, color="#f0f2f6")
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cost data not found to calculate profit per location.")
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 5: Hourly Sales Heatmap (full width)
        st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Hourly Sales Heatmap</p>', unsafe_allow_html=True)
        
        heatmap_df = pd.read_sql_query(
            f"SELECT timestamp, amount, quantity, machine_name FROM transactions WHERE timestamp IS NOT NULL AND timestamp != '' {location_clause}",
            conn
        )
        if not heatmap_df.empty:
            heatmap_df["timestamp_parsed"] = pd.to_datetime(heatmap_df["timestamp"], errors="coerce", infer_datetime_format=True)
            heatmap_df = heatmap_df.dropna(subset=["timestamp_parsed"])
            if date_filter == "This Month":
                heatmap_df = heatmap_df[heatmap_df["timestamp_parsed"] >= pd.to_datetime(first_of_month)]
            elif date_filter == "Last 7 Days":
                heatmap_df = heatmap_df[heatmap_df["timestamp_parsed"] >= pd.to_datetime(week_ago)]
            elif date_filter == "Custom":
                heatmap_df = heatmap_df[
                    (heatmap_df["timestamp_parsed"] >= pd.to_datetime(start_date)) &
                    (heatmap_df["timestamp_parsed"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1))
                ]

            heatmap_df["Hour"] = heatmap_df["timestamp_parsed"].dt.hour
            heatmap_df["Day"] = heatmap_df["timestamp_parsed"].dt.day_name()
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot = heatmap_df.pivot_table(
                index="Day",
                columns="Hour",
                values="amount",
                aggfunc="sum",
                fill_value=0
            ).reindex(day_order)

            if not pivot.empty:
                fig = go.Figure(data=go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns,
                    y=pivot.index,
                    colorscale=[[0, '#0e1112'], [0.5, '#00cc6d'], [1, '#00ff88']],
                    hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Revenue: $%{z:,.2f}<extra></extra>"
                ))
                fig = apply_chart_styling(fig, height=350)
                fig.update_layout(
                    xaxis=dict(title="Hour of Day"),
                    yaxis=dict(title=""),
                    margin=dict(l=80, r=20, t=10, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Row 6: Top Products by Margin + Payment Methods
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Profit per Item Sold</p>', unsafe_allow_html=True)
            
            cost_map = load_inventory_costs()
            if cost_map:
                tax_map = load_product_tax_rates()
                margin_df = pd.read_sql_query(f"""
                    SELECT 
                        COALESCE(NULLIF(master_name, ''), product_name_original) as Product,
                        CAST(quantity AS INTEGER) as Items,
                        ROUND(amount, 2) as Revenue
                    FROM transactions
                    WHERE 1=1 {date_clause} {location_clause}
                """, conn)
                if not margin_df.empty:
                    margin_df = apply_quantity_adjustments(margin_df)
                    margin_df = (
                        margin_df.groupby("Product", as_index=False)
                        .agg({"Adj_Items": "sum", "Revenue": "sum"})
                        .rename(columns={"Adj_Items": "Items"})
                    )
                    margin_df["key"] = margin_df["Product"].str.lower().str.strip()
                    margin_df["Tax_Rate"] = margin_df["key"].map(tax_map).fillna(0)
                    margin_df["Revenue_Net"] = margin_df["Revenue"] / (1 + margin_df["Tax_Rate"])
                    margin_df["key"] = margin_df["Product"].str.lower().str.strip()
                    margin_df["Unit_Cost"] = margin_df["key"].map(cost_map)
                    margin_df = margin_df.dropna(subset=["Unit_Cost"])
                    margin_df = margin_df[margin_df["Items"] > 0]
                    margin_df["Avg_Price"] = margin_df["Revenue_Net"] / margin_df["Items"]
                    margin_df["Unit_Margin"] = margin_df["Avg_Price"] - margin_df["Unit_Cost"]
                    margin_df["Total_Margin"] = margin_df["Unit_Margin"] * margin_df["Items"]
                    margin_df = margin_df.sort_values("Unit_Margin", ascending=False).head(15)

                    fig = go.Figure(go.Bar(
                        x=margin_df["Unit_Margin"],
                        y=margin_df["Product"],
                        orientation='h',
                        marker=dict(
                            color=margin_df["Unit_Margin"],
                            colorscale=[[0, '#008044'], [0.5, '#00cc6d'], [1, '#00ff88']],
                            cornerradius=4
                        ),
                        text=margin_df["Unit_Margin"].apply(lambda x: f"${x:,.2f}"),
                        textposition='inside',
                        textfont=dict(color='#0e1112', size=11, weight='bold'),
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Unit Profit: $%{x:,.2f}<br>"
                            "Avg Price: $%{customdata[0]:,.2f}<br>"
                            "Unit Cost: $%{customdata[1]:,.2f}<br>"
                            "Total Profit: $%{customdata[2]:,.2f}"
                            "<extra></extra>"
                        ),
                        customdata=margin_df[["Avg_Price", "Unit_Cost", "Total_Margin"]],
                    ))
                    fig = apply_chart_styling(fig, height=420)
                    fig.update_layout(
                        yaxis=dict(categoryorder='total ascending', tickfont=dict(color='#808495', size=11)),
                        margin=dict(l=200, r=30, t=10, b=10)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add Unit Cost in the SKU Mapper to enable profit per item.")
        
        with col2:
            st.markdown('<p style="color: #f0f2f6; font-weight: 600; margin-bottom: 0.5rem;">Payment Methods</p>', unsafe_allow_html=True)
            
            payment_methods = pd.read_sql_query(f"""
                SELECT 
                    CASE 
                        WHEN payment_method LIKE '%Cash%' THEN 'Cash'
                        WHEN payment_method = '' OR payment_method IS NULL THEN 'Card'
                        ELSE 'Card'
                    END as Method,
                    COUNT(*) as Transactions,
                    ROUND(SUM(amount), 2) as Revenue
                FROM transactions
                WHERE 1=1 {date_clause} {location_clause}
                GROUP BY Method
            """, conn)
            
            if not payment_methods.empty:
                fig = go.Figure(go.Pie(
                    values=payment_methods["Revenue"],
                    labels=payment_methods["Method"],
                    hole=0.5,
                    marker=dict(colors=[COLORS['primary'], COLORS['tertiary']]),
                    textinfo='value',
                    texttemplate='$%{value:,.0f}',
                    textfont=dict(color='#0e1112', size=12),
                    textposition='inside',
                    insidetextorientation='horizontal',
                    hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>"
                ))
                fig = apply_chart_styling(fig, height=260, show_legend=True)
                fig.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.35,
                        xanchor="center",
                        x=0.5
                    ),
                    margin=dict(l=30, r=30, t=10, b=60),
                    uniformtext_minsize=10,
                    uniformtext_mode="hide"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                payment_table = payment_methods.copy()
                payment_table["Revenue"] = payment_table["Revenue"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(payment_table[["Method", "Revenue"]], hide_index=True, use_container_width=True)
        
        conn.close()
    else:
        conn.close()
        st.markdown("""
        <div class="metric-card" style="text-align: center; padding: 3rem;">
            <h3 style="margin-bottom: 1rem;">No Data Yet</h3>
            <p style="color: #808495;">Go to <strong>Upload Data</strong> to import your POS exports.</p>
        </div>
        """, unsafe_allow_html=True)
