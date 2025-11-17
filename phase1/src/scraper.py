# src/scraper.py

import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys

# --- Configuration ---

# Define the path to write the data
DATA_DIR = "data"
CSV_FILE_PATH = os.path.join(DATA_DIR, "raw_comments.csv")

# These are the specific, high-comment videos about the scandal.
# This provides a perfect, concentrated dataset for the "Back-Tester" MVP.
VIDEO_IDS_TO_SCRAPE = [
    'AzPIgPTPuOA',  # "How to Mistreat Your Dog & Fail to Get Away With It..." (9.9K+ comments)
    'aAVr72W1MHI',  # "xQc Just FINISHED on Hasan" (3.1K+ comments)
    'R2smNd9FBHc',  # "Dog Expert Reacts To Hasan Piker Dog Abuse Drama" (5.9K+ comments)
    'vYhclZkPcvk',  # "xQc Reacts to Another Clip of Hasan Using Shock Collar..." (2.4K+ comments)
    '1K0GJlQGxIk',  # "Streamer Hasan Piker Accused of Using a Shock Collar..." (1.1K+ comments)
]

# --- Main Functions ---

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


def scrape_comments():
    """
    Scrapes comments from the defined video IDs and saves them to a CSV file.
    """

    if os.path.exists(CSV_FILE_PATH):
        print(f"Comments data already exists at {CSV_FILE_PATH}. Skipping scraping.")
        return pd.read_csv(CSV_FILE_PATH)
    youtube = setup_youtube_client()
    
    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Starting scrape. Data will be saved to '{CSV_FILE_PATH}'")
    
    all_comments_data = [] # A list to hold all our comment data (as dicts)

    # --- Outer loop: Iterate through each Video ---
    for video_id in VIDEO_IDS_TO_SCRAPE:
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
    df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8')
    
    print(f"Total comments scraped: {len(df)}")
    print(f"Data saved to: {CSV_FILE_PATH}")

    return df