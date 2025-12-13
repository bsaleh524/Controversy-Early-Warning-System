# import requests
# from bs4 import BeautifulSoup
# import re

# FANDOM_URL = "https://youtube.fandom.com/api.php"

# def search_fandom_page(query):
#     """
#     Searches the YouTube Fandom wiki for a page matching the query.
#     Returns the page title and ID.
#     """
#     params = {
#         "action": "query",
#         "list": "search",
#         "srsearch": query,
#         "format": "json"
#     }
#     try:
#         response = requests.get(FANDOM_URL, params=params)
#         data = response.json()
        
#         if "query" in data and data["query"]["search"]:
#             # Return the top result
#             top_result = data["query"]["search"][0]
#             return top_result["title"], top_result["pageid"]
#     except Exception as e:
#         print(f"Error searching for {query}: {e}")
    
#     return None, None

# def get_page_content(page_title):
#     """
#     Fetches the raw HTML content of a specific wiki page.
#     """
#     params = {
#         "action": "parse",
#         "page": page_title,
#         "prop": "text|images",
#         "format": "json",
#         "redirects": 1
#     }
#     try:
#         response = requests.get(FANDOM_URL, params=params)
#         data = response.json()
        
#         if "parse" in data:
#             return data["parse"]["text"]["*"], data["parse"]["images"]
#     except Exception as e:
#         print(f"Error fetching content for {page_title}: {e}")
    
#     return None, None

# def clean_wiki_text(html_content):
#     """
#     Parses HTML, removes unwanted sections (Trivia, References),
#     and returns a clean text summary.
#     """
#     soup = BeautifulSoup(html_content, "html.parser")
    
#     # 1. Remove unwanted sections (Infoboxes, Tables, References)
#     # Removing Infobox explicitly (we might parse it separately later if needed)
#     for tag in soup.select(".infobox, .reference, .toc, table"):
#         tag.decompose()

#     # 2. Identify and remove unwanted headers + their content
#     # Common unwanted sections in Fandom wikis
#     unwanted_headers = ["Trivia", "References", "Gallery", "Milestones", "External links", "See also"]
    
#     # We iterate through all headers; if we hit a "bad" one, we stop collecting text
#     # until we hit a "good" one? Or easier: just remove the header and next siblings?
#     # A safer approach for embeddings: Just grab the Introduction (Lead Paragraphs).
    
#     # Let's extract the main text content paragraphs
#     text_content = []
    
#     # The intro usually comes before the first <h2> header
#     # Let's just grab all paragraphs that aren't empty
#     for p in soup.find_all("p"):
#         text = p.get_text().strip()
#         if text:
#             text_content.append(text)
            
#     # Join them
#     full_text = " ".join(text_content)
    
#     # 3. Simple Truncation for Embeddings
#     # Embedding models usually handle ~300 words well. 
#     # Let's take the first 2000 characters (approx 300-400 words) to ensure
#     # we capture the "Main Idea" without confusing the model with deep lore.
#     truncated_text = full_text[:2000]
    
#     return truncated_text

# def get_fandom_image(page_title):
#     """
#     Attempts to get the main thumbnail for the page.
#     This is tricky with MediaWiki API; usually requires a separate query.
#     """
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageimages",
#         "pithumbsize": 500,
#         "format": "json"
#     }
#     try:
#         response = requests.get(FANDOM_URL, params=params)
#         data = response.json()
#         pages = data["query"]["pages"]
#         for page_id in pages:
#             if "thumbnail" in pages[page_id]:
#                 return pages[page_id]["thumbnail"]["source"]
#     except Exception:
#         pass
#     return None

# def scrape_creator_data(creator_name):
#     """
#     Main function to orchestrate the scraping for a single creator.
#     """
#     print(f"Scraping Fandom for: {creator_name}...")
    
#     # 1. Find the page
#     title, page_id = search_fandom_page(creator_name)
#     if not title:
#         print(f"  -> Page not found for {creator_name}")
#         return None
        
#     print(f"  -> Found page: '{title}'")
    
#     # 2. Get Info
#     html_content, images = get_page_content(title)
#     if not html_content:
#         return None
        
#     # 3. Clean Text
#     bio_text = clean_wiki_text(html_content)
    
#     # 4. Get Image
#     image_url = get_fandom_image(title)
    
#     return {
#         "id": f"fandom_{page_id}", # Generate a unique ID
#         "title": title,
#         "description": bio_text, # The rich text for embedding
#         "thumbnail": image_url or "https://via.placeholder.com/150",
#         "subscribers": "N/A" # Parsing subs from Infobox is very brittle; leaving placeholder
#     }

# if __name__ == "__main__":
#     # Test run
#     data = scrape_creator_data("HasanAbi")
#     if data:
#         print("\n--- Scrape Result ---")
#         print(f"Title: {data['title']}")
#         print(f"Image: {data['thumbnail']}")
#         print(f"Bio Preview: {data['description'][:300]}...")


