import feedparser # pyright: ignore[reportMissingImports]
import json
import os
import re
from bs4 import BeautifulSoup # pyright: ignore[reportMissingImports]
from urllib.parse import unquote
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()

RSS_URL = os.environ['RSS_URL']
SEEN_FILE = os.environ['SEEN_FILE']
MAX_SEEN = 40

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return list(json.load(f))
    return list()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def add_seen(seen, post_id, seed):
    if not seed:
        seen.insert(0, post_id)
        if len(seen) > MAX_SEEN:
            del seen[-1]
    elif seed:
        seen.append(post_id)
    return seen

def nitter_img_to_direct(url: str) -> str:
    if '/pic/' in url:
        path = unquote(url.split('/pic/', 1)[1])
        return f"https://pbs.twimg.com/{path}"
    return url

def build_vxtwitter_url(username: str, post_id: str) -> str:
    return f"https://vxtwitter.com/{username}/status/{post_id}"

UNDESIRED_LINK_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?play\.underdogsports\.com\S*', re.IGNORECASE
)

def strip_underdog_links(text: str) -> str:
    cleaned = UNDESIRED_LINK_PATTERN.sub('', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned.strip()

def has_quoted_tweet(html: str) -> bool:
    return bool(BeautifulSoup(html, "html.parser").find("blockquote"))

def extract_media(html: str, username: str, post_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    video_node = soup.find(string=re.compile(r'^\s*Video\s*$'))
    has_video = bool(video_node)
    if video_node:
        video_anchor = video_node.find_parent('a')
        if video_anchor:
            video_anchor.decompose()
        else:
            video_node.extract()
    video_url = build_vxtwitter_url(username, post_id) if has_video else None

    images = [
        nitter_img_to_direct(img['src'])
        for img in soup.find_all('img')
        if img.get('src')
    ]

    return {"images": images, "video_url": video_url}

def get_new_posts(seed=False) -> list[dict]:
    seen = load_seen()
    new_posts = []

    try:
        feed = feedparser.parse(RSS_URL, request_headers={"User-Agent": "Mozilla/5.0"})

        for entry in feed.entries:
            post_id = entry.get("id").split("/")[-1]

            if post_id not in seen:

                seen = add_seen(seen, post_id, seed)

                if not seed:
                    title = entry.get("title", "")
                    if re.match(r'^RT by @', title):
                        continue
                    if re.match(r'^R to @', title):
                        continue

                    summary = entry.get("summary", "")

                    if has_quoted_tweet(summary):
                        continue

                    username = entry.get("author", "").lstrip('@')
                    media = extract_media(summary, username, post_id)

                    text = strip_underdog_links(title)

                    new_posts.append({
                        "text": text,
                        "images": media["images"],
                        "video_url": media["video_url"],
                    })

    except Exception as e:
        print(f"Error fetching NFL feed: {e}")

    save_seen(seen)
    new_posts.reverse()

    return new_posts