# src/scraper.py
import os
import pandas as pd
from googleapiclient.errors import HttpError
from youtube import setup_youtube_client
import yaml


# --- Main Functions ---

def load_video_ids(data_dir: str):
    """Loads video IDs from a data YAML file."""
    data_path = os.path.join(data_dir, "video_ids.yaml")
    with open(data_path, 'r') as file:
        yaml_ids = yaml.safe_load(file)
    return yaml_ids.get("VIDEO_IDS_TO_SCRAPE", [])

def load_channel_info(data_dir: str):
    """Loads video IDs from a data YAML file."""
    data_path = os.path.join(data_dir, "channel_ids.yaml")
    with open(data_path, 'r') as file:
        yaml_ids = yaml.safe_load(file)
    return yaml_ids.get("CHANNEL_IDS", [])
    
def scrape_comments(data_dir: str, csv_path: str):
    """
    Scrapes comments from the defined video IDs and saves them to a CSV file.
    """

    if os.path.exists(csv_path):
        print(f"Comments data already exists at {csv_path}. Skipping scraping.")
        return pd.read_csv(csv_path)
    youtube = setup_youtube_client()
    
    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    print(f"Starting scrape. Data will be saved to '{csv_path}'")
    
    all_comments_data = [] # A list to hold all our comment data (as dicts)

    # --- Outer loop: Iterate through each Video ---
    video_ids = load_video_ids(data_dir)
    print(f"video_ids loaded: {video_ids}")
    for video_id in video_ids:
        print(f"\nFetching comments from video ID: {video_id}")
        
        try:
            # --- Inner loop: Handle API Pagination ---
            # This is how we get *all* comments, not just the first 100
            
            next_page_token = None
            comments_scraped_for_video = 0

            while True:
                # Request comment threads for the video
                request = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=100,  # Max allowed by the API
                    pageToken=next_page_token,
                    textFormat='plainText' # Get plain text, not HTML
                )
                response = request.execute()

                # Loop through each comment thread in the response
                for item in response['items']:
                    # Get the top-level comment snippet
                    comment = item['snippet']['topLevelComment']['snippet']
                    
                    # Clean the body text: remove newlines/tabs and strip whitespace
                    body = comment['textDisplay'].replace('\n', ' ').replace('\r', ' ').strip()
                    
                    # Append the data to our master list
                    all_comments_data.append({
                        'video_id': video_id,
                        'comment_id': item['snippet']['topLevelComment']['id'],
                        'timestamp_utc': comment['publishedAt'],
                        'body': body,
                        'score': comment['likeCount']
                    })
                    comments_scraped_for_video += 1

                # Check if there is another page of comments
                next_page_token = response.get('nextPageToken')
                
                if not next_page_token:
                    # No more pages, break the inner 'while' loop
                    break

                # Optional: A small status update
                if comments_scraped_for_video % 500 == 0:
                    print(f"  ... scraped {comments_scraped_for_video} comments so far for this video...")

            print(f"Successfully scraped {comments_scraped_for_video} comments from video {video_id}.")

        except HttpError as e:
            if e.resp.status == 403 and 'commentsDisabled' in str(e.content):
                print(f"Comments are disabled for video {video_id}. Skipping.")
            else:
                print(f"An HTTP error occurred for video {video_id}: {e}")
        except Exception as e:
            print(f"An error occurred processing video {video_id}: {e}")
            continue # Skip to the next video if one fails

    # --- After all videos are done, save to CSV ---
    if not all_comments_data:
        print("No comments were scraped. Exiting.")
        return

    print("\n--- Scraping Complete ---")
    
    # Convert the list of dictionaries to a Pandas DataFrame
    df = pd.DataFrame(all_comments_data)
    
    # Save the DataFrame to a CSV file
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    print(f"Total comments scraped: {len(df)}")
    print(f"Data saved to: {csv_path}")

    return df

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

# Scrape titles

# Scrape users