# import requests
# from bs4 import BeautifulSoup
# import re

# FANDOM_URL = "https://youtube.fandom.com/api.php"

# def search_fandom_page(query):
#     """
#     Searches the YouTube Fandom wiki for a page matching the query.
#     Returns the page title and ID.
#     """
#     params = {
#         "action": "query",
#         "list": "search",
#         "srsearch": query,
#         "format": "json"
#     }
#     try:
#         response = requests.get(FANDOM_URL, params=params)
#         data = response.json()
        
#         if "query" in data and data["query"]["search"]:
#             # Return the top result
#             top_result = data["query"]["search"][0]
#             return top_result["title"], top_result["pageid"]
#     except Exception as e:
#         print(f"Error searching for {query}: {e}")
    
#     return None, None

# def get_page_content(page_title):
#     """
#     Fetches the raw HTML content of a specific wiki page.
#     """
#     params = {
#         "action": "parse",
#         "page": page_title,
#         "prop": "text", # We only need text, we will parse images from HTML
#         "format": "json",
#         "redirects": 1
#     }
#     try:
#         response = requests.get(FANDOM_URL, params=params)
#         data = response.json()
        
#         if "parse" in data:
#             return data["parse"]["text"]["*"]
#     except Exception as e:
#         print(f"Error fetching content for {page_title}: {e}")
    
#     return None

# def clean_wiki_text(html_content):
#     """
#     Parses HTML, removes unwanted sections (Trivia, References, Infoboxes),
#     and returns a clean text summary.
#     """
#     soup = BeautifulSoup(html_content, "html.parser")
    
#     # 1. Remove unwanted sections
#     # .portable-infobox: Contains the stats (Subs, Name, etc.) which we don't want in the Bio text
#     # .wds-tabs: The "Appearance / YouTube Icon" tabs
#     # .mw-editsection: The [Edit] buttons
#     tags_to_remove = [
#         ".portable-infobox", 
#         ".infobox", 
#         ".reference", 
#         ".toc", 
#         "table", 
#         ".wds-tabs", 
#         ".wikia-gallery-item", 
#         ".mw-editsection", 
#         "script", 
#         "style",
#         "figure"
#     ]
    
#     for selector in tags_to_remove:
#         for tag in soup.select(selector):
#             tag.decompose()

#     # 2. Extract Text
#     # We focus on Paragraphs to get the actual bio
#     text_content = []
#     for p in soup.find_all("p"):
#         # Get text and strip whitespace
#         text = p.get_text().strip()
#         if text:
#             text_content.append(text)
            
#     # Join with spaces
#     full_text = " ".join(text_content)
    
#     # 3. Aggressive Whitespace Cleaning
#     # This replaces all newlines, tabs, and multiple spaces with a single space
#     clean_text = re.sub(r'\s+', ' ', full_text)
    
#     # 4. Truncation
#     # Keep it to ~400 words (approx 2500 chars) for the embedding model
#     return clean_text[:2500]

# def get_fandom_image(html_content):
#     """
#     Parses the HTML to find the main Infobox image.
#     This is usually the 'YouTube Icon' or profile picture.
#     """
#     soup = BeautifulSoup(html_content, "html.parser")
    
#     # Priority 1: The standard Fandom Infobox Image class
#     img = soup.select_one(".pi-image-thumbnail")
    
#     if img and img.get("src"):
#         return img.get("src")
        
#     # Priority 2: Sometimes it's just an image inside the portable infobox
#     img = soup.select_one(".portable-infobox img")
#     if img and img.get("src"):
#         return img.get("src")

#     return None

# def scrape_creator_data(creator_name):
#     """
#     Main function to orchestrate the scraping for a single creator.
#     """
#     print(f"Scraping Fandom for: {creator_name}...")
    
#     # 1. Find the page
#     title, page_id = search_fandom_page(creator_name)
#     if not title:
#         print(f"  -> Page not found for {creator_name}")
#         return None
        
#     print(f"  -> Found page: '{title}'")
    
#     # 2. Get Info (Raw HTML)
#     html_content = get_page_content(title)
#     if not html_content:
#         return None
        
#     # 3. Clean Text
#     bio_text = clean_wiki_text(html_content)
    
#     # 4. Get Image (From HTML, not API prop)
#     image_url = get_fandom_image(html_content)
    
#     return {
#         "id": f"fandom_{page_id}", 
#         "title": title,
#         "description": bio_text, 
#         "thumbnail": image_url or "https://via.placeholder.com/150",
#         "subscribers": "N/A" 
#     }

# if __name__ == "__main__":
#     # Test run
#     data = scrape_creator_data("HasanAbi")
#     if data:
#         print("\n--- Scrape Result ---")
#         print(f"Title: {data['title']}")
#         print(f"Image: {data['thumbnail']}")
#         print(f"Bio Preview: {data['description'][:300]}...")
import requests
from bs4 import BeautifulSoup
import re

