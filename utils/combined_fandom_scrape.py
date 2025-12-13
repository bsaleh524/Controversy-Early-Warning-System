import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from urllib.parse import unquote

# --- Configuration ---
FANDOM_API_URL = "https://youtube.fandom.com/api.php"
BASE_URL = "https://youtube.fandom.com"
START_CATEGORY_URL = "https://youtube.fandom.com/wiki/Category:YouTubers"
OUTPUT_FILE = "data/youtubers_data.json"
DELAY = 1.0  # Seconds between requests to be polite
# --- PART 1: The API Scraper (Clean Data) ---

def get_page_content(page_title):
    """
    Fetches the raw HTML content of a specific wiki page via API.
    Returns: (html_content, page_id)
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text", 
        "format": "json",
        "redirects": 1
    }
    try:
        response = requests.get(FANDOM_API_URL, params=params)
        data = response.json()
        
        if "parse" in data:
            return data["parse"]["text"]["*"], data["parse"].get("pageid")
    except Exception as e:
        print(f"Error fetching content for {page_title}: {e}")
    
    return None, None

def clean_wiki_text(html_content):
    """
    Parses HTML, removes unwanted sections, and returns clean text.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove junk
    tags_to_remove = [
        ".portable-infobox", ".infobox", ".reference", ".toc", "table", 
        ".wds-tabs", ".wikia-gallery-item", ".mw-editsection", 
        "script", "style", "figure", ".navbox", ".category-page__members"
    ]
    
    for selector in tags_to_remove:
        for tag in soup.select(selector):
            tag.decompose()

    # Extract text from paragraphs
    text_content = []
    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if text:
            # Filters for admin text
            if len(text) < 30 and ("Sign in" in text or "Edit" in text):
                continue
            if text.endswith('.jpg') or text.endswith('.png'):
                continue
            text_content.append(text)
            
    full_text = " ".join(text_content)
    clean_text = re.sub(r'\s+', ' ', full_text) # Collapse whitespace
    
    return clean_text[:3000] # Truncate to ~500 words for embedding models

def get_fandom_image(html_content):
    """
    Parses the HTML to find the 'YouTube Icon' or best available image.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Priority 1: Check for explicit "YouTube Icon" or "Profile" titles in Infobox
    target_titles = ["YouTube Icon", "Profile", "Avatar", "Appearance"]
    
    for title in target_titles:
        # Check <a> links with title
        link = soup.select_one(f".portable-infobox figure a[title='{title}']")
        if link:
            img = link.find("img")
            if img and img.get("src"): return img.get("src")
        
        # Check <img> tags with alt text
        img = soup.select_one(f".portable-infobox img[alt='{title}']")
        if img and img.get("src"): return img.get("src")

    # Priority 2: Fallback to the standard thumbnail class
    img = soup.select_one(".pi-image-thumbnail")
    if img and img.get("src"): return img.get("src")
        
    # Priority 3: Any image in the infobox
    img = soup.select_one(".portable-infobox img")
    if img and img.get("src"): return img.get("src")

    return "https://via.placeholder.com/150"

def process_creator_by_title(title):
    """
    Orchestrates the API scrape for a single creator title.
    """
    html_content, page_id = get_page_content(title)
    
    if not html_content:
        return None
        
    bio_text = clean_wiki_text(html_content)
    image_url = get_fandom_image(html_content)
    
    # If bio is empty, it's likely a redirect page or empty stub
    if not bio_text:
        return None

    return {
        "id": f"fandom_{page_id}", 
        "title": title,
        "description": bio_text, 
        "thumbnail": image_url,
        "subscribers": "N/A" # Fandom structure makes extracting subs unreliable
    }

# --- PART 2: The Category Crawler (Discovery) ---

def get_soup_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error crawling {url}: {e}")
    return None

def get_category_links(start_url, max_pages=5):
    """
    Crawls the Category pagination to get a list of Creator Titles.
    """
    titles = []
    current_url = start_url
    page_count = 0
    
    print("Starting category crawl...")
    
    while current_url and (max_pages is None or page_count < max_pages):
        print(f"Scanning category page {page_count+1}: {current_url}")
        soup = get_soup_from_url(current_url)
        if not soup:
            break

        # Extract profile links
        for member in soup.find_all('li', class_='category-page__member'):
            anchor = member.find('a', class_='category-page__member-link')
            if anchor and anchor.has_attr('href'):
                href = anchor['href']
                # Filter out system pages
                if "/wiki/Category:" not in href and "/wiki/User:" not in href:
                    # Extract Title from URL
                    raw_title = href.split('/wiki/')[-1]
                    # Decode URL (e.g., "PewDiePie%27s" -> "PewDiePie's")
                    clean_title = unquote(raw_title).replace('_', ' ')
                    titles.append(clean_title)

        # Find Next Button
        next_button = soup.find('a', class_='category-page__pagination-next')
        if next_button and next_button.has_attr('href'):
            current_url = next_button['href']
            # Handle relative URLs
            if current_url.startswith('/'):
                current_url = BASE_URL + current_url
        else:
            current_url = None
            
        page_count += 1
        time.sleep(1.0) # Polite crawling delay

    return list(set(titles))

# --- PART 3: Main Execution ---

def run_bulk_scrape(limit=50):
    """
    Runs the full pipeline: Crawl Categories -> Scrape API -> Save JSON.
    """
    # 1. Discovery
    # Increase max_pages if you want more than the first few pages of creators
    all_titles = get_category_links(START_CATEGORY_URL, max_pages=10)
    print(f"\nFound {len(all_titles)} unique profiles. Processing the first {limit}...")
    
    results = []
    
    # 2. Scraping
    for i, title in enumerate(all_titles[:limit]):
        print(f"[{i+1}/{limit}] Scraping API: {title}")
        
        data = process_creator_by_title(title)
        
        if data:
            results.append(data)
        else:
            print(f"  -> Skipped (Empty/Error): {title}")
        
        time.sleep(DELAY) # API rate limit protection
        
    # 3. Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nScraping complete. Saved {len(results)} profiles to {OUTPUT_FILE}")

if __name__ == "__main__":
    # Adjust 'limit' to control how many youtubers you want to embed
    run_bulk_scrape(limit=30)