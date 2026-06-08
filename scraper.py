import feedparser # pyright: ignore[reportMissingImports]
import json
import os
import re
from urllib.parse import unquote
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

def nitter_img_to_direct(url: str) -> str:
    if '/pic/' in url:
        path = unquote(url.split('/pic/', 1)[1])
        return f"https://pbs.twimg.com/{path}"
    return url

def nitter_to_vxtwitter(url: str) -> str:
    match = re.search(r'nitter\.[^/]+/([^/]+)/status/(\d+)', url)
    if match:
        username, tweet_id = match.groups()
        return f"https://vxtwitter.com/{username}/status/{tweet_id}"
    return url

VIDEO_PATTERN = r'<a href="([^"]+/status/\d+[^"]*)"[^>]*>.*?Video.*?</a>'

def extract_media(html: str) -> dict:
    html = re.sub(r'<blockquote.*?</blockquote>', '', html, flags=re.DOTALL)

    video_match = re.search(VIDEO_PATTERN, html, flags=re.DOTALL)
    video_url = nitter_to_vxtwitter(video_match.group(1)) if video_match else None

    if video_url:
        html = re.sub(VIDEO_PATTERN, '', html, flags=re.DOTALL)

    images = [nitter_img_to_direct(src) for src in re.findall(r'<img[^>]+src="([^"]+)"', html)]

    return {"images": images, "video_url": video_url}

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
                    title = entry.get("title", "")
                    if re.match(r'^RT by @', title):
                        continue
                    if re.match(r'^R to @', title):
                        continue
                    media = extract_media(entry.get("summary", ""))
                    new_posts.append({
                        "text": title,
                        "images": media["images"],
                        "video_url": media["video_url"],
                    })

    except Exception as e:
        print(f"Error fetching NFL feed: {e}")

    save_seen(seen)
    new_posts.reverse()

    return new_posts
