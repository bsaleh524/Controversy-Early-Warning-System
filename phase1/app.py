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
        st.error(f"Analyzed file not present in path {filepath}")
        return None
    
    return pd.read_csv(filepath)

def main():
    st.title("⚠️ Controversy Early Warning System Dashboard")
    st.subheader("First version of project, using Hasan Piker's Dog Collar Incident of June 2024")
    st.markdown("""
    This dashboard presents the results of the first version of the
    Controversy Early Warning System (CEWS) pipeline. The pipeline scrapes
    YouTube comments from selected videos and analyzes them using local
    machine learning models for:
    * Sentiment Analysis.
    * Keyword Extraction.
    """
    )

    # Load data
    df = load_data(ANALYZED_CSV_PATH)

    if df is None:
        st.error(
            f"Data not found in path: {ANALYZED_CSV_PATH}"
            "Please rerun offline pipeline."
        )
        st.stop()
    
    # High Level view
    st.header("High Level Overview")
    st.markdown("Sentiment Summary:\n"
                
          f"Positive: {len(df[df['sentiment_label']=='Positive'])}\n"
          f"Neutral: {len(df[df['sentiment_label']=='Neutral'])}\n"
          f"Negative: {len(df[df['sentiment_label']=='Negative'])}\n")
    

if __name__ == "__main__":
    main()