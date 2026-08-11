# ============================================
# Utility Functions - Helpers & Helpers
# ============================================

import pandas as pd
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import tempfile
from config import CSV_COLUMNS, OUTPUT_FILE, OUTPUT_DIR, INSTAGRAM_URL_PATTERN
import os

INSTAGRAM_RESERVED_PATHS = {
    "about", "accounts", "direct", "directory", "explore", "graphql",
    "p", "press", "reel", "reels", "stories", "tv"
}

def remove_duplicates(urls_list):
    """
    Remove duplicate Instagram URLs from list
    
    Args:
        urls_list: List of URLs
        
    Returns:
        List of unique URLs
    """
    unique_urls = []
    seen = set()
    
    for url in urls_list:
        normalized = normalize_url(url)
        key = normalized or str(url).lower().strip()
        if key not in seen:
            unique_urls.append(normalized or url)
            seen.add(key)
    
    print(f"✅ Duplicates removed: {len(urls_list)} → {len(unique_urls)}")
    return unique_urls


def validate_instagram_url(url):
    """
    Check if URL is valid Instagram profile URL
    
    Args:
        url: URL string to validate
        
    Returns:
        Boolean - True if valid, False otherwise
    """
    username = extract_instagram_username(url)
    return username is not None


def _extract_path_username(url):
    """Extract a profile path from an Instagram URL or redirect URL."""
    parsed = urlparse(url)
    query_url = parse_qs(parsed.query).get("q", [None])[0]
    if query_url:
        return _extract_path_username(query_url)

    host = parsed.netloc.lower().split(":", 1)[0]
    if host not in {"instagram.com", "www.instagram.com", "instagr.am", "www.instagr.am"}:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 1:
        return None

    username = parts[0].lower()
    if username in INSTAGRAM_RESERVED_PATHS:
        return None
    if not re.fullmatch(r"[a-zA-Z0-9._-]+", username):
        return None
    return username


def _is_valid_url_input(url):
    if not url:
        return False
    return isinstance(url, str) and bool(url.strip())


def extract_instagram_username(url):
    """
    Extract username from Instagram URL
    
    Args:
        url: Instagram profile URL
        
    Returns:
        Username string or None
    """
    if not _is_valid_url_input(url):
        return None
    return _extract_path_username(url.strip())


def normalize_url(url):
    """
    Normalize Instagram URL to standard format
    
    Args:
        url: Raw Instagram URL
        
    Returns:
        Normalized URL
    """
    if not url:
        return None
    
    # Extract username
    username = extract_instagram_username(url)
    
    if not username:
        return None
    
    # Return normalized format
    return f"https://www.instagram.com/{username}/"


