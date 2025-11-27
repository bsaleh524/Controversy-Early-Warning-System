import os
import sys
from googleapiclient.discovery import build

def setup_youtube_client():
    """
    Loads API credentials from .env and builds the YouTube API service.
    """
    api_key = os.environ["YOUTUBE_API_KEY"]

    if not api_key:
        raise ValueError("Missing YOUTUBE_API_KEY in .env file.")

    try:
        # Build the service object
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("Successfully authenticated with YouTube Data API v3.")
        return youtube
    except Exception as e:
        print(f"Error building YouTube client: {e}")
        sys.exit(1)