import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

DATA_DIR = Path("data")
ANALYZED_CSV_PATH = DATA_DIR / "analyzed_data.csv"

# Setup overall page configuration
st.set_page_config(
    page_title="Controversy Early Warning System V1",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_data(filepath):
    """Load analyzed CSV data, return a dataframe
    for streamlit."""

    if not filepath.exists():
        st.error(f"Analyzed file not present in path {ANALYZED_CSV_PATH}")
        return None
    
    return pd.read_csv(filepath)

def main():
    st.title("⚠️ Controversy Early Warning System Dashboard")

if __name__ == "__main__":
    main()