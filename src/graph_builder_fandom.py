import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE

# --- Configuration ---
DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "youtubers_data.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "fandom_graph_data.json")

def build_fandom_graph():
    """
    Builds a semantic graph from scraped Fandom data.
    """
    print("--- Starting Fandom Graph Builder ---")

    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run 'src/fandom_scraper.py' first.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        creators = json.load(f)
    
    print(f"Loaded {len(creators)} creators from {INPUT_FILE}")

    if not creators:
        print("No creators found in data. Exiting.")
        return

    # 2. Generate Embeddings
    print("Loading embedding model (local)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Generating embeddings from Fandom bios...")
    # We combine Title + Description to ensure the model knows WHO it is + WHAT they do.
    # We strip newlines to keep the input clean for the model.
    text_corpus = []
    for c in creators:
        cleaned_description = c['description'].replace('\n', ' ')
        text_corpus.append(f"{c['title']} - {cleaned_description}")
    
    embeddings = model.encode(text_corpus)

    # 3. Calculate Similarity & Coordinates
    print("Calculating relationships...")
    
    # Cosine Similarity for Edges
    similarity_matrix = cosine_similarity(embeddings)
    
    # t-SNE for 2D Layout (Nodes)
    n_samples = len(embeddings)
    # Dynamic perplexity: must be < n_samples. 
    # 30 is default, but for small datasets (<50), 2-5 is better.
    perplexity_val = min(5, max(1, n_samples - 1))
    
    print(f"Projecting to 2D using t-SNE (perplexity={perplexity_val})...")
    tsne = TSNE(
        n_components=2, 
        perplexity=perplexity_val, 
        random_state=42, 
        init='pca', 
        learning_rate='auto'
    )
    coords = tsne.fit_transform(embeddings)

    # 4. Construct Graph JSON
    nodes = []
    edges = []

    # Create Nodes
    for i, c in enumerate(creators):
        # Format the tooltip title
        if c['subscribers'] != "N/A":
            tooltip = f"{c['title']} ({c['subscribers']} subs)"
        else:
            tooltip = c['title']

        nodes.append({
            "id": c['id'],
            "label": c['title'],
            "image": c['thumbnail'],
            # Scale coordinates for better visual spread in the UI
            "x": float(coords[i][0]) * 20, 
            "y": float(coords[i][1]) * 20,
            "shape": "circularImage",
            "title": tooltip, # Used for hover text
            # Add extra metadata for the UI sidebar
            "meta_description": c['description'][:300] + "..." # Preview text
        })

    # Create Edges
    # Threshold: Only draw lines if similarity is high enough
    SIMILARITY_THRESHOLD = 0.30 

    for i in range(len(creators)):
        for j in range(i + 1, len(creators)): # Avoid duplicates (A-B is same as B-A)
            score = float(similarity_matrix[i][j])
            
            if score > SIMILARITY_THRESHOLD:
                edges.append({
                    "source": creators[i]['id'],
                    "target": creators[j]['id'],
                    "weight": score,
                    "label": f"{score:.2f}" # Optional: show score on line
                })

    # 5. Save
    output_data = {
        "nodes": nodes,
        "edges": edges
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Graph built successfully!")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    build_fandom_graph()