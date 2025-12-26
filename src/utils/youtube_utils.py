import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def get_channel_id_from_youtube(channel_name):
    """
    Attempts to fetch the channel ID by guessing the handle URL (e.g., @ChannelName).
    """
    # Remove spaces for the handle (e.g., "Mr Beast" -> "@MrBeast")
    clean_name = channel_name.replace(" ", "")
    
    # 1. Try the direct Handle URL (This gets the page structure you pasted)
    urls_to_try = [
        f"https://www.youtube.com/@{clean_name}",
        f"https://www.youtube.com/@{channel_name}" # Try with original formatting just in case
    ]

    # Headers are often needed to prevent YouTube from blocking the request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for url in urls_to_try:
        try:
            print(f"Trying URL: {url}")
            response = requests.get(url, headers=headers)
            
            # If the channel doesn't exist, YouTube usually returns 404
            if response.status_code == 404:
                continue
                
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- METHOD 1: Meta Tags (Best/Easiest) ---
            # Look for: <meta property="og:url" content="https://www.youtube.com/channel/UC...">
            og_url = soup.find("meta", property="og:url")
            if og_url:
                content = og_url.get("content", "")
                if "/channel/" in content:
                    return content.split("/channel/")[1]

            # --- METHOD 2: Canonical Link ---
            # Look for: <link rel="canonical" href="https://www.youtube.com/channel/UC...">
            canonical = soup.find("link", rel="canonical")
            if canonical:
                href = canonical.get("href", "")
                if "/channel/" in href:
                    return href.split("/channel/")[1]

            # --- METHOD 3: RSS Feed (The one you found) ---
            # Look for: <link rel="alternate" ... href="...channel_id=UC...">
            rss_link = soup.find("link", type="application/rss+xml")
            if rss_link:
                href = rss_link.get("href", "")
                if "channel_id=" in href:
                    return href.split("channel_id=")[1]

        except Exception as e:
            print(f"Error checking {url}: {e}")

    print(f"Could not find channel ID for '{channel_name}'")
    return None

