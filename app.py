import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Smart Vending ATX Dashboard",
    page_icon="🏢",
    layout="wide"
)

# Title
st.title("🏢 Smart Vending ATX Dashboard")
st.markdown("---")

# Placeholder content
st.info("✨ Dashboard is being built! Check back soon.")

# Sample metrics (placeholder)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue", "$0.00", "0%")
with col2:
    st.metric("Total Transactions", "0", "0")
with col3:
    st.metric("Avg Transaction", "$0.00", "0%")
