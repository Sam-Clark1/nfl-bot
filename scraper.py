import feedparser # pyright: ignore[reportMissingImports]
import json
import os
import hashlib
import re
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()

RSS_URL = os.environ['RSS_URL']
SEEN_FILE = "seen_posts.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

# def get_media(entry) -> str:
#     """Extract image or video URL from a feed entry if present."""
#     # Check media_content (common in RSS/Nitter)
#     if hasattr(entry, "media_content") and entry.media_content:
#         return entry.media_content[0].get("url", "")

#     # Check enclosures (another common RSS media field)
#     if hasattr(entry, "enclosures") and entry.enclosures:
#         return entry.enclosures[0].get("href", "")

#     return ""

def get_new_posts(seed=False) -> list[dict]:
    seen = load_seen()
    new_posts = []

    try:

        feed = feedparser.parse(RSS_URL, request_headers={"User-Agent": "Mozilla/5.0"})

        for entry in feed.entries:
            post_id = entry.get("id").split("/")[-1]

            if post_id not in seen:
                seen.add(post_id)

                if not seed:
                    summary = re.sub(r'\s*https?://\S+$', '', entry.get("summary", "")).strip()
                    new_posts.append({
                        "summary": summary,
                        # "media": get_media(entry),
                    })
                    
    except Exception as e:
        print(f"Error fetching NFL feed: {e}")

    save_seen(seen)
    new_posts.reverse()

    return new_posts