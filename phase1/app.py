import streamlit as st
import pandas as pd
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



# --- Data Loading ---
@st.cache_data  # <-- Caching ensures we only load data once
def load_data(filepath):
    """Load analyzed CSV data, return a dataframe
    for streamlit."""

    if not filepath.exists():
        st.error(f"Analyzed file not present in path {filepath}")
        return None
    
    return pd.read_csv(filepath)
    
    df = pd.read_csv(filepath)
    
    # CRITICAL: Convert timestamp string to a real datetime object
    # We use errors='coerce' to handle any bad data
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
    
    # Drop any rows that failed timestamp conversion
    df.dropna(subset=['timestamp_utc'], inplace=True)
    
    return df

# --- Main Application ---
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
        st.stop() # Stop the app from running further

    # High Level View
    total_comments = len(df)
    sentiment_counts = df['sentiment_label'].value_counts()
    
    total_negative = sentiment_counts.get('Negative', 0)
    total_positive = sentiment_counts.get('Positive', 0)
    total_neutral = sentiment_counts.get('Neutral', 0)
    
    # Calculate the meter score
    neg_percentage = (total_negative / total_comments) * 100 if total_comments > 0 else 0

    # --- 1. The "Scandal-O-Meter" ---
    st.header("'Scandal-O-Meter")
    st.write("This score is the percentage of all analyzed comments that were flagged as 'Negative'.")
    
    # We use st.gauge to create a "speedometer" dial
    st.gauge(
        value=neg_percentage,
        min_value=0,
        max_value=100,
        label="Negative Sentiment %",
        format_string=f"{neg_percentage:.1f}%"
    )

    # --- 2. High-Level Sentiment Counts ---
    st.header("Sentiment Breakdown")
    
    # Use columns for a clean KPI layout
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Comments", f"{total_comments:,}")
    col2.metric("Negative", f"{total_negative:,}")
    col3.metric("Positive", f"{total_positive:,}")
    col4.metric("Neutral", f"{total_neutral:,}")

    # --- 3. Top Negative Keywords ---
    st.header("🧾 Top Negative Keywords")
    st.write("Most common phrases extracted from all 'Negative' YT comments.")
    
    # Get all negative comments
    negative_comments = df[df['sentiment_label'] == 'Negative']
    
    # Split keywords and count them
    keyword_counts = negative_comments['keywords'].str.split(', ').explode().value_counts()
    
    # Filter out empty strings (from comments with no keywords)
    keyword_counts = keyword_counts[keyword_counts.index != '']
    
    # Display the top 20 keywords in a simple table
    st.dataframe(
        keyword_counts.head(20), 
        column_config={"index": "Keyword", "value": "Count"},
        use_container_width=True
    )

if __name__ == "__main__":
    main()