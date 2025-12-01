import os
import json
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.youtube import setup_youtube_client, fetch_channel_details
from utils.scraper import load_channel_info

DATA_DIR = "data"
GRAPH_FILE_PATH = os.path.join(DATA_DIR, "graph_data.json")

def build_graph(yt_client):
    """
    Main execution flow:
    1. Fetch Channel Data
    2. Generate Embeddings for Descriptions
    3. Calculate Similarity
    4. Save Nodes and Edges to JSON
    """
    print("--- Starting Graph Builder ---")
    
    # 1. Fetch Data
    yt_client = setup_youtube_client()
    target_ids = load_channel_info(DATA_DIR)

    channels_data = fetch_channel_details(yt_client, target_ids)
    
    # Convert our dict values to a list of IDs
    target_ids = list(channels_data.values())
    
    # API Hack: If list > 50, you need to batch. We have ~13, so one call is fine.
    channels = fetch_channel_details(yt_client, target_ids)
    
    # 2. Generate Embeddings
    print("Loading embedding model (this runs locally)...")
    # We use a small, fast model for semantic similarity
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    descriptions = [ch['description'] for ch in channels]
    print("Generating embeddings for channel descriptions...")
    embeddings = model.encode(descriptions)
    
    # 3. Calculate Cosine Similarity Matrix
    print("Calculating relationships...")
    similarity_matrix = cosine_similarity(embeddings)
    
    # 4. Construct the Graph Structure (Nodes & Edges)
    nodes = []
    edges = []
    
    # Create Nodes
    for ch in channels:
        nodes.append({
            "id": ch['id'],
            "label": ch['title'],
            "image": ch['thumbnail'], # For showing their avatar in the graph
            "shape": "circularImage", # Style for streamlit-agraph
            "subscribers": ch['subscribers']
        })
        
    # Create Edges based on threshold
    # We only draw a line if similarity is > 0.5 (Adjust this to make graph denser/sparser)
    SIMILARITY_THRESHOLD = 0.45 
    
    for i in range(len(channels)):
        for j in range(i + 1, len(channels)): # Avoid duplicates (A-B is same as B-A)
            score = float(similarity_matrix[i][j])
            
            if score > SIMILARITY_THRESHOLD:
                edges.append({
                    "source": channels[i]['id'],
                    "target": channels[j]['id'],
                    "weight": score, # Store the strength of the link
                    "label": f"{score:.2f}" # Optional: show score on line
                })

    # 5. Save to JSON
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
    build_graph(yt_client)