def save_to_csv(data, filepath=OUTPUT_FILE):
    """
    Save data to CSV file
    
    Args:
        data: List of dictionaries with profile data
        filepath: Output CSV file path
        
    Returns:
        Boolean - True if successful
    """
    try:
        # Create output directory if doesn't exist
        output_dir = os.path.dirname(filepath) or OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Ensure all required columns exist
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = None
        
        # Select only required columns in order
        df = df[CSV_COLUMNS]
        
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', newline='', suffix='.csv',
            dir=output_dir, delete=False
        ) as temporary_file:
            temporary_path = temporary_file.name
        try:
            df.to_csv(temporary_path, index=False, encoding='utf-8')
            os.replace(temporary_path, filepath)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        print(f"✅ Data saved to {filepath}")
        print(f"   Total records: {len(df)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        return False


def load_from_csv(filepath=OUTPUT_FILE):
    """
    Load data from existing CSV
    
    Args:
        filepath: CSV file path
        
    Returns:
        DataFrame or None if file doesn't exist
    """
    try:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            print(f"✅ Loaded {len(df)} records from {filepath}")
            return df
        else:
            print(f"⚠️  File not found: {filepath}")
            return None
    
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return None


def generate_search_queries(city, keywords):
    """
    Generate a broad set of Instagram-focused search queries for a city and niche list.

    The goal is to create many intelligent combinations such as:
    - city + niche
    - city + niche + creator type
    - niche + city + creator type
    - city + creator + niche

    Args:
        city: City name
        keywords: List of niche keywords

    Returns:
        List of search queries
    """
    if not city:
        return []

    city = " ".join(str(city).split()).strip()
    if not city:
        return []

    base_keywords = []
    for keyword in keywords or []:
        cleaned = " ".join(str(keyword).split()).strip()
        if cleaned:
            base_keywords.append(cleaned.lower())

    if not base_keywords:
        base_keywords = ["influencer", "creator"]

    creator_types = [
        "blogger",
        "influencer",
        "creator",
        "content creator",
        "food blogger",
        "food creator",
        "food influencer",
        "food reviewer",
        "reviewer",
        "media creator",
        "fashion creator",
        "fashion blogger",
        "fitness creator",
        "lifestyle creator",
        "travel creator",
        "photographer",
        "maker",
        "coach",
        "expert",
        "professional",
        "local creator",
        "local influencer",
        "city creator",
        "city influencer",
        "community creator",
        "micro influencer",
        "nano influencer",
        "uploader",
        "storyteller",
    ]

    city_slug = re.sub(r'[^a-zA-Z0-9]+', '', city).lower()
    queries = []
    seen = set()

    def add_query(query):
        normalized = " ".join(str(query).split()).strip()
        if not normalized:
            return
        if normalized not in seen:
            queries.append(normalized)
            seen.add(normalized)

    for keyword in base_keywords:
        keyword_clean = " ".join(str(keyword).split()).strip()
        niche_phrases = [
            keyword_clean,
            f"{keyword_clean} creator",
            f"{keyword_clean} blogger",
            f"{keyword_clean} influencer",
            f"{keyword_clean} reviewer",
            f"{keyword_clean} content creator",
            f"{keyword_clean} media creator",
            f"{keyword_clean} expert",
        ]

        for phrase in niche_phrases:
            phrase_clean = " ".join(str(phrase).split()).strip()
            for creator_type in creator_types:
                creator_clean = " ".join(str(creator_type).split()).strip()
                full_phrase = f"{keyword_clean} {creator_clean}".strip()
                if full_phrase == keyword_clean:
                    continue
                add_query(f'site:instagram.com "{city} {full_phrase}"')
                add_query(f'site:instagram.com {city} {full_phrase}')
                add_query(f'site:instagram.com inurl:{city_slug} {full_phrase}')
                add_query(f'site:instagram.com "{city} {phrase_clean}"')
                add_query(f'site:instagram.com {city} {phrase_clean}')
                add_query(f'site:instagram.com inurl:{city_slug} {phrase_clean}')
                add_query(f'site:instagram.com "{phrase_clean} {city}"')
                add_query(f'site:instagram.com {phrase_clean} {city}')
                add_query(f'site:instagram.com inurl:{city_slug} {phrase_clean} {city}')

            add_query(f'site:instagram.com "{city} {phrase_clean}"')
            add_query(f'site:instagram.com {city} {phrase_clean}')
            add_query(f'site:instagram.com inurl:{city_slug} {phrase_clean}')
            add_query(f'site:instagram.com "{phrase_clean} {city}"')
            add_query(f'site:instagram.com {phrase_clean} {city}')

    # Add broad local-intent discovery queries to boost coverage.
    add_query(f'site:instagram.com "{city} influencer"')
    add_query(f'site:instagram.com {city} influencer')
    add_query(f'site:instagram.com "{city} creator"')
    add_query(f'site:instagram.com {city} creator')
    add_query(f'site:instagram.com "{city} blogger"')
    add_query(f'site:instagram.com {city} blogger')
    add_query(f'site:instagram.com "{city} local influencer"')
    add_query(f'site:instagram.com {city} local influencer')
    add_query(f'site:instagram.com "{city} local creator"')
    add_query(f'site:instagram.com {city} local creator')
    add_query(f'site:instagram.com "{city} near me influencer"')
    add_query(f'site:instagram.com {city} near me influencer')
    add_query(f'site:instagram.com "{city} near me creator"')
    add_query(f'site:instagram.com {city} near me creator')
    add_query(f'site:instagram.com "{city} hashtag"')
    add_query(f'site:instagram.com {city} hashtag')
    add_query(f'site:instagram.com "{city} community"')
    add_query(f'site:instagram.com {city} community')

    # Keep the list ordered and compact while preserving breadth.
    queries = queries[:240]

    print(f"✅ Generated {len(queries)} search queries for '{city}'")
    return queries


def get_timestamp():
    """
    Get current timestamp
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_profile_record(username=None, name=None, url=None, profile_url=None, source_query=None, followers=None, following=None, bio=None, verified=None, niche=None):
    """
    Create a validated profile data record containing only the fields needed for storage.

    Returns:
        Dictionary with clean profile data, or None if the profile is invalid.
    """
    normalized_url = normalize_url(profile_url or url or username)
    if not normalized_url:
        return None

    normalized_username = extract_instagram_username(normalized_url)
    if not normalized_username:
        return None

    cleaned_name = " ".join(str(name or normalized_username).split()).strip() or normalized_username
    cleaned_bio = " ".join(str(bio or "").split()).strip() if bio is not None else None
    if cleaned_bio and len(cleaned_bio) > 220:
        cleaned_bio = cleaned_bio[:220]

    def parse_count(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            if not cleaned:
                return None
            suffix = ""
            if cleaned[-1].upper() in {"K", "M", "B"}:
                suffix = cleaned[-1].upper()
                cleaned = cleaned[:-1]
            if not cleaned:
                return None
            try:
                numeric_value = float(cleaned)
            except ValueError:
                return None
            if suffix == "K":
                return int(numeric_value * 1000)
            if suffix == "M":
                return int(numeric_value * 1000000)
            if suffix == "B":
                return int(numeric_value * 1000000000)
            return int(numeric_value)
        return None

    parsed_followers = parse_count(followers)
    parsed_following = parse_count(following)

    if niche is None:
        cleaned_niche = None
    elif isinstance(niche, (list, tuple, set)):
        cleaned_niche = next((str(item).strip().lower() for item in niche if str(item).strip()), None)
    else:
        cleaned_niche = " ".join(str(niche).split()).strip().lower()

    if cleaned_niche in {"", "none", "general"}:
        cleaned_niche = None

    verified_value = None if verified is None else bool(verified)

    record = {
        "username": normalized_username,
        "name": cleaned_name,
        "profile_url": normalized_url,
        "followers": parsed_followers,
        "following": parsed_following,
        "bio": cleaned_bio,
        "verified": verified_value,
        "niche": cleaned_niche,
        "date_collected": get_timestamp(),
    }

    if source_query:
        record["source_query"] = " ".join(str(source_query).split()).strip()

    return record


print("✅ Utils module loaded successfully")