FANDOM_URL = "https://youtube.fandom.com/api.php"

def search_fandom_page(query):
    """
    Searches the YouTube Fandom wiki for a page matching the query.
    Returns the page title and ID.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    try:
        response = requests.get(FANDOM_URL, params=params)
        data = response.json()
        
        if "query" in data and data["query"]["search"]:
            # Return the top result
            top_result = data["query"]["search"][0]
            return top_result["title"], top_result["pageid"]
    except Exception as e:
        print(f"Error searching for {query}: {e}")
    
    return None, None

def get_page_content(page_title):
    """
    Fetches the raw HTML content of a specific wiki page.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text", # We only need text, we will parse images from HTML
        "format": "json",
        "redirects": 1
    }
    try:
        response = requests.get(FANDOM_URL, params=params)
        data = response.json()
        
        if "parse" in data:
            return data["parse"]["text"]["*"]
    except Exception as e:
        print(f"Error fetching content for {page_title}: {e}")
    
    return None

def clean_wiki_text(html_content):
    """
    Parses HTML, removes unwanted sections (Trivia, References, Infoboxes),
    and returns a clean text summary.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 1. Remove unwanted sections
    # .portable-infobox: Contains the stats (Subs, Name, etc.) which we don't want in the Bio text
    # .wds-tabs: The "Appearance / YouTube Icon" tabs
    # .mw-editsection: The [Edit] buttons
    tags_to_remove = [
        ".portable-infobox", 
        ".infobox", 
        ".reference", 
        ".toc", 
        "table", 
        ".wds-tabs", 
        ".wikia-gallery-item", 
        ".mw-editsection", 
        "script", 
        "style",
        "figure"
    ]
    
    for selector in tags_to_remove:
        for tag in soup.select(selector):
            tag.decompose()

    # 2. Extract Text
    # We focus on Paragraphs to get the actual bio
    text_content = []
    for p in soup.find_all("p"):
        # Get text and strip whitespace
        text = p.get_text().strip()
        if text:
            text_content.append(text)
            
    # Join with spaces
    full_text = " ".join(text_content)
    
    # 3. Aggressive Whitespace Cleaning
    # This replaces all newlines, tabs, and multiple spaces with a single space
    clean_text = re.sub(r'\s+', ' ', full_text)
    
    # 4. Truncation
    # Keep it to ~400 words (approx 2500 chars) for the embedding model
    return clean_text[:2500]

def get_fandom_image(html_content):
    """
    Parses the HTML to find the main Infobox image.
    Prioritizes images labeled 'YouTube Icon' or 'Profile'.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Priority 1: Specific "YouTube Icon" or "Profile" images in the Infobox
    # We look for the <a> tag wrapping the image, which often has the title
    target_titles = ["YouTube Icon", "Profile", "Avatar"]
    
    for title in target_titles:
        # Find <a> tag with this title inside an infobox figure
        link = soup.select_one(f".portable-infobox figure a[title='{title}']")
        if link:
            img = link.find("img")
            if img and img.get("src"):
                return img.get("src")
        
        # Sometimes the title is on the img tag itself (alt text)
        img = soup.select_one(f".portable-infobox img[alt='{title}']")
        if img and img.get("src"):
            return img.get("src")

    # Priority 2: Fallback to the first standard Infobox thumbnail
    img = soup.select_one(".pi-image-thumbnail")
    if img and img.get("src"):
        return img.get("src")
        
    # Priority 3: Fallback to ANY image inside the portable infobox
    img = soup.select_one(".portable-infobox img")
    if img and img.get("src"):
        return img.get("src")

    return None

def scrape_creator_data(creator_name):
    """
    Main function to orchestrate the scraping for a single creator.
    """
    print(f"Scraping Fandom for: {creator_name}...")
    
    # 1. Find the page
    title, page_id = search_fandom_page(creator_name)
    if not title:
        print(f"  -> Page not found for {creator_name}")
        return None
        
    print(f"  -> Found page: '{title}'")
    
    # 2. Get Info (Raw HTML)
    html_content = get_page_content(title)
    if not html_content:
        return None
        
    # 3. Clean Text
    bio_text = clean_wiki_text(html_content)
    
    # 4. Get Image (From HTML, not API prop)
    image_url = get_fandom_image(html_content)
    
    return {
        "id": f"fandom_{page_id}", 
        "title": title,
        "description": bio_text, 
        "thumbnail": image_url or "https://via.placeholder.com/150",
        "subscribers": "N/A" 
    }

if __name__ == "__main__":
    # Test run
    data = scrape_creator_data("HasanAbi")
    if data:
        print("\n--- Scrape Result ---")
        print(f"Title: {data['title']}")
        print(f"Image: {data['thumbnail']}")
        print(f"Bio Preview: {data['description'][:300]}...")
        