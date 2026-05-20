# nfl-bot

A Discord bot that monitors an NFL news Twitter account via a Nitter RSS feed and automatically posts new tweets to a designated Discord channel. Each post includes the tweet text, any attached images displayed side by side, and an embedded video player for video tweets.

## How It Works

The bot polls a Nitter RSS feed on a configurable interval. When new posts are detected, it parses the tweet text and extracts any media from the HTML description. Images are downloaded and sent as file attachments so Discord displays them in a grid. Video tweets are converted to vxtwitter.com links so Discord can render an inline video player. A channel mention is prepended to each message as a header.

Post IDs are persisted in `seen_posts.json` so the bot never reposts content across restarts.

## Project Structure

```
nfl-bot/
├── bot.py            # Discord client, polling loop, message sending
├── scraper.py        # RSS fetching, HTML parsing, media extraction
├── seen_posts.json   # Tracks already-posted tweet IDs
├── .env              # Configuration (not committed)
└── README.md
```

## Setup

### 1. Install dependencies

```
pip install discord.py feedparser python-dotenv aiohttp
```

### 2. Create a Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
2. Under the Bot tab, create a bot and copy its token.
3. Enable the following Privileged Gateway Intents: Server Members Intent, Message Content Intent.
4. Invite the bot to your server with the `Send Messages` and `Attach Files` permissions.

### 3. Configure the .env file

Create a `.env` file in the project root:

```
DISCORD_TOKEN = your_bot_token_here
CHANNEL_ID = your_channel_id_here
RSS_URL = "https://nitter.net/{X/Twitter Handle}/rss"
POLL_INTERVAL = 60
```

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your Discord bot token |
| `CHANNEL_ID` | ID of the channel the bot posts to |
| `RSS_URL` | Nitter RSS feed URL to monitor |
| `POLL_INTERVAL` | How often to check for new posts, in seconds |

To get a channel ID, enable Developer Mode in Discord (Settings > Advanced), then right-click the channel and select Copy Channel ID.

### 4. First run

On first run, delete `seen_posts.json` if it exists. The bot will seed itself by reading the current feed and marking all existing posts as seen without posting them. From that point on it will only post new content.

```
python bot.py
```

## Changing the RSS Source

The RSS URL can point to any Nitter instance or account. Update `RSS_URL` in `.env` and delete `seen_posts.json` before restarting so the seeding logic runs cleanly against the new feed.

## Dependencies

| Package | Purpose |
|---|---|
| `discord.py` | Discord API client and task scheduling |
| `feedparser` | RSS feed parsing |
| `aiohttp` | Async image downloading |
| `python-dotenv` | Loading configuration from `.env` |
