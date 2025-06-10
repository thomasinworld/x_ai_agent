#!/usr/bin/env python3
"""
Baggy Moonz Twitter Bot
An autonomous Twitter bot that tweets funny content and replies to mentions
with sassy, humorous responses.
"""
import os
import time
import random
import logging
import schedule
import tweepy
import openai
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("baggy_moonz.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BaggyMoonz")

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Baggy Moonz's Twitter ID (to be filled in after creating the account)
BAGGY_MOONZ_ID = os.getenv("BAGGY_MOONZ_ID", "")

# Initialize Twitter API v2 client
def get_twitter_client():
    """Initialize and return a Twitter API v2 client."""
    client = tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET
    )
    return client

# Generate content using OpenAI
def generate_content(prompt, max_tokens=100):
    """Generate content using OpenAI's API."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Baggy Moonz, a sarcastic, funny Twitter personality who loves making fun of people in a playful way. Your tweets are short, witty, and sometimes absurd. You have strong opinions about random things and aren't afraid to share them."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return None

# Tweet generation prompts
TWEET_PROMPTS = [
    "Create a funny observation about modern technology.",
    "Make a sarcastic comment about social media influencers.",
    "Share an absurd hot take about a mundane topic.",
    "Rant about something trivial as if it's the most important issue in the world.",
    "Create a bizarre conspiracy theory that's obviously a joke.",
    "Make fun of a current trend in a witty way.",
    "Share an unpopular opinion about something everyone loves.",
    "Create a funny 'hot take' that will make people laugh.",
    "Make a sarcastic observation about human behavior.",
    "Share a weird thought that popped into your head."
]

# Post a random tweet
def post_random_tweet():
    """Generate and post a random tweet."""
    prompt = random.choice(TWEET_PROMPTS)
    content = generate_content(prompt)
    
    if content:
        try:
            client = get_twitter_client()
            tweet = client.create_tweet(text=content)
            tweet_id = tweet.data['id']
            tweet_text = content
            logger.info(f"Posted tweet: {tweet_text} (ID: {tweet_id})")
            return True
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
    
    return False

# Get mentions and reply to them
def check_and_reply_to_mentions():
    """Check for mentions and reply to them."""
    try:
        client = get_twitter_client()
        
        # Get the most recent mention we've responded to
        last_mention_id = None
        try:
            with open("last_mention_id.txt", "r") as f:
                last_mention_id = f.read().strip()
        except FileNotFoundError:
            last_mention_id = None
        
        # Get mentions
        mentions = client.get_users_mentions(
            id=BAGGY_MOONZ_ID,
            since_id=last_mention_id,
            tweet_fields=["text", "author_id", "created_at"]
        )
        
        if not mentions.data:
            logger.info("No new mentions found.")
            return
        
        # Process each mention
        newest_id = None
        for mention in mentions.data:
            mention_id = mention.id
            mention_text = mention.text
            author_id = mention.author_id
            
            # Update newest ID
            if newest_id is None or mention_id > newest_id:
                newest_id = mention_id
            
            # Get author info
            author = client.get_user(id=author_id)
            author_username = author.data.username if author.data else "someone"
            
            # Generate a reply
            prompt = f"Create a funny, sarcastic reply to this tweet: '{mention_text}' from user @{author_username}. Make it personal but not mean-spirited."
            reply_content = generate_content(prompt)
            
            if reply_content:
                # Post the reply
                client.create_tweet(
                    text=reply_content,
                    in_reply_to_tweet_id=mention_id
                )
                logger.info(f"Replied to mention {mention_id} from @{author_username}")
        
        # Save the newest mention ID
        if newest_id:
            with open("last_mention_id.txt", "w") as f:
                f.write(str(newest_id))
            
    except Exception as e:
        logger.error(f"Error checking mentions: {e}")

# Main function to run the bot
def run_bot():
    """Main function to run the bot."""
    logger.info("Starting Baggy Moonz Twitter bot...")
    
    # Check for Twitter API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, TWITTER_BEARER_TOKEN]):
        logger.error("Twitter API credentials not found. Please set them in the .env file.")
        return
    
    # Check for OpenAI API key
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found. Please set it in the .env file.")
        return
    
    # Check for Baggy Moonz Twitter ID
    if not BAGGY_MOONZ_ID:
        logger.warning("Baggy Moonz Twitter ID not set. Mentions functionality will not work properly.")
    
    # Schedule tweets and mention checks
    schedule.every(4).hours.do(post_random_tweet)  # Tweet every 4 hours
    schedule.every(30).minutes.do(check_and_reply_to_mentions)  # Check mentions every 30 minutes
    
    # Post an initial tweet
    logger.info("Posting initial tweet...")
    post_random_tweet()
    
    # Run the scheduled tasks
    logger.info("Bot is running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute between checks

if __name__ == "__main__":
    run_bot()
