import os
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
# Do three components,(x,y,x)
# Do tsne for 3 components
# Ensure plotter properly grabs thumbnail
# --- Configuration ---
DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "fandom", "youtubers_data_combined.json")

def build_starmap():
    """
    1. Loads scraped data.
    2. Generates embeddings.
    3. Clusters data into 'Genres' (K-Means).
    4. Projects to 2D (t-SNE).
    5. Saves as a lightweight CSV for the App.
    """
    print("--- Starting Star Map Builder ---")

    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        creators = json.load(f)
    
    print(f"Loaded {len(creators)} creators.")
    if len(creators) < 5:
        print("Not enough data to build a map. Need at least 5 creators.")
        return

    # 2. Generate Embeddings
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Generating embeddings (this may take a moment)...")
    # Combine Title + Description for rich context
    # text_corpus = [f"{c['title']} - {c['description'].replace('\n', ' ')}" for c in creators]
    text_corpus = []
    for c in creators:
        cleaned_description = c['description'].replace('\n', ' ')[:3000]
        text_corpus.append(f"{c['title']} - {cleaned_description}")

    embeddings = model.encode(text_corpus, show_progress_bar=True)

    # 3. Clustering (The "Genre" Detector)
    # We arbitrary pick 15 clusters. In a real app, you might optimize this.
    print("Clustering creators into genres...")
    num_clusters = 60 #25 #15 # Safety check for small datasets
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)

    # 4. Dimensionality Reduction (The "Map" Maker)
    print("Projecting to 3D space...")
    
    # Dynamic perplexity to avoid crashes on small data
    n_samples = len(embeddings)

    perplexity_val = min(30, max(2, n_samples - 1))
    tsne = TSNE(
        n_components=3, 
        perplexity=perplexity_val, 
        random_state=42, 
        init='pca', 
        learning_rate='auto'
    )
    coords = tsne.fit_transform(embeddings)

    # mds = MDS(n_components=3, dissimilarity="precomputed", random_state=42)
    # similarity_matrix = cosine_similarity(embeddings)
    # distance_matrix = 1 - similarity_matrix  # Convert similarity to distance
    # coords_mds = mds.fit_transform(distance_matrix)


    # 5. Build DataFrame & Save
    print("Saving Star Map data...")
    
    df = pd.DataFrame({
        'id': [c['id'] for c in creators],
        'title': [c['title'] for c in creators],
        'description': [c['description'] + "..." for c in creators], # Truncate for CSV
        'thumbnail': [c.get('thumbnail', '') for c in creators],
        'youtube_url': [c.get('youtube_url', '') for c in creators],
        'cluster_id': clusters,
        'x': coords[:, 0],
        'y': coords[:, 1],
        'z': coords[:, 2],
    })

    # Sort by cluster for cleaner legend
    df.sort_values('cluster_id', inplace=True)
    output_file = os.path.join(DATA_DIR, "processed", "plotly", f"starmap_data_tsne_{num_clusters}.csv")

    df.to_csv(output_file, index=False)
    print(f"Done! Saved {len(df)} nodes to {output_file}")

if __name__ == "__main__":
    build_starmap()