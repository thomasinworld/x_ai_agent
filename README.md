# Baggy Moonz Twitter Bot

An autonomous Twitter bot that tweets funny content and replies to mentions with sassy, humorous responses.

## Overview

Baggy Moonz is an AI-powered Twitter alter ego that:
- Posts random funny tweets on a schedule
- Automatically replies to mentions with witty, sarcastic responses
- Has a distinct personality that loves making fun of people in a playful way

## Setup Instructions

### 1. Create a Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app/project
3. Request elevated access to get v2 API features
4. Generate API keys, access tokens, and bearer token

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your Twitter API credentials and OpenAI API key in the `.env` file:
```
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
BAGGY_MOONZ_ID=your_twitter_id_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the Bot

```bash
python baggy_moonz_bot.py
```

## Customization

You can customize Baggy Moonz's personality and tweet frequency:

- Edit the system prompt in the `generate_content()` function to change the personality
- Modify the `TWEET_PROMPTS` list to change the types of tweets generated
- Adjust the scheduling in the `run_bot()` function to change how often it tweets and checks mentions

## Running Continuously

For continuous operation, consider using a process manager like `systemd`, `supervisor`, or running it on a cloud service.

Example using `screen` (simple approach):
```bash
screen -S baggy_moonz
python baggy_moonz_bot.py
# Press Ctrl+A, then D to detach
```

To reattach:
```bash
screen -r baggy_moonz
```

## Logs

The bot logs its activity to both the console and a file named `baggy_moonz.log`.
