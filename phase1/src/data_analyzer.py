import pandas as pd
import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
from timeit import default_timer as timer

DATA_DIR = "data"
RAW_CSV_PATH = os.path.join(DATA_DIR, "raw_comments.csv")
ANALYZED_CSV_PATH = os.path.join(DATA_DIR, "analyzed_data.csv")

# HuggingFace models
SENTIMENT_MODEL_ID = "cardiffnlp/twitter-roberta-base-sentiment-latest"
KEYWORD_MODEL_ID = "all-MiniLM-L6-v2"

def _find_device():
    """Determines the available device: GPU (CUDA or MPS) or CPU.
    
    Returns: torch.device, str
    """
    if torch.cuda.is_available():
        print("Device: CUDA")
        return torch.device("cuda"), "GPU (CUDA)"
    elif torch.backends.mps.is_available():
        print("Device: MPS")
        return torch.device("mps"), "GPU (MPS)"
    else:
        print("Device: CPU")
        return torch.device("cpu"), "CPU"

def load_models():
    """Loads Sentiment and Keyword models.
    Also enables GPU is available(CUDA or MPS)
    """
    device, device_name = _find_device()
    
    # Load Sentiment Model
    sentiment_tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_ID)
    sentiment_model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_ID)
    sentiment_model = sentiment_model.to(device)

    # Create pipeline for batching
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=sentiment_model,
        tokenizer=sentiment_tokenizer,
        device=device
    )

    # Load Keyword Model
    keyword_model = KeyBERT(model=KEYWORD_MODEL_ID)

    return sentiment_pipeline, keyword_model, device_name

def analyze_sentiment(texts, sentiment_pipeline):
    """Analyzes sentiment of a batch of texts using the provided sentiment pipeline.
    
    Args:
        texts (List[str]): List of comment texts to analyze.
        sentiment_pipeline (pipeline): HuggingFace sentiment analysis pipeline.
    
    Returns:
        List[dict]: List of dicts with 'label' and 'score' for the texts.
    """
    
    # Run Pipeline on text. Ensure Truncation happens due to sentiment model limits
    results = sentiment_pipeline(
        texts,
        batch_size=128,
        truncation=True,
        max_length=512
    )

    # Acquire labels and scores
    labels_map = {
        'negative': 'Negative',
        'neutral': 'Neutral',
        'positive': 'Positive'
    }
    labels = [
        labels_map.get(res['label'].lower(), 'Neutral')
        for res in results
    ]
    scores = [res['score'] for res in results]

    return labels, scores

def extract_keywords(texts, keyword_model, top_n=5):
    """Extracts keywords from a batch of texts using the provided keyword model.
    
    Args:
        texts (List[str]): List of comment texts to extract keywords from.
        keyword_model (KeyBERT): KeyBERT model for keyword extraction.
        top_n (int): Number of top keywords to extract.
    
    Returns:
        List[List[str]]: List of lists containing extracted keywords for each text.
    """

    # Get top N keyphrases, joined by a comma

    keyword_results = keyword_model.extract_keywords(
        texts,
        keyphrase_ngram_range=(1,2), # Get 1-word and 2-word phrases
        stop_words="english",
        top_n=top_n
    )

    # Formart output for CSV
    formatted_keywords = []
    for keyword_tuple in keyword_results:
        # Join phrases with a comma
        phrases = [kw[0] for kw in keyword_tuple]
        formatted_keywords.append(", ".join(phrases))
    
    return formatted_keywords

def run_analysis():
    """Run sentiment and keyword analysis pipeline on CSV data."""

    # Load Models
    print("Loading Sentiment and Keyword Models...")
    sentiment_pipeline, keyword_model, _ = load_models()
    
    # Find Data and load it
    if not os.path.exists(RAW_CSV_PATH):
        raise FileNotFoundError(f"Raw data CSV not found at {RAW_CSV_PATH}\n")
    print(f"Loading csv data from {RAW_CSV_PATH}...\n")
    df = pd.read_csv(RAW_CSV_PATH)

    # Clean data before processing
    df.dropna(subset=['body'], inplace=True)
    df['body'] = df['body'].astype(str) # Ensure strings

    print(f"Data Loaded for {len(df)} comments.\n")
    print("Running Sentiment Analysis...\n")

    start_time = timer()
    text_to_analyze = df['body'].tolist() # Convert body to list for batching
    labels, scores = analyze_sentiment(
        texts=text_to_analyze,
        sentiment_pipeline=sentiment_pipeline
    )
    df['sentiment_label'] = labels
    df['sentiment_score'] = scores

    end_time_kw = timer()
    print(f"Sentiment analysis completed in {end_time_kw - start_time:.2f} seconds.\n")

    # Begin Investigating Negative comments from keywords
    df['keywords'] = ""

    negative_mask = df['sentiment_label'] == 'Negative'
    negative_texts = df.loc[negative_mask, 'body'].tolist()

    if not negative_texts:
        print("No Negative comments found")
    else:
        print(f"Running keyword extraction on {len(negative_texts)} negative comments...\n")
        start_time = timer()

        # Run keyword model on negative comments only
        negative_keywords = extract_keywords(
            texts=negative_texts,
            keyword_model=keyword_model,
            top_n=3
        )
        df.loc[negative_mask, 'keywords'] = negative_keywords

        end_time_kw = timer()
        print(f"Keyword extraction completed in {end_time_kw - start_time:.2f} seconds.\n")
    
    df.to_csv(ANALYZED_CSV_PATH, index=False, encoding='utf-8')

    print(f"Analyzed data saved to {ANALYZED_CSV_PATH}\n")
    print("\nSentiment Summary:"
          f"\nPositive: {len(df[df['sentiment_label']=='Positive'])}"
          f"\nNeutral: {len(df[df['sentiment_label']=='Neutral'])}"
          f"\nNegative: {len(df[df['sentiment_label']=='Negative'])}\n")