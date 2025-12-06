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

def fetch_batch_channel_details(youtube, channel_ids):
    """
    Fetches snippet, statistics, and contentDetails for a list of channel IDs.
    
    Args:
        youtube: The authenticated service object.
        channel_ids (list): A list of channel ID strings.
        
    Returns:
        list: A list of dicts containing channel info + uploads_playlist_id.
    """
    print(f"Fetching batch details for {len(channel_ids)} channels...")
    
    # Join IDs into a comma-separated string
    ids_string = ",".join(channel_ids)
    
    # We add 'contentDetails' to the part list to get the uploads playlist
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=ids_string
    )
    response = request.execute()
    
    channels_data = []
    for item in response.get('items', []):
        channels_data.append({
            "id": item['id'],
            "title": item['snippet']['title'],
            "description": item['snippet']['description'],
            "thumbnail": item['snippet']['thumbnails']['default']['url'],
            "subscribers": item['statistics']['subscriberCount'],
            # This is the key to getting their videos:
            "uploads_playlist_id": item['contentDetails']['relatedPlaylists']['uploads']
        })
    
    return channels_data

def fetch_recent_video_titles(youtube, playlist_id, limit=10):
    """
    Fetches the titles of the most recent videos from a specific playlist.
    
    Args:
        youtube: The authenticated service object.
        playlist_id (str): The ID of the uploads playlist.
        limit (int): How many videos to fetch (default 10).
        
    Returns:
        list: A list of video title strings.
    """
    try:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=limit
        )
        response = request.execute()
        
        titles = []
        for item in response.get('items', []):
            titles.append(item['snippet']['title'])
            
        return titles
        
    except Exception as e:
        print(f"Error fetching videos for playlist {playlist_id}: {e}")
        return []