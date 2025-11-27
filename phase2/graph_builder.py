import os
import json
import pandas as pd
import numpy as np
from googleapiclient.discovert import build
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = "data"
GRAPH_FILE_PATH = os.path.join(DATA_DIR, "graph_data.json")

# Select a set of example people to make a graph
# of first, then implement a live model.
# Mix contains Gaming, Commentary, Politics
EXAMPLE_PEOPLE = {
    "PewDiePie": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
    "MrBeast": "UCX6OQ3DkcsbYNE6H8uQQuVA",
    "Markiplier": "UC7_YxT-KID8kRbqZo7MyscQ",
    "Jacksepticeye": "UChGJGhZ9SOOHvBB0Y4DOO_w",
    "HasanAbi": "UCtoaZpBnrd0lhycxYJ4MNOQ",
    "xQc": "UCmDTrq0LNgPodDOFZiSbsww",
    "Ludwig": "UCrPseYLGpNygVi34QpGNqpA",
    "MoistCr1TiKaL": "UCq6VFHwMzcMXbuKyG7SQYIg",
    "H3 Podcast": "UCLtREJY21xRfCuEKvdki1Kw",
    "Marques Brownlee": "UCBJycsmduvYl917o249m0vQ",  # Tech (Control group)
    "Anthony Fantano": "UCt7fwAhXDy3oNFTAzF2o8Pw", # Music (Control group)
    "Destiny": "UC554eY5jNUfDq3yDOJYirOQ",
    "Vaush": "UC1E-JS8L0j1Ei70D9VEx98w",
    "Kai Cenat": "UCqXLjvpUhqI1kwbS2855_7A",
    "IShowSpeed": "UCjC3ZVqS3y9QvFp_1WjF1-A",
    "The Majority Report": "UC-3jIAlnQmbbVMV6gR7K8aQ",
}
# --- Helper Functions ---

def setup_youtube_client():
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("Missing YOUTUBE_API_KEY in .env file.")
    return build('youtube', 'v3', developerKey=api_key)

def fetch_channel_details(youtube, channel_ids):
    """
    Fetches snippet (title, description, thumbnails) for a list of channel IDs.
    """
    print(f"Fetching details for {len(channel_ids)} channels...")
    
    # The API accepts a comma-separated string of IDs
    ids_string = ",".join(channel_ids)
    
    request = youtube.channels().list(
        part="snippet,statistics",
        id=ids_string
    )
    response = request.execute()
    
    channels_data = []
    for item in response['items']:
        channels_data.append({
            "id": item['id'],
            "title": item['snippet']['title'],
            "description": item['snippet']['description'],
            "thumbnail": item['snippet']['thumbnails']['default']['url'],
            "subscribers": item['statistics']['subscriberCount']
        })
    return channels_data

def build_graph():
    """
    Main execution flow:
    1. Fetch Channel Data
    2. Generate Embeddings for Descriptions
    3. Calculate Similarity
    4. Save Nodes and Edges to JSON
    """
    print("--- Starting Graph Builder ---")
    
    # 1. Fetch Data
    youtube = setup_youtube_client()
    # Convert our dict values to a list of IDs
    target_ids = list(CREATOR_IDS.values())
    
    # API Hack: If list > 50, you need to batch. We have ~13, so one call is fine.
    channels = fetch_channel_details(youtube, target_ids)
    
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
    build_graph()