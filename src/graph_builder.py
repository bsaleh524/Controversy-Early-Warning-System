import os
import json
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import MDS, TSNE
from utils.youtube import setup_youtube_client, fetch_batch_channel_details, fetch_recent_video_titles
from utils.scraper import load_channel_info

DATA_DIR = "data"
YAML_DIR = "yamls"
GRAPH_FILE_PATH = os.path.join(DATA_DIR, "graph_data.json")

def build_graph(yt_client, rich_data_file=None):
    """
    Main execution flow:
    1. Fetch Channel Data
    2. Generate Embeddings for Descriptions
    3. Calculate 2D Coordinates (MDS) for Plotting
    4. Calculate Similarity Edges
    5. Save Nodes (with x,y) and Edges to JSON
    """
    print("--- Starting Graph Builder ---")
    
    channels = []
    
    # 1. Try to load from cache first
    if rich_data_file and os.path.exists(rich_data_file):
        print(f"Loading cached rich data from {rich_data_file}...")
        with open(rich_data_file, "r") as f:
            channels = json.load(f)
    else:
        # --- Fetch Fresh Data ---
        print("Cache not found or not used. Fetching fresh data from YouTube API...")
        
        channel_info_dict = load_channel_info(YAML_DIR)
        target_ids = list(channel_info_dict.values())
        
        # Fetch details (Batch call)
        print(f"Fetching details for {len(target_ids)} channels...")
        channels = fetch_batch_channel_details(yt_client, target_ids)
        
        # Enrich with Video Titles
        print("Fetching recent video titles to improve embeddings...")
        
        for ch in channels:
            # Fetch last 10 videos for this specific channel
            video_titles = fetch_recent_video_titles(yt_client, ch['uploads_playlist_id'], limit=10)
            
            # Combine them into a single string
            titles_string = ", ".join(video_titles)
            
            # Create the "Rich Text" for the embedding model
            rich_text = f"{ch['title']} - {ch['description']}. Recent Videos: {titles_string}"
            
            # Store it in the channel dict so we can save it
            ch['rich_text'] = rich_text
            print(f"  -> Enriched {ch['title']} with {len(video_titles)} titles.")

        # Save the rich data if a file path was provided
        if rich_data_file:
            print(f"Saving rich data to {rich_data_file}...")
            with open(rich_data_file, "w") as f:
                json.dump(channels, f, indent=2)

    # 2. Generate Embeddings
    print("Loading embedding model (this runs locally)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings for enriched channel data...")
    # Extract the rich text from our channel list
    rich_descriptions = [ch['rich_text'] for ch in channels]
    embeddings = model.encode(rich_descriptions)
    
    # 3. Calculate Cosine Similarity Matrix
    print("Calculating relationships...")
    similarity_matrix = cosine_similarity(embeddings)
    distance_matrix = 1 - similarity_matrix  # Convert similarity to distance

    # Use MDS to project high-dimensional embeddings to 2D x,y coordinates
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42)
    # tsne = TSNE(n_components=2, random_state=42)
    coords_mds = mds.fit_transform(distance_matrix)
    # coords_tsne = tsne.fit_transform(embeddings)
    
    # 5. Construct Graph
    nodes = []
    edges = []
    
    for i, ch in enumerate(channels):
        nodes.append({
            "id": ch['id'],
            "label": ch['title'],
            "image": ch['thumbnail'],
            "subscribers": ch['subscribers'],
            # Scale coordinates slightly for better visualization spread
            "x": float(coords_mds[i][0]) * 100, 
            "y": float(coords_mds[i][1]) * 100,
            "shape": "circularImage"
        })
        
    SIMILARITY_THRESHOLD = 0.45 
    
    for i in range(len(channels)):
        for j in range(i + 1, len(channels)):
            score = float(similarity_matrix[i][j])
            if score > SIMILARITY_THRESHOLD:
                edges.append({
                    "source": channels[i]['id'],
                    "target": channels[j]['id'],
                    "weight": score,
                    "label": f"{score:.2f}"
                })

    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GRAPH_FILE_PATH, 'w') as f:
        json.dump(graph_data, f, indent=2)
        
    print(f"Graph built! {len(nodes)} nodes and {len(edges)} edges.")
    print(f"Saved to {GRAPH_FILE_PATH}")

if __name__ == "__main__":
    yt_client = setup_youtube_client()
    # Define a default path for the rich data cache
    CACHE_FILE = os.path.join(DATA_DIR, "rich_channel_data.json")
    build_graph(yt_client, rich_data_file=CACHE_FILE)