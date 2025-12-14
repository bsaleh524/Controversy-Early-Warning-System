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
OUTPUT_FILE = "data/youtubers_data_combined.json"
DELAY = 1.0

# --- PART 1: API & Parsing Logic (Clean Data) ---

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
    
    # Remove junk sections that clutter the bio
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
            # Filters for admin/system text
            if len(text) < 30 and ("Sign in" in text or "Edit" in text):
                continue
            if text.endswith('.jpg') or text.endswith('.png'):
                continue
            text_content.append(text)
            
    full_text = " ".join(text_content)
    # Collapse whitespace (newlines/tabs -> single space)
    clean_text = re.sub(r'\s+', ' ', full_text)
    
    return clean_text

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

def get_youtube_url(html_content):
    """
    Parses the HTML to find the 'YouTube Channel' link in the infobox.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Target the infobox specifically to avoid random links in the bio
    infobox = soup.select_one(".portable-infobox")
    if not infobox:
        return None
        
    # Look for any link containing youtube.com
    # We prefer links that look like channel profiles
    for a in infobox.find_all('a', href=True):
        href = a['href']
        if "youtube.com" in href or "youtu.be" in href:
            # Common channel URL patterns
            if any(x in href for x in ["/channel/", "/user/", "/c/", "/@"]):
                return href
            
    return None

# --- PART 2: Crawler Logic (Discovery) ---

def get_soup_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error crawling {url}: {e}")
    return None

def get_category_links(start_url, max_pages=None):
    """
    Crawls the Category pagination to get a list of Creator Profile URLs.
    """
    profile_links = []
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
                # Handle relative URLs
                full_link = BASE_URL + anchor['href'] if anchor['href'].startswith('/') else anchor['href']
                # Filter out system pages
                if "/wiki/Category:" not in full_link and "/wiki/User:" not in full_link:
                    profile_links.append(full_link)

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
        time.sleep(DELAY)

    return list(set(profile_links))

# --- PART 3: Main Execution ---

def main(links=None):
    # 1. If no links provided, crawl the category
    if not links:
        # Set max_pages=None to crawl EVERYTHING, or integer (e.g. 5) for testing
        links = get_category_links(START_CATEGORY_URL)
    
    print(f"\nFound {len(links)} profiles. Starting scrape...")

    results = []
    
    # 2. Scrape each link
    for i, link in enumerate(links):
        # Extract Title from URL (e.g. .../wiki/Gamer_Chad -> Gamer Chad)
        raw_title = link.split('/wiki/')[-1]
        title = unquote(raw_title).replace('_', ' ')
        
        print(f"[{i+1}/{len(links)}] Scraping: {link}")
        
        # Use API to get clean content
        html_content, page_id = get_page_content(title)
        
        if not html_content:
            print(f"  -> Failed to get content for {title}")
            continue

        # Process Content
        bio_text = clean_wiki_text(html_content)
        image_url = get_fandom_image(html_content)
        youtube_url = get_youtube_url(html_content)

        # Filter out empty pages
        if not bio_text:
            print(f"  -> Skipping empty bio for {title}")
            continue

        results.append({
            "id": f"fandom_{page_id}",
            "title": title,
            "description": bio_text,
            "thumbnail": image_url,
            "youtube_url": youtube_url,
            "url": link
        })
        
        time.sleep(DELAY) # API rate limit protection

    # 3. Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\nScraping complete. Saved {len(results)} profiles to {OUTPUT_FILE}")

if __name__ == "__main__":
    # You can pass a specific list for testing, or leave empty to crawl
    # test_links = ["https://youtube.fandom.com/wiki/Gamer_Chad", "https://youtube.fandom.com/wiki/Channel_Mat", "https://youtube.fandom.com/wiki/Supersnailboy"]
    # main(test_links)
    main()