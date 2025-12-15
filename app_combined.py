import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="Controversy Early Warning System",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATA_DIR = Path("data")
# Note: Ensure you run the pipeline to generate these files!
ANALYZED_CSV_PATH = DATA_DIR / "analyzed_data.csv"
STARMAP_CSV_PATH = DATA_DIR / "plotly/starmap_data_3.csv"

# --- Data Loading ---
# @st.cache_data
# def load_scandal_data(filepath):
#     if not filepath.exists(): return None
#     df = pd.read_csv(filepath)
#     df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
#     df.dropna(subset=['timestamp_utc'], inplace=True)
#     return df

@st.cache_data
def load_starmap_data(filepath):
    if not filepath.exists(): return None
    df = pd.read_csv(filepath)
    # Ensure youtube_url is string and handle NaNs
    if 'youtube_url' not in df.columns:
        df['youtube_url'] = ""
    df['youtube_url'] = df['youtube_url'].fillna("")
    return df

# --- Components ---

def render_gauge(value):
    """Renders a Gauge Chart using Plotly"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Negative Sentiment %"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#FF4B4B"}, # Streamlit Red
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': "#e6f9e6"}, # Greenish
                {'range': [30, 70], 'color': "#fff8e6"}, # Yellowish
                {'range': [70, 100], 'color': "#ffe6e6"} # Reddish
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width='stretch')

def render_scandal_dashboard(df):
    """Tab 1: Sentiment Analysis"""
    st.subheader("High-Level Summary: Hasan 'Shock Collar' Incident")
    
    total_comments = len(df)
    sentiment_counts = df['sentiment'].value_counts()
    total_negative = sentiment_counts.get('Negative', 0)
    neg_percentage = (total_negative / total_comments) * 100 if total_comments > 0 else 0

    col_gauge, col_stats = st.columns([1, 2])
    
    with col_gauge:
        st.write("### Scandal Score")
        render_gauge(neg_percentage)
        
    with col_stats:
        st.write("### Sentiment Breakdown")
        # Custom CSS metrics for better look
        c1, c2, c3 = st.columns(3)
        c1.metric("Negative", f"{total_negative:,}", delta="Alert" if neg_percentage > 50 else None, delta_color="inverse")
        c2.metric("Positive", f"{sentiment_counts.get('Positive', 0):,}")
        c3.metric("Neutral", f"{sentiment_counts.get('Neutral', 0):,}")

    st.divider()
    st.subheader("Receipts: Top Negative Keywords")
    
    negative_comments = df[df['sentiment'] == 'Negative']
    if not negative_comments.empty:
        keyword_counts = negative_comments['keywords'].str.split(', ').explode().value_counts()
        st.dataframe(keyword_counts.head(15), width='stretch', column_config={"count": "Frequency"})
    else:
        st.info("No negative keywords found.")

def render_starmap(df):
    """Tab 2: The Creator Galaxy (3D)"""
    st.subheader("The Creator Galaxy (3D Star Map)")
    
    col_map, col_info = st.columns([3, 1])
    
    with col_map:
        search_query = st.text_input("🔍 Find a Creator (e.g. 'Markiplier', 'Ludwig')", "")
        
        # Data Prep
        df['color_group'] = df['cluster_id'].astype(str)
        df['size'] = 5 # Default size smaller for 3D density
        
        if search_query:
            mask = df['title'].str.contains(search_query, case=False, na=False)
            if mask.any():
                df.loc[mask, 'color_group'] = 'Match' 
                df.loc[mask, 'size'] = 20 # Highlight size
                st.success(f"Found {mask.sum()} matches! (Look for Red Stars)")
            else:
                st.warning("No matches found.")

        # --- 3D SCATTER PLOT ---
        fig = px.scatter_3d(
            df, 
            x='x', 
            y='y', 
            z='z',
            color='color_group',
            hover_name='title',
            hover_data={'description': False, 'cluster_id': True, 'x': False, 'y': False, 'z': False, 'color_group': True},
            custom_data=['thumbnail', 'description', 'title', 'youtube_url'],
            size='size',
            size_max=20,
            opacity=0.7, # Transparency helps see depth
            color_discrete_map={'Match': '#FF0000'}, 
            title="Creator Semantic Clusters (3D)"
        )
        
        fig.update_layout(
            height=800, 
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='#0e1117' # Match Streamlit dark theme
            ),
            paper_bgcolor='#0e1117',
            font=dict(color="white"),
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        
        # Render
        selected_points = st.plotly_chart(fig, width='stretch', on_select="rerun")

    # Info Panel
    with col_info:
        st.info("👆 Click on a star to see details.")
        
        target_row = None
        
        if selected_points and selected_points['selection']['points']:
            point_index = selected_points['selection']['points'][0]['point_index']
            target_row = df.iloc[point_index]
        elif search_query and df['color_group'].eq('Match').any():
            target_row = df[df['color_group'] == 'Match'].iloc[0]

        if target_row is not None:
            if pd.notna(target_row['thumbnail']) and str(target_row['thumbnail']).startswith('http'):
                st.image(target_row['thumbnail'], width=150)
            
            st.markdown(f"### {target_row['title']}")
            
            yt_url = str(target_row['youtube_url']).strip()
            if yt_url and yt_url.startswith('http'):
                st.markdown(f"**[📺 Visit YouTube Channel]({yt_url})**")
            
            st.caption(f"Cluster Group: {target_row['cluster_id']}")
            st.markdown("---")
            st.markdown("**Bio Preview:**")
            st.write(target_row['description'])

# --- Main ---
def main():
    st.title("📉 Controversy Early Warning System")
    tab1, tab2 = st.tabs(["🔥 Scandal-O-Meter", "🌌 Creator Galaxy"])

    # with tab1:
    #     df = load_scandal_data(ANALYZED_CSV_PATH)
    #     if df is not None: render_scandal_dashboard(df)
    #     else: st.warning(f"No scandal data found at {ANALYZED_CSV_PATH}. Run Phase 1 pipeline.")

    with tab2:
        df_map = load_starmap_data(STARMAP_CSV_PATH)
        # Check if Z axis exists (in case user runs old pipeline)
        if df_map is not None: 
            if 'z' not in df_map.columns:
                st.error("⚠️ Data is 2D. Please run `python src/starmap_builder.py` to regenerate 3D data.")
            else:
                render_starmap(df_map)
        else: 
            st.warning(f"No star map data found at {STARMAP_CSV_PATH}. Run 'src/starmap_builder.py'.")

if __name__ == "__main__":
    main()