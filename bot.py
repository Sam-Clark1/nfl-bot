import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]
from scraper import get_new_posts

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
poll_interval = int(os.environ['POLL_INTERVAL'])

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    await seed_seen_posts()
    poll_news.start()

async def seed_seen_posts():
    SEEN_FILE = "seen_posts.json"
    if not os.path.exists(SEEN_FILE) or os.path.getsize(SEEN_FILE) == 0:
        print("First run detected — seeding seen posts without posting...")
        get_new_posts(seed=True)
        print("Seeding done. Bot will now only post new tweets going forward.")

@tasks.loop(seconds=poll_interval)
async def poll_news():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found!")
        return

    posts = get_new_posts()

    for post in posts:
        message = post["summary"]
        
        if post.get("media"):
            message += f"\n{post['media']}"

        await channel.send(message)
        
bot.run(TOKEN)