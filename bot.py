import discord
from discord.ext import tasks
import os
import io
import aiohttp
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from scraper import get_new_posts

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
POLL_INTERVAL = int(os.environ['POLL_INTERVAL'])
SEEN_FILE = os.getenv('SEEN_FILE')

IMAGE_MAX_WIDTH = 400

POLL_START_HOUR = 7
POLL_END_HOUR = 0

def is_polling_hours() -> bool:
    hour = datetime.now().hour
    if POLL_START_HOUR == POLL_END_HOUR:
        return True
    if POLL_START_HOUR < POLL_END_HOUR:
        return POLL_START_HOUR <= hour < POLL_END_HOUR
    return hour >= POLL_START_HOUR or hour < POLL_END_HOUR

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    await seed_seen_posts()
    poll_news.start()

async def seed_seen_posts():
    if not os.path.exists(SEEN_FILE) or os.path.getsize(SEEN_FILE) == 0:
        print('First run detected — seeding seen posts without posting...')
        get_new_posts(seed=True)
        print('Seeding done. Bot will now only post new tweets going forward.')

def resize_image(data: bytes) -> bytes:
    image = Image.open(io.BytesIO(data))
    if image.width <= IMAGE_MAX_WIDTH:
        return data
    ratio = IMAGE_MAX_WIDTH / image.width
    new_size = (IMAGE_MAX_WIDTH, round(image.height * ratio))
    resized = image.resize(new_size, Image.LANCZOS)
    output = io.BytesIO()
    resized.save(output, format=image.format or 'PNG')
    return output.getvalue()

async def download_images(urls: list[str]) -> list[discord.File]:
    files = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        data = resize_image(data)
                        filename = url.split('/')[-1].split('?')[0] or 'image.jpg'
                        files.append(discord.File(io.BytesIO(data), filename=filename))
            except Exception as e:
                print(f"Failed to download image {url}: {e}")
    return files

@tasks.loop(seconds=POLL_INTERVAL)
async def poll_news():
    if not is_polling_hours():
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print('Channel not found!')
        return

    posts = get_new_posts()

    for post in posts:
        content = f"<#{CHANNEL_ID}>\n{post['text']}"
        if post.get('video_url'):
            content += f"\n{post['video_url']}"

        files = await download_images(post.get('images', []))
        await channel.send(content=content, files=files)

bot.run(TOKEN)