import feedparser # pyright: ignore[reportMissingImports]
import json
import os
import hashlib
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()
rss_url = os.environ['RSS_URL']

SEEN_FILE = "seen_posts.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def make_id(entry) -> str:
    raw = entry.get("link") or entry.get("title") or str(entry)
    return hashlib.md5(raw.encode()).hexdigest()

def get_media(entry) -> str:
    """Extract image or video URL from a feed entry if present."""
    # Check media_content (common in RSS/Nitter)
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url", "")

    # Check enclosures (another common RSS media field)
    if hasattr(entry, "enclosures") and entry.enclosures:
        return entry.enclosures[0].get("href", "")

    return ""

def get_new_posts(seed=False) -> list[dict]:
    seen = load_seen()
    new_posts = []

    try:
        feed = feedparser.parse(rss_url, request_headers={"User-Agent": "Mozilla/5.0"})
        for entry in feed.entries:
            # post_id = make_id(entry)
            post_id = entry.get("id").split("/")[-1]
            if post_id not in seen:
                seen.add(post_id)
                if not seed:
                    new_posts.append({
                        "summary": entry.get("summary", ""),
                        "media": get_media(entry),
                    })
                    
    except Exception as e:
        print(f"Error fetching NFL feed: {e}")

    save_seen(seen)
    new_posts.reverse()
    return new_posts