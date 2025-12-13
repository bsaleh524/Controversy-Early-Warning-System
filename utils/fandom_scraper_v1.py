import requests
from bs4 import BeautifulSoup
import time
import json

# Configuration
BASE_URL = "https://youtube.fandom.com"
START_URL = "https://youtube.fandom.com/wiki/Category:YouTubers"
OUTPUT_FILE = "youtubers_data.json"
DELAY = 1.0  # Seconds between requests to be polite

def get_soup(url):
    """Helper to fetch a URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        else:
            print(f"Failed to retrieve {url} (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_category_links(start_url):
    """Crawls the category pagination to get all YouTuber profile URLs."""
    profile_links = []
    current_url = start_url
    
    print("Starting category crawl...")
    
    while current_url:
        print(f"Scanning category page: {current_url}")
        soup = get_soup(current_url)
        if not soup:
            break

        # 1. Extract profile links from the current category page
        # Fandom category members are usually in a div with class 'category-page__members'
        member_sections = soup.find_all('li', class_='category-page__member')
        
        for member in member_sections:
            anchor = member.find('a', class_='category-page__member-link')
            if anchor and anchor.has_attr('href'):
                # Handle relative URLs
                full_link = BASE_URL + anchor['href'] if anchor['href'].startswith('/') else anchor['href']
                # Filter out 'Category:' or 'User:' pages that might slip in
                if "/wiki/Category:" not in full_link and "/wiki/User:" not in full_link:
                    profile_links.append(full_link)

        # 2. Find the 'Next' button for pagination
        next_button = soup.find('a', class_='category-page__pagination-next')
        if next_button and next_button.has_attr('href'):
            current_url = next_button['href']
            # Sometimes the href is relative, sometimes absolute
            if current_url.startswith('/'):
                current_url = BASE_URL + current_url
        else:
            current_url = None # Stop loop if no next button

        time.sleep(DELAY) # Respect rate limits

    # Remove duplicates just in case
    return list(set(profile_links))

def scrape_profile(url):
    """Extracts data from a single YouTuber's page with improved text parsing."""
    soup = get_soup(url)
    if not soup:
        return None

    # 1. Extract Title (Name)
    # Try the standard header first
    title_tag = soup.find('h1', class_='page-header__title')
    # Backup: try getting it from the <title> tag if h1 is missing
    if not title_tag:
        name = soup.title.string.split('|')[0].strip() if soup.title else "Unknown"
    else:
        name = title_tag.get_text(strip=True)

    # 2. Extract Description
    # We look for the main content container
    content_div = soup.find('div', {'id': 'mw-content-text'})
    
    description_paragraphs = []
    
    if content_div:
        # Find ALL paragraphs inside the content, not just direct children
        # We limit to the first 10 paragraphs to avoid grabbing footer text or comments
        paragraphs = content_div.find_all('p', limit=10)
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # FILTERS:
            # 1. Ignore empty paragraphs
            if not text:
                continue
            
            # 2. Ignore short "administrative" text often found in headers/infoboxes
            if len(text) < 30 and ("Sign in" in text or "Edit" in text):
                continue

            # 3. Ignore text that looks like a file name (common in Fandom image captions)
            if text.endswith('.jpg') or text.endswith('.png'):
                continue

            description_paragraphs.append(text)

    # Join the valid paragraphs. If we found none, fallback to an empty string.
    description = "\n\n".join(description_paragraphs)

    return {
        "name": name,
        "url": url,
        "description": description
    }

def main():
    # Step 1: Get all links
    links = get_category_links(START_URL)
    print(f"\nFound {len(links)} profiles. Starting scrape...")

    results = []
    
    # Step 2: Scrape each link
    # Using enumerate to show progress
    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] Scraping: {link}")
        data = scrape_profile(link)
        if data:
            results.append(data)
        
        time.sleep(DELAY) # IMPORTANT: Sleep to prevent IP bans

    # Step 3: Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\nScraping complete. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()