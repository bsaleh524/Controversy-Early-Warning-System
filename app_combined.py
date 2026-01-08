import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="Youtube Galaxy",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATA_DIR = Path("data")
ANALYZED_CSV_PATH = DATA_DIR / "analyzed_data.csv"
# Using the UMAP path from your snippet
STARMAP_CSV_PATH = DATA_DIR / "processed/plotly/starmap_data_tsne_trimmed_120_labeled.csv"

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
    if 'youtube_url' not in df.columns:
        df['youtube_url'] = ""
    df['youtube_url'] = df['youtube_url'].fillna("")
    return df

# --- Components ---

# def render_gauge(value):
#     fig = go.Figure(go.Indicator(
#         mode = "gauge+number",
#         value = value,
#         domain = {'x': [0, 1], 'y': [0, 1]},
#         title = {'text': "Negative Sentiment %"},
#         gauge = {
#             'axis': {'range': [None, 100]},
#             'bar': {'color': "#FF4B4B"}, 
#             'bgcolor': "white",
#             'borderwidth': 2,
#             'bordercolor': "gray",
#             'steps': [
#                 {'range': [0, 30], 'color': "#e6f9e6"},
#                 {'range': [30, 70], 'color': "#fff8e6"},
#                 {'range': [70, 100], 'color': "#ffe6e6"}
#             ],
#         }
#     ))
#     fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
#     st.plotly_chart(fig, width='stretch')

# def render_scandal_dashboard(df):
#     st.subheader("High-Level Summary: Hasan 'Shock Collar' Incident")
#     total_comments = len(df)
#     sentiment_counts = df['sentiment'].value_counts()
#     total_negative = sentiment_counts.get('Negative', 0)
#     neg_percentage = (total_negative / total_comments) * 100 if total_comments > 0 else 0

#     col_gauge, col_stats = st.columns([1, 2])
#     with col_gauge:
#         st.write("### Scandal Score")
#         render_gauge(neg_percentage)
#     with col_stats:
#         st.write("### Sentiment Breakdown")
#         c1, c2, c3 = st.columns(3)
#         c1.metric("Negative", f"{total_negative:,}", delta="Alert" if neg_percentage > 50 else None, delta_color="inverse")
#         c2.metric("Positive", f"{sentiment_counts.get('Positive', 0):,}")
#         c3.metric("Neutral", f"{sentiment_counts.get('Neutral', 0):,}")

#     st.divider()
#     st.subheader("Receipts: Top Negative Keywords")
#     negative_comments = df[df['sentiment'] == 'Negative']
#     if not negative_comments.empty:
#         keyword_counts = negative_comments['keywords'].str.split(', ').explode().value_counts()
#         st.dataframe(keyword_counts.head(15), width='stretch', column_config={"count": "Frequency"})
#     else:
#         st.info("No negative keywords found.")

