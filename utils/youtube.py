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