def render_starmap(df):
    """Tab 2: The Creator Galaxy (3D)"""
    st.subheader("The Creator Galaxy (3D Star Map)")
    
    # Create a copy so we don't mutate the cached dataframe
    df = df.copy()
    
    col_map, col_info = st.columns([3, 1])
    
    # Placeholder for logic sharing
    list_selected_creator_title = None

    with col_map:
        # --- Filters ---
        c1, c2 = st.columns([1, 1])
        with c1:
            search_query = st.text_input("🔍 Find a Creator", "")
        with c2:
            # Get unique clusters for the dropdown
            if 'cluster_name' in df.columns:
                clusters = sorted(df['cluster_name'].unique())
                cluster_options = ["All"] + [str(c) for c in clusters]
            else:
                clusters = []
                cluster_options = ["All"]
            selected_cluster = st.selectbox("🎨 Highlight Group", cluster_options)

    # --- LIST SELECTION LOGIC (Sidebar) ---
    # We render this BEFORE the map logic so the selection can influence the map colors
    with col_info:
        if selected_cluster != "All":
            st.markdown(f"**Members of '{selected_cluster}'**")
            st.caption("Select one to highlight")
            
            # Filter for the list
            cluster_df = df[df['cluster_name'].astype(str) == selected_cluster].sort_values('title')
            
            # Show list with selection enabled
            selection = st.dataframe(
                cluster_df[['title']], 
                hide_index=True, 
                width='stretch',
                on_select="rerun",
                selection_mode="single-row",
                key=f"list_{selected_cluster}" # Resets selection if you change category
            )
            
            # Capture the selection
            if selection and selection.selection.rows:
                idx = selection.selection.rows[0]
                list_selected_creator_title = cluster_df.iloc[idx]['title']

    # --- MAP LOGIC ---
    with col_map:
        # 1. Base State
        df['color_group'] = df['cluster_name'].astype(str)
        df['size'] = 3 # Default size
        
        # 2. Colors
        palette = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
        cluster_color_map = {str(c): palette[i % len(palette)] for i, c in enumerate(clusters)}
        cluster_color_map['Match'] = '#FF0000'     # Bright Red for Search/Selection
        cluster_color_map['Background'] = '#222222' # Dark Gray for Dimmed items

        if selected_cluster != "All":
            # Identify rows that do NOT match the selection
            mask_unselected = df['cluster_name'].astype(str) != selected_cluster
            
            # "Turn small" and gray out the unselected
            df.loc[mask_unselected, 'size'] = 1
            df.loc[mask_unselected, 'color_group'] = 'Background'
            
            # Highlight selected cluster
            mask_selected = df['cluster_name'].astype(str) == selected_cluster
            df.loc[mask_selected, 'size'] = 15

        # 3. Apply Search OR List Selection Highlight (Overrides Cluster logic)
        mask_search = pd.Series(False, index=df.index)
        mask_list = pd.Series(False, index=df.index)

        # Check Search
        if search_query:
            mask_search = df['title'].str.contains(search_query, case=False, na=False)
        
        # Check List Selection
        if list_selected_creator_title:
            mask_list = df['title'] == list_selected_creator_title

        # Combine Matches
        final_match_mask = mask_search | mask_list

        if final_match_mask.any():
            df.loc[final_match_mask, 'color_group'] = 'Match' 
            df.loc[final_match_mask, 'size'] = 20 # Super big
            
            if search_query:
                st.success(f"Found {mask_search.sum()} matches!")
        
        # 4. Render Chart
        fig = px.scatter_3d(
            df, 
            x='x', 
            y='y', 
            z='z',
            color='color_group',
            hover_name='title',
            hover_data={
                'description': False, 'cluster_name': False, 
                'x': False, 'y': False, 'z': False, 
                'color_group': False, 'size': False
            },
            custom_data=['thumbnail', 'description', 'title', 'youtube_url'],
            size='size',
            size_max=14,
            opacity=0.7,
            color_discrete_map=cluster_color_map,
            title="Creator Semantic Clusters (3D)"
        )
        
        fig.update_layout(
            height=800, 
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='#0e1117'
            ),
            paper_bgcolor='#0e1117',
            font=dict(color="white"),
            showlegend=True,
            legend=dict(itemsizing='constant'),
            margin=dict(l=0, r=0, t=30, b=0),
            clickmode='event+select'
        )
        
        selected_points = st.plotly_chart(fig, width='stretch', on_select="rerun")

    # --- INFO PANEL (DETAILS) ---
    with col_info:
        st.markdown("---") # Separator between list and details
        
        target_row = None
        
        # Priority Logic:
        # 1. List Selection (Specific drill-down)
        if list_selected_creator_title:
             target_row = df[df['title'] == list_selected_creator_title].iloc[0]
        
        # 2. Map Click (Visual exploration)
        # Note: If List is selected, it takes priority unless deselecting list.
        elif selected_points and selected_points['selection']['points']:
            point_index = selected_points['selection']['points'][0]['point_index']
            target_row = df.iloc[point_index]

        # 3. Search Query (Text search)
        elif search_query and mask_search.any():
            target_row = df[mask_search].iloc[0]

        if target_row is not None:
            # --- 1. Basic Details ---
            if pd.notna(target_row['thumbnail']) and str(target_row['thumbnail']).startswith('http'):
                st.image(target_row['thumbnail'], width=150)
            
            st.markdown(f"### {target_row['title']}")
            
            yt_url = str(target_row['youtube_url']).strip()
            if yt_url and yt_url.startswith('http'):
                st.markdown(f"**[📺 Visit YouTube Channel]({yt_url})**")
            
            st.caption(f"Cluster Group: {target_row['cluster_name']}")
            st.markdown("---")
            
            # --- 2. Truncated Description ---
            st.markdown("**Bio Preview:**")
            desc = str(target_row['description'])
            if len(desc) > 300:
                desc = desc[:300] + "..."
            st.write(desc)
            
            st.markdown("---")
            
            # --- 3. Nearest Neighbors Logic ---
            st.markdown("#### 🔭 Closest Creators")
            
            tx, ty, tz = target_row['x'], target_row['y'], target_row['z']
            
            # Calculate Distance
            distances = np.sqrt(
                (df['x'] - tx)**2 + 
                (df['y'] - ty)**2 + 
                (df['z'] - tz)**2
            )
            
            df_neighbors = df.copy()
            df_neighbors['distance'] = distances
            
            # Filter self and get top 5
            closest_df = df_neighbors[df_neighbors['distance'] > 0.0001].nsmallest(5, 'distance')
            
            st.dataframe(
                closest_df[['title', 'cluster_name']],
                column_config={
                    "title": "Creator",
                    "cluster_name": "Group",
                },
                hide_index=True,
                width='stretch'
            )
        else:
             if selected_cluster == "All":
                 st.info("Search for a creator or select category to find a creator")

# --- Main ---
def main():
    st.title("🌌 Youtube Galaxy")
    st.markdown("""
    Explore the vast universe of YouTube creators clustered by content similarity.
    Use the search box or highlight specific groups to discover creators and their connections.
    """)
    tab2 = st.tabs(["Galaxy"])

    # with tab1:
    #     df = load_scandal_data(ANALYZED_CSV_PATH)
    #     if df is not None: render_scandal_dashboard(df)
    #     else: st.warning(f"No scandal data found at {ANALYZED_CSV_PATH}. Run Phase 1 pipeline.")

    # with tab2:
    df_map = load_starmap_data(STARMAP_CSV_PATH)
    if df_map is not None: 
        if 'z' not in df_map.columns:
            st.error("⚠️ Data is 2D. Please run `python src/starmap_builder.py` to regenerate 3D data.")
        else:
            render_starmap(df_map)
    else: 
        st.warning(f"No star map data found at {STARMAP_CSV_PATH}. Run 'src/starmap_builder.py'.")

if __name__ == "__main__":
    main()