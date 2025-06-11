#!/usr/bin/env python3
"""
Baggy Moonz Twitter Bot - Intelligent Edition
An autonomous Twitter bot that makes smart decisions about when and how to engage
"""
import os
import time
import random
import logging
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from personality import *  # Import all personality functions

# Configure logging for console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("baggy_moonz.log"),
        logging.StreamHandler()  # This ensures everything goes to console
    ]
)
logger = logging.getLogger("BaggyMoonz")

# Load environment variables
load_dotenv()

# Bot configuration
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class IntelligentTwitterBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.last_tweet_time = None
        self.last_bio_update = None
        self.engagement_history = []
        self.blacklisted_users = set()
        self.followers = []
        self.engaged_tweets = set()  # Track tweets we've already engaged with
        
    def setup_driver(self):
        """Set up Chrome driver with options."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        
        try:
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            logger.error(f"ChromeDriver installation failed: {e}")
            logger.info("Trying to use system ChromeDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 10)
        logger.info("✅ Chrome driver setup complete")
    
    def login_to_twitter(self):
        """Log in to Twitter using credentials."""
        try:
            logger.info("🔐 Logging into Twitter...")
            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(3)
            
            # Enter username
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"]'))
            )
            username_input.send_keys(TWITTER_USERNAME)
            
            # Click Next
            next_button = self.driver.find_element(By.XPATH, '//span[text()="Next"]/..')
            next_button.click()
            time.sleep(2)
            
            # Enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.send_keys(TWITTER_PASSWORD)
            
            # Click Log in
            login_button = self.driver.find_element(By.XPATH, '//span[text()="Log in"]/..')
            login_button.click()
            
            # Wait for home page to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]')))
            self.logged_in = True
            logger.info("✅ Successfully logged into Twitter")
            
        except Exception as e:
            logger.error(f"❌ Error logging in to Twitter: {e}")
            self.logged_in = False
    
    def generate_content(self, prompt, content_type="tweet"):
        """Generate content using OpenAI with personality."""
        try:
            logger.info(f"🧠 Generating {content_type}...")
            
            # Use personality system prompt
            system_prompt = get_system_prompt()
            
            # Add extremely strict instructions for clean content
            enhanced_prompt = f"{prompt}\n\nCRITICAL RULES - NEVER BREAK THESE:\n1. NO emojis of any kind (no 🚀💎😀🤔💻🔥💯)\n2. NO hashtags ever (no #, no #rekt, no #ngmi)\n3. NO symbols except basic punctuation and crypto tickers (.,!? and $BTC etc are OK)\n4. Under 150 characters total\n5. Crypto tickers like $BTC $ETH are allowed and encouraged\n6. Be savage but avoid emoji/hashtag symbols\n7. Don't include any usernames or @mentions in the reply content itself\n8. MOST IMPORTANT: Your reply MUST directly respond to their content - don't generate random roasts, respond to what they actually said\n9. NEVER mention other usernames that aren't the person you're replying to\n10. Stay focused on the specific tweet content you're responding to"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=50,  # Increased to ensure complete sentences
                temperature=0.5  # Lower for more focused content
            )
            
            content = response.choices[0].message.content.strip()
            
            # Ensure complete sentences
            content = self.ensure_complete_sentence(content)
            
            # Don't enhance with personality - let the AI generate clean content
            # content = enhance_tweet(content)  # Commented out to avoid adding emojis
            
            # Validate content with retries
            max_attempts = 8
            attempt = 0
            
            while not self.validate_content(content) and attempt < max_attempts:
                attempt += 1
                logger.warning(f"⚠️  Content failed validation (attempt {attempt}), regenerating...")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{enhanced_prompt}\n\nPrevious attempt failed - make it shorter and cleaner but complete the sentence."}
                    ],
                    max_tokens=40,  # Increased to ensure complete sentences on retries
                    temperature=0.4
                )
                
                content = response.choices[0].message.content.strip()
            
            if attempt >= max_attempts:
                logger.error("❌ Failed to generate valid content after maximum attempts")
                return None
            
            logger.info(f"✅ Generated {content_type}: {content}")
            return content
                
        except Exception as e:
            logger.error(f"❌ Error generating content: {e}")
            return None
    
    def ensure_complete_sentence(self, content):
        """Ensure the content ends with a complete sentence."""
        if not content:
            return content
        
        # Remove quotes if they're unmatched
        if content.count('"') % 2 != 0:
            content = content.replace('"', '')
        
        # If it doesn't end with proper punctuation, try to complete it
        if not content.endswith(('.', '!', '?', ':', ';')):
            # Find the last complete word and add appropriate ending
            words = content.split()
            if words:
                # Add period to make it a complete sentence
                content = ' '.join(words) + '.'
        
        return content
    
    def validate_content(self, content):
        """Validate content before posting - keep it short and clean."""
        logger.info(f"🔍 Validating content: {content}")
        
        # Check for hashtags
        if '#' in content:
            logger.warning("❌ Content contains hashtags")
            return False
            
        # Check for emojis - no emojis allowed (comprehensive pattern)
        import re
        emoji_pattern = r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]|[\U00002600-\U000027BF]|[\U0001F900-\U0001F9FF]|[\U000024C2-\U0001F251]|[\U0001F004]|[\U0001F0CF]|[\U0001F170-\U0001F171]|[\U0001F17E-\U0001F17F]|[\U0001F18E]|[\U0001F191-\U0001F19A]|[\U0001F1E6-\U0001F1FF]'
        # Also check for common text emojis
        text_emojis = ['🤔', '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥', '😌', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶', '🥴', '😵', '🤯', '🤠', '🥳', '😎', '🤓', '🧐', '😕', '😟', '🙁', '😮', '😯', '😲', '😳', '🥺', '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱', '😖', '😣', '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬', '😈', '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽', '👾', '🤖', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '🚀', '💎', '🙌', '💰', '💸', '🔥', '💯', '⚡', '🎯', '📈', '🌕', '🌙']
        if re.search(emoji_pattern, content) or any(emoji in content for emoji in text_emojis):
            logger.warning("❌ Content contains emojis")
            return False
        
        # Length check - allow complete sentences
        if len(content) > 200:
            logger.warning("❌ Content too long")
            return False
        
        # Only block truly dangerous content
        dangerous_words = ['kys', 'kill yourself', 'suicide', 'terrorist', 'bomb', 'murder']
        if any(word in content.lower() for word in dangerous_words):
            logger.warning("❌ Content crosses the line")
            return False
        
        # Check if it's too short or meaningless
        if len(content) < 10:
            logger.warning("❌ Content too short")
            return False
        
        # More lenient proofreading
        return self.ai_proofread(content)
    
    def ai_proofread(self, content):
        """Use AI to proofread and validate content quality."""
        try:
            logger.info("📝 AI proofreading content...")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Rate this Twitter reply from 1-10. Be very lenient with edgy/savage content as that's the personality. Only rate 1-2 for spam/gibberish. Rate 5+ for decent replies, 7+ for good ones. Respond with just a number."},
                    {"role": "user", "content": f"Rate this reply: {content}"}
                ],
                max_tokens=5,
                temperature=0.1
            )
            
            rating = int(response.choices[0].message.content.strip())
            logger.info(f"📊 Content rating: {rating}/10")
            
            if rating >= 4:  # Lower threshold - let savage personality shine
                logger.info("✅ Content passed AI proofreading")
                return True
            else:
                logger.warning("❌ Content failed AI proofreading")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in AI proofreading: {e}")
            return True  # Default to allowing if proofreading fails
    
    def validate_reply_relevance(self, reply_content, original_tweet_text, expected_username):
        """Validate that the generated reply is actually relevant to the tweet being replied to."""
        try:
            logger.info(f"🔍 Validating reply relevance for @{expected_username}")
            
            # Check if reply mentions wrong usernames (common issue)
            other_usernames = re.findall(r'@(\w+)', reply_content)
            # Filter out the expected username
            wrong_usernames = [u for u in other_usernames if u.lower() != expected_username.lower()]
            
            if wrong_usernames:
                logger.warning(f"❌ Reply mentions wrong usernames: {wrong_usernames}")
                return False
            
            # Simplified relevance check - look for key overlap
            # Extract key terms from both tweets (remove common words)
            original_words = set(re.findall(r'\b\w+\b', original_tweet_text.lower()))
            reply_words = set(re.findall(r'\b\w+\b', reply_content.lower()))
            
            # Remove common stop words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'you', 'your', 'this', 'that', 'will', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could', 'would', 'should', 'may', 'might', 'must', 'shall', 'going', 'get', 'got', 'like', 'more', 'much', 'many', 'most', 'some', 'any', 'all', 'if', 'then', 'so', 'just', 'only', 'also', 'even', 'still', 'now', 'here', 'there', 'when', 'where', 'why', 'how', 'what', 'who', 'which', 'about', 'after', 'before', 'during', 'while', 'until', 'since', 'from', 'into', 'through', 'over', 'under', 'up', 'down', 'out', 'off', 'between', 'among', 'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'theirs'}
            
            original_words -= stop_words
            reply_words -= stop_words
            
            # Check for word overlap (crypto tweets often share tickers, technical terms)
            word_overlap = len(original_words & reply_words)
            
            # Check for crypto tickers specifically (high relevance indicator)
            crypto_tickers = re.findall(r'\$[A-Z]{2,6}', original_tweet_text.upper())
            ticker_overlap = any(ticker in reply_content.upper() for ticker in crypto_tickers)
            
            # More lenient validation - if there's good overlap or shared crypto context, it's likely relevant
            if word_overlap >= 2 or ticker_overlap or len(original_words & reply_words) > 0:
                logger.info(f"✅ WORD OVERLAP VALIDATION: Found {word_overlap} overlapping words, ticker overlap: {ticker_overlap}")
                return True
            
            # For very short tweets, be more lenient
            if len(original_tweet_text.split()) <= 10:
                logger.info("✅ SHORT TWEET VALIDATION: Being lenient with short tweets")
                return True
            
            # If basic checks fail, use AI but with more lenient instructions
            validation_prompt = f"""
            Original tweet: "{original_tweet_text}"
            Reply: "{reply_content}"
            
            IMPORTANT: This reply should be considered relevant if it:
            - References the same topic (crypto, trading, etc.)
            - Responds to the sentiment or question
            - Makes sense as a reaction to the original tweet
            - Shares context even if it's sarcastic or critical
            
            BE LENIENT - most crypto replies that mention similar topics are relevant.
            Answer YES if it makes sense as a response, NO only if it's completely unrelated.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are checking if a Twitter reply makes sense. Be LENIENT - if replies share context or respond to the topic, answer YES. Only say NO if completely unrelated."},
                    {"role": "user", "content": validation_prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            relevance_check = response.choices[0].message.content.strip().upper()
            is_relevant = "YES" in relevance_check
            
            logger.info(f"🤖 LENIENT AI relevance check: {relevance_check} - {'✅ PASS' if is_relevant else '❌ FAIL'}")
            
            return is_relevant
            
        except Exception as e:
            logger.error(f"❌ Error validating reply relevance: {e}")
            return True  # Default to allowing if validation fails

    def extract_tweet_author(self, tweet_element):
        """Extract the tweet author from a tweet element - helper method for validation."""
        try:
            # Use the same logic as in scroll_and_engage
            tweet_author = None
            try:
                # Method 1: Most specific - look for the author link in the tweet header area only
                username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"] [tabindex="-1"]')
                href = username_element.get_attribute('href')
                if href and '/' in href and not '/status/' in href:
                    tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                    if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                        return tweet_author
            except:
                pass
            
            # Method 2: Alternative header selector - target the profile link specifically
            if not tweet_author:
                try:
                    username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"] a[tabindex="-1"]')
                    href = username_element.get_attribute('href')
                    if href and '/' in href and not '/status/' in href:
                        tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                        if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                            return tweet_author
                except:
                    pass
            
            # Method 3: Look specifically in the tweet header div (most reliable area)
            if not tweet_author:
                try:
                    # Find the tweet header section first
                    header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                    # Then look for the first username link within that header only
                    username_links = header_section.find_elements(By.CSS_SELECTOR, 'a[href^="/"]')
                    
                    for link in username_links[:1]:  # Only check the first link in header
                        href = link.get_attribute('href')
                        if (href and '/' in href and 
                            not '/status/' in href and 
                            not '/notifications' in href and 
                            not '/messages' in href and
                            not '/home' in href and
                            not '/search' in href):
                            
                            potential_author = href.split('/')[-1].split('?')[0]  # Remove query params
                            if (potential_author and 
                                not potential_author.startswith('status') and
                                len(potential_author) > 0 and
                                not potential_author in ['i', 'compose', 'settings']):
                                
                                return potential_author
                except:
                    pass
            
            # Method 4: Fallback - look for span with username format @username in header area
            if not tweet_author:
                try:
                    header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"]')
                    username_spans = header_section.find_elements(By.TAG_NAME, 'span')
                    for span in username_spans:
                        text = span.text.strip()
                        if text.startswith('@') and len(text) > 1:
                            return text[1:]  # Remove @ symbol
                except:
                    pass
            
            return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting tweet author: {e}")
            return None

    def should_engage(self, tweet_text, username):
        """Decide whether to engage using personality system."""
        logger.info(f"🤔 Deciding whether to engage with @{username}")
        
        # Check blacklist
        if username in self.blacklisted_users:
            logger.info(f"❌ User @{username} is blacklisted")
            return False
        
        # Use personality-based engagement
        should_engage = should_engage_with_content(tweet_text)
        
        if should_engage:
            logger.info(f"🎯 ENGAGING - Tweet matches interests: {tweet_text[:50]}...")
        else:
            logger.info(f"🤷 NOT ENGAGING - Not interested in: {tweet_text[:50]}...")
        
        return should_engage
    
    def should_tweet_now(self):
        """Decide if it's a good time to tweet - pure AI mood."""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a chill person who likes tech and internet culture. Decide if you feel like tweeting something interesting. Answer YES or NO."},
                    {"role": "user", "content": "Do you feel like tweeting something right now? What's your mood?"}
                ],
                max_tokens=30,
                temperature=0.8
            )
            
            decision = response.choices[0].message.content.strip()
            should_tweet = "YES" in decision.upper() or "SURE" in decision.upper() or "YEAH" in decision.upper()
            
            logger.info(f"🎲 AI mood check: {decision}")
            return should_tweet
            
        except Exception as e:
            logger.error(f"❌ Error checking tweet mood: {e}")
            return random.random() < 0.3  # 30% fallback chance
    
    def should_update_bio(self):
        """Decide if it's time to update bio."""
        if not self.last_bio_update:
            return True
        
        time_since_update = datetime.now() - self.last_bio_update
        if time_since_update > timedelta(hours=6):  # Update bio every 6+ hours
            return random.random() < 0.3  # 30% chance
        
        return False
    
    def update_bio(self):
        """Update Twitter bio with new personality using improved navigation."""
        try:
            logger.info("📝 Updating bio...")
            new_bio = get_bio_update()
            logger.info(f"🎯 New bio content: {new_bio}")
            
            # Method 1: Try the direct profile edit URL
            logger.info("🔗 Trying direct profile settings URL...")
            self.driver.get("https://twitter.com/settings/profile")
            time.sleep(5)
            
            # Look for bio textarea with improved selectors
            bio_textarea = None
            bio_selectors = [
                'textarea[data-testid="bioTextarea"]',
                'textarea[name="description"]',
                'textarea[aria-label*="Bio"]',
                'textarea[aria-label*="bio"]',
                'textarea[placeholder*="bio"]',
                'textarea[placeholder*="Bio"]',
                'textarea[data-testid*="bio"]',
                'textarea[data-testid*="Bio"]',
                '#react-root textarea',
                'div[data-testid="bioTextarea"]',
                'div[contenteditable="true"][data-testid*="bio"]'
            ]
            
            for selector in bio_selectors:
                try:
                    bio_textarea = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Found bio textarea with selector: {selector}")
                    break
                except:
                    continue
            
            # Method 2: Try going through profile page first
            if not bio_textarea:
                logger.info("🔄 Trying profile page route...")
                self.driver.get(f"https://twitter.com/{TWITTER_USERNAME}")
                time.sleep(3)
                
                # Try to find and click "Edit profile" button
                try:
                    edit_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='Edit profile']/.." or By.CSS_SELECTOR, "[data-testid='editProfileButton']"))
                    )
                    edit_button.click()
                    time.sleep(3)
                    
                    # Now try to find bio textarea again
                    for selector in bio_selectors:
                        try:
                            bio_textarea = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            logger.info(f"✅ Found bio textarea via profile route with selector: {selector}")
                            break
                        except:
                            continue
                except Exception as edit_e:
                    logger.warning(f"⚠️ Could not find edit profile button: {edit_e}")
            
            # Method 3: Try alternative settings URLs
            if not bio_textarea:
                logger.info("🔄 Trying alternative settings routes...")
                alternative_urls = [
                    "https://twitter.com/settings/account",
                    "https://twitter.com/settings/profile/bio",
                    "https://x.com/settings/profile"
                ]
                
                for url in alternative_urls:
                    try:
                        self.driver.get(url)
                        time.sleep(4)
                        
                        for selector in bio_selectors:
                            try:
                                bio_textarea = self.wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                logger.info(f"✅ Found bio textarea via {url} with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if bio_textarea:
                            break
                    except:
                        continue
            
            if not bio_textarea:
                logger.error("❌ Could not find bio textarea after trying multiple methods")
                return False
            
            # Clear existing bio and enter new one
            bio_textarea.click()
            time.sleep(1)
            
            # Clear existing content using multiple methods
            try:
                bio_textarea.clear()
            except:
                # Fallback: select all and delete
                try:
                    bio_textarea.send_keys(Keys.CONTROL + "a")
                    bio_textarea.send_keys(Keys.DELETE)
                except:
                    pass
            
            time.sleep(1)
            
            # Type new bio
            bio_textarea.send_keys(new_bio)
            time.sleep(2)
            
            # Find and click save button with improved selectors
            save_button = None
            save_selectors = [
                '[data-testid="Profile_Save_Button"]',
                '[data-testid="settingsSaveBtn"]',
                'button[data-testid*="save"]',
                'button[data-testid*="Save"]',
                'div[data-testid*="save"]',
                'div[data-testid*="Save"]',
                'button[type="submit"]',
                'div[role="button"][aria-label*="Save"]',
                'button[aria-label*="Save"]'
            ]
            
            for selector in save_selectors:
                try:
                    save_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Found save button with selector: {selector}")
                    break
                except:
                    continue
            
            # Try XPath selectors for save button
            if not save_button:
                xpath_selectors = [
                    "//div[@role='button' and contains(text(), 'Save')]",
                    "//button[contains(text(), 'Save')]",
                    "//span[text()='Save']/parent::*",
                    "//div[contains(@aria-label, 'Save')]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        save_button = self.driver.find_element(By.XPATH, xpath)
                        logger.info(f"✅ Found save button with xpath: {xpath}")
                        break
                    except:
                        continue
            
            if not save_button:
                logger.error("❌ Could not find save button")
                return False
            
            # Click save button using JavaScript for better reliability
            try:
                save_button.click()
            except:
                # Fallback to JavaScript click
                self.driver.execute_script("arguments[0].click();", save_button)
            time.sleep(3)
            
            logger.info("✅ Bio updated successfully!")
            self.last_bio_update = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating bio: {e}")
            return False
    
    def follow_user(self, username):
        """Follow a user that Baggy finds interesting."""
        try:
            logger.info(f"👤 Following @{username}...")
            
            # Navigate to user's profile
            profile_url = f"https://twitter.com/{username}"
            logger.info(f"🔗 Navigating to {profile_url}")
            self.driver.get(profile_url)
            time.sleep(3)
            
            # Look for the follow button with multiple strategies
            follow_button = None
            follow_selectors = [
                '[data-testid="follow"]',
                '[data-testid*="follow"]',
                'div[role="button"]:has-text("Follow")',
                'button[aria-label*="Follow"]',
                'div[aria-label*="Follow"]',
                'span:has-text("Follow")',
                'button:has-text("Follow")'
            ]
            
            # Try CSS selectors first
            for selector in follow_selectors:
                try:
                    follow_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Found follow button with selector: {selector}")
                    break
                except:
                    continue
            
            # If CSS selectors fail, try XPath
            if not follow_button:
                xpath_selectors = [
                    "//div[@role='button' and contains(text(), 'Follow')]",
                    "//button[contains(text(), 'Follow')]",
                    "//span[text()='Follow']/parent::*/parent::*",
                    "//div[@data-testid='follow']",
                    "//div[contains(@aria-label, 'Follow')]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        follow_button = self.driver.find_element(By.XPATH, xpath)
                        logger.info(f"✅ Found follow button with xpath: {xpath}")
                        break
                    except:
                        continue
            
            if not follow_button:
                logger.warning(f"⚠️ Could not find follow button for @{username}")
                # Check if already following
                try:
                    following_indicators = [
                        '[data-testid="unfollow"]',
                        'div[role="button"]:has-text("Following")',
                        'button:has-text("Following")'
                    ]
                    
                    for indicator in following_indicators:
                        try:
                            following_button = self.driver.find_element(By.CSS_SELECTOR, indicator)
                            logger.info(f"✅ Already following @{username}")
                            return True
                        except:
                            continue
                except:
                    pass
                
                logger.error(f"❌ Could not find follow button and not already following @{username}")
                return False
            
            # Click the follow button
            try:
                # Scroll to make sure button is visible
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", follow_button)
                time.sleep(1)
                
                # Try regular click first
                follow_button.click()
                logger.info(f"✅ Clicked follow button for @{username}")
                
            except Exception as click_e:
                # Fallback to JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", follow_button)
                    logger.info(f"✅ JavaScript clicked follow button for @{username}")
                except Exception as js_e:
                    logger.error(f"❌ Failed to click follow button: {click_e}, {js_e}")
                    return False
            
            time.sleep(2)
            
            # Verify the follow action worked by checking if button changed
            try:
                # Look for "Following" button which indicates success
                following_check = self.driver.find_elements(By.XPATH, "//div[@role='button' and contains(text(), 'Following')]")
                if following_check:
                    logger.info(f"✅ Successfully followed @{username}!")
                    return True
                else:
                    # Sometimes it takes a moment to update, try once more
                    time.sleep(2)
                    following_check = self.driver.find_elements(By.XPATH, "//div[@role='button' and contains(text(), 'Following')]")
                    if following_check:
                        logger.info(f"✅ Successfully followed @{username}!")
                        return True
                    else:
                        logger.warning(f"⚠️ Follow button clicked but couldn't confirm follow status for @{username}")
                        return True  # Assume it worked
            except:
                logger.info(f"✅ Follow attempt completed for @{username} (couldn't verify)")
                return True
            
        except Exception as e:
            logger.error(f"❌ Error following user @{username}: {e}")
            return False
    
    def get_followers(self):
        """Get list of followers to potentially interact with."""
        try:
            logger.info("👥 Getting followers list...")
            # Use correct URL for followers
            self.driver.get(f"https://twitter.com/{TWITTER_USERNAME}/followers")
            time.sleep(5)
            
            followers = []
            try:
                # Use Selenium instead of BeautifulSoup for better element detection
                user_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]')
                
                if not user_elements:
                    # Try alternative selectors
                    user_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="UserCell"]')
                
                if not user_elements:
                    # Try even more generic approach
                    user_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[dir="ltr"]')
                
                logger.info(f"📊 Found {len(user_elements)} potential user elements")
                
                for user_elem in user_elements[:20]:  # Process first 20 elements
                    try:
                        # Try to find username links
                        username_links = user_elem.find_elements(By.CSS_SELECTOR, 'a[href^="/"][href!="/notifications"][href!="/messages"]')
                        
                        for link in username_links:
                            href = link.get_attribute('href')
                            if href and '/' in href:
                                potential_username = href.split('/')[-1]
                                # Filter out obvious non-usernames
                                if (potential_username and 
                                    not potential_username.startswith('status') and
                                    not potential_username in ['home', 'notifications', 'messages', 'explore'] and
                                    len(potential_username) > 0 and
                                    potential_username != TWITTER_USERNAME):
                                    
                                    if potential_username not in followers:
                                        followers.append(potential_username)
                                        logger.info(f"👤 Found follower: @{potential_username}")
                                    break
                    except Exception as e:
                        continue
                
                # If we still don't have followers, create a placeholder
                if not followers:
                    logger.info("📊 No followers detected, using engagement approach")
                    followers = ['placeholder_for_engagement']  # This prevents the 0 follower issue
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not parse followers: {e}")
                followers = ['placeholder_for_engagement']
            
            self.followers = followers
            logger.info(f"✅ Found {len(self.followers)} followers")
            return self.followers
            
        except Exception as e:
            logger.error(f"❌ Error getting followers: {e}")
            self.followers = ['placeholder_for_engagement']
            return self.followers
    
    def scroll_and_engage(self, tab="home"):
        """Scroll through timeline and selectively engage with threads."""
        try:
            if tab == "following":
                logger.info("📱 Scrolling through Following tab...")
                # Try multiple URLs for Following tab
                following_urls = [
                    "https://twitter.com/home/following",
                    "https://x.com/home/following", 
                    "https://twitter.com/following"
                ]
                
                success = False
                for url in following_urls:
                    try:
                        self.driver.get(url)
                        time.sleep(3)
                        
                        # Check if we successfully loaded the Following tab
                        # Look for Following tab indicator or tweets
                        tweets = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                        if tweets:
                            logger.info(f"✅ Successfully loaded Following tab via {url}")
                            success = True
                            break
                    except:
                        continue
                
                if not success:
                    logger.info("🔄 Trying to click Following tab manually...")
                    # Go to home and try to click the Following tab
                    self.driver.get("https://twitter.com/home")
                    time.sleep(2)
                    
                    try:
                        # Try to find and click the Following tab
                        following_tab_selectors = [
                            'a[href="/home/following"]',
                            'div[role="tab"]:has-text("Following")',
                            'span:has-text("Following")',
                            '[data-testid="AppTabBar_Home_Link"][aria-label*="Following"]'
                        ]
                        
                        clicked = False
                        for selector in following_tab_selectors:
                            try:
                                following_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                                following_tab.click()
                                time.sleep(3)
                                logger.info("✅ Successfully clicked Following tab")
                                clicked = True
                                break
                            except:
                                continue
                        
                        # Try XPath as backup
                        if not clicked:
                            xpath_selectors = [
                                "//span[text()='Following']/parent::*",
                                "//div[@role='tab' and contains(text(), 'Following')]",
                                "//a[contains(@href, 'following')]"
                            ]
                            
                            for xpath in xpath_selectors:
                                try:
                                    following_tab = self.driver.find_element(By.XPATH, xpath)
                                    following_tab.click()
                                    time.sleep(3)
                                    logger.info("✅ Successfully clicked Following tab via XPath")
                                    clicked = True
                                    break
                                except:
                                    continue
                        
                        if not clicked:
                            logger.warning("⚠️ Could not click Following tab, staying on For You")
                            tab = "home"
                        
                    except Exception as tab_e:
                        logger.warning(f"⚠️ Error clicking Following tab: {tab_e}, staying on For You")
                        tab = "home"
            else:
                logger.info("📱 Scrolling through For You timeline...")
                self.driver.get("https://twitter.com/home")
            
            time.sleep(2)
            
            # Scroll very few times to be ultra chill
            scrolls = random.randint(1, 2)  # Minimal scrolling (was 2-4)
            logger.info(f"📜 Will scroll {scrolls} times on {tab.upper()} tab")
            
            for scroll in range(scrolls):
                logger.info(f"📜 Scroll {scroll + 1}/{scrolls}")
                
                # Get tweet elements directly with Selenium
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                
                # Look at fewer tweets per scroll to reduce API calls
                for i, tweet_element in enumerate(tweet_elements[:3]):  # Check first 3 tweets each scroll (was 5)
                    try:
                        # Re-find the element to avoid stale reference
                        current_tweets = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                        if i >= len(current_tweets):
                            continue
                        tweet_element = current_tweets[i]
                        # Extract tweet info using Selenium
                        text_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                        
                        # Get the actual tweet author's username - improved accuracy
                        tweet_author = None
                        try:
                            # Method 1: Most specific - look for the author link in the tweet header area only
                            # This targets the actual tweet author, not mentions in content
                            username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"] [tabindex="-1"]')
                            href = username_element.get_attribute('href')
                            if href and '/' in href and not '/status/' in href:
                                tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                                    logger.debug(f"🎯 Method 1 - Found author: @{tweet_author}")
                        except:
                            pass
                        
                        # Method 2: Alternative header selector - target the profile link specifically
                        if not tweet_author:
                            try:
                                username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"] a[tabindex="-1"]')
                                href = username_element.get_attribute('href')
                                if href and '/' in href and not '/status/' in href:
                                    tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                    if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                                        logger.debug(f"🎯 Method 2 - Found author: @{tweet_author}")
                            except:
                                pass
                        
                        # Method 3: Look specifically in the tweet header div (most reliable area)
                        if not tweet_author:
                            try:
                                # Find the tweet header section first
                                header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                                # Then look for the first username link within that header only
                                username_links = header_section.find_elements(By.CSS_SELECTOR, 'a[href^="/"]')
                                
                                for link in username_links[:1]:  # Only check the first link in header
                                    href = link.get_attribute('href')
                                    if (href and '/' in href and 
                                        not '/status/' in href and 
                                        not '/notifications' in href and 
                                        not '/messages' in href and
                                        not '/home' in href and
                                        not '/search' in href):
                                        
                                        potential_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                        if (potential_author and 
                                            not potential_author.startswith('status') and
                                            len(potential_author) > 0 and
                                            not potential_author in ['i', 'compose', 'settings']):
                                            
                                            tweet_author = potential_author
                                            logger.debug(f"🎯 Method 3 - Found author: @{tweet_author}")
                                            break
                            except:
                                pass
                        
                        # Method 4: Fallback - look for span with username format @username in header area
                        if not tweet_author:
                            try:
                                header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"]')
                                username_spans = header_section.find_elements(By.TAG_NAME, 'span')
                                for span in username_spans:
                                    text = span.text.strip()
                                    if text.startswith('@') and len(text) > 1:
                                        tweet_author = text[1:]  # Remove @ symbol
                                        logger.debug(f"🎯 Method 4 - Found author from @text: @{tweet_author}")
                                        break
                            except:
                                pass
                        
                        if text_elem and tweet_author:
                            tweet_text = text_elem.text.strip()
                            username = tweet_author
                            
                            # Skip our own tweets
                            if username.lower() == TWITTER_USERNAME.lower():
                                logger.info(f"🚫 Skipping our own tweet: {tweet_text[:50]}...")
                                continue
                            
                            # Create a unique identifier for this tweet to prevent duplicate engagement
                            tweet_id = f"{username}:{hash(tweet_text[:100])}"  # Use username + text hash
                            
                            # Skip if we've already engaged with this tweet
                            if tweet_id in self.engaged_tweets:
                                logger.info(f"🔄 Already engaged with @{username}'s tweet: {tweet_text[:30]}...")
                                continue
                            
                            logger.info(f"👀 Looking at tweet from @{username}: {tweet_text[:50]}...")
                            logger.info(f"🎯 CONFIRMED AUTHOR: @{username} - Will reply to this user specifically")
                            
                            # Check if it's a thread (simplified check)
                            is_thread = "Show this thread" in tweet_element.get_attribute('innerHTML') or "🧵" in tweet_text
                            
                            if is_thread:
                                logger.info("🧵 Thread detected!")
                                # Use thread content for engagement decision
                                should_engage = self.should_engage_with_thread(tweet_text)
                                content_to_analyze = tweet_text
                            else:
                                # Regular tweet engagement
                                should_engage = self.should_engage(tweet_text, username)
                                content_to_analyze = tweet_text
                            
                            if should_engage:
                                # Determine engagement style based on content
                                engagement_style = get_engagement_style(content_to_analyze)
                                
                                                # Choose engagement type - heavily favor likes over API-heavy replies
                                engagement_type = random.choices(
                                    ['like', 'reply', 'retweet', 'follow'], 
                                    weights=[60, 15, 20, 5]  # Heavily favor likes (no API calls)
                                )[0]
                                
                                # For retweets, do additional content check
                                if engagement_type == 'retweet':
                                    if not should_retweet_content(tweet_text):
                                        logger.info("🔄 Content not worthy of retweet, switching to like")
                                        engagement_type = 'like'
                                
                                logger.info(f"🎯 Engaging with {engagement_type} on {'thread' if is_thread else 'tweet'}")
                                
                                # Mark this tweet as engaged with BEFORE attempting engagement
                                self.engaged_tweets.add(tweet_id)
                                
                                if engagement_type == 'like':
                                    self.like_tweet(tweet_element)
                                    time.sleep(random.randint(2, 5))
                                elif engagement_type == 'reply':
                                    # Final validation before replying - ensure we have the right tweet element
                                    logger.info(f"🎯 FINAL CHECK: About to reply to @{username} for tweet: {tweet_text[:50]}...")
                                    
                                    # Re-confirm we're looking at the right tweet by checking the username again
                                    try:
                                        # Scroll to make sure the tweet is still visible and clickable
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_element)
                                        time.sleep(1)
                                        
                                        # Double-check we have the right username from this specific tweet element
                                        confirmation_author = self.extract_tweet_author(tweet_element)
                                        if confirmation_author and confirmation_author.lower() == username.lower():
                                            logger.info(f"✅ CONFIRMED: Tweet element matches expected author @{username}")
                                            # Use the proper reply function with tweet element
                                            self.reply_to_tweet(tweet_element, tweet_text, username, engagement_style)
                                        else:
                                            logger.error(f"❌ MISMATCH: Tweet element shows @{confirmation_author} but expected @{username}")
                                            logger.error("❌ Skipping reply to prevent wrong user reply")
                                    except Exception as validation_e:
                                        logger.error(f"❌ Error validating tweet element: {validation_e}")
                                        logger.error("❌ Skipping reply for safety")
                                    
                                    time.sleep(random.randint(30, 60))  # Longer wait after replies
                                elif engagement_type == 'retweet':
                                    # Retweet the tweet (already passed content check)
                                    if self.retweet_tweet(tweet_element):
                                        logger.info("✅ Successfully retweeted content")
                                    time.sleep(random.randint(5, 10))
                                elif engagement_type == 'follow':
                                    self.follow_user(username)
                                    time.sleep(random.randint(3, 8))
                            else:
                                logger.info(f"🤷 Not engaging with @{username}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error processing tweet: {e}")
                        continue
                
                # Natural scrolling behavior
                scroll_amount = random.randint(400, 1200)
                self.driver.execute_script(f"window.scrollTo(0, window.pageYOffset + {scroll_amount});")
                
                # Slower, more natural reading pace
                time.sleep(random.randint(5, 15))  # Longer pauses between scrolls
                
        except Exception as e:
            logger.error(f"❌ Error scrolling timeline: {e}")
    
    def like_tweet(self, tweet_element):
        """Like a tweet."""
        try:
            # Find and click the like button
            like_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
            like_button.click()
            logger.info("❤️  Liked a tweet")
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error liking tweet: {e}")
    
    def retweet_tweet(self, tweet_element):
        """Retweet a tweet."""
        try:
            logger.info("🔄 Retweeting a tweet...")
            
            # Find and click the retweet button
            retweet_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
            retweet_button.click()
            time.sleep(2)
            
            # Handle the retweet modal - look for "Retweet" confirmation button
            try:
                # Try to find the retweet confirmation button in the modal
                retweet_confirm_selectors = [
                    '[data-testid="retweetConfirm"]',
                    'div[role="menuitem"][data-testid="retweetConfirm"]',
                    'div[role="menuitem"]:first-child',  # Usually the first option
                    'span:contains("Retweet")'
                ]
                
                retweet_confirmed = False
                for selector in retweet_confirm_selectors:
                    try:
                        confirm_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        confirm_button.click()
                        retweet_confirmed = True
                        break
                    except:
                        continue
                
                if retweet_confirmed:
                    logger.info("✅ Tweet retweeted successfully!")
                    time.sleep(2)
                    return True
                else:
                    logger.error("❌ Could not find retweet confirmation button")
                    return False
                    
            except Exception as modal_e:
                logger.error(f"❌ Error with retweet modal: {modal_e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error retweeting tweet: {e}")
            return False
    
    def post_tweet(self, content):
        """Post a tweet with validation."""
        try:
            if not self.logged_in:
                logger.error("❌ Not logged in to Twitter")
                return False
            
            logger.info(f"📝 Posting tweet: {content}")
            
            # Navigate to home and wait for load
            self.driver.get("https://twitter.com/home")
            time.sleep(3)
            
            # Try multiple strategies to find the tweet textarea
            tweet_textarea = None
            selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea_1"]',
                '.public-DraftEditor-content',
                '[aria-label="Post text"]'
            ]
            
            for selector in selectors:
                try:
                    tweet_textarea = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not tweet_textarea:
                logger.error("❌ Could not find tweet textarea")
                return False
            
            # Clear any existing content and type new content
            tweet_textarea.click()
            time.sleep(1)
            tweet_textarea.clear()
            tweet_textarea.send_keys(content)
            
            time.sleep(2)
            
            # Try multiple selectors for the tweet button
            tweet_button = None
            button_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                '[data-testid="sendTweet"]',
                'div[role="button"][aria-label="Post"]'
            ]
            
            for selector in button_selectors:
                try:
                    tweet_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not tweet_button:
                logger.error("❌ Could not find tweet button")
                return False
            
            tweet_button.click()
            
            self.last_tweet_time = datetime.now()
            logger.info("✅ Tweet posted successfully!")
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting tweet: {e}")
            return False
    
    def reply_to_tweet(self, tweet_element, tweet_text, username, engagement_style="roasting"):
        """Generate and post a proper reply using the reply interface with validation."""
        try:
            logger.info(f"💬 Replying to @{username} with {engagement_style} style")
            logger.info(f"📋 Original tweet content: {tweet_text}")
            
            # Generate reply based on engagement style and personality - RESPOND TO THE ACTUAL CONTENT
            if engagement_style == "relatable_life_roast":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a funny, relatable reply that sympathizes with their struggle but roasts them gently. Be supportive but with humor. Respond directly to their content. Do NOT mention any other usernames."
            elif engagement_style == "dating_comedy":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a funny reply about dating/relationships that responds to what @{username} said. Be humorous but not mean-spirited. Address their actual content. Do NOT mention any other usernames."
            elif engagement_style == "entertainment_banter":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a fun, engaging reply about movies/TV/entertainment that directly responds to what @{username} said. Be conversational and entertaining. Do NOT mention any other usernames."
            elif engagement_style == "lifestyle_jokes":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a playful, funny reply about food/coffee/lifestyle that responds to what @{username} said. Be light-hearted and relatable. Do NOT mention any other usernames."
            elif engagement_style == "gaming_banter":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a funny gaming-related reply that responds to what @{username} said. Use gamer humor but be engaging. Do NOT mention any other usernames."
            elif engagement_style == "wholesome_funny":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a wholesome but funny reply about pets/animals that responds to what @{username} said. Be positive and humorous. Do NOT mention any other usernames."
            elif engagement_style == "helpful_sarcasm":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a helpful but slightly sarcastic reply that actually answers their question or responds to their content. Be useful but with humor. Do NOT mention any other usernames."
            elif engagement_style == "opinion_roast":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a funny reply that playfully roasts their opinion while responding to what @{username} said. Be witty but not too harsh. Do NOT mention any other usernames."
            elif engagement_style == "financial_destruction":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a savage reply that directly responds to what @{username} said, mocking their financial decisions. Be brutal but relevant to their actual words. Do NOT mention any other usernames."
            elif engagement_style == "crypto_annihilation":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a savage reply that directly responds to what @{username} said, calling out their crypto delusions. Be brutal but address their content. Do NOT mention any other usernames."
            elif engagement_style == "skill_issue":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a savage reply that directly responds to what @{username} said, calling it a skill issue. Be brutal but respond to their actual words. Do NOT mention any other usernames."
            elif engagement_style == "rare_respect":
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a reply that actually respects what @{username} said, acknowledging they're based. Be positive but still edgy, responding to their actual content. Do NOT mention any other usernames."
            else:
                prompt = f"IMPORTANT: You are replying to @{username} who posted: '{tweet_text}'. Write a funny, engaging reply that directly responds to what @{username} said. Be humorous and relatable but make sure your reply makes sense as a response to their content. Do NOT mention any other usernames."
            
            reply_content = self.generate_content(prompt, "reply")
            
            if reply_content:
                # Validate that the reply is actually relevant to this specific tweet and user
                if not self.validate_reply_relevance(reply_content, tweet_text, username):
                    logger.warning(f"⚠️ Generated reply not relevant to @{username}'s tweet, regenerating...")
                    
                    # Try again with even more specific prompt
                    enhanced_prompt = f"CRITICAL: Reply ONLY to @{username}'s tweet: '{tweet_text}'. Your reply must reference what they said about '{tweet_text[:30]}...' and be a direct response. Do not mention other users or unrelated content."
                    reply_content = self.generate_content(enhanced_prompt, "reply")
                    
                    # Final validation
                    if reply_content and not self.validate_reply_relevance(reply_content, tweet_text, username):
                        logger.error(f"❌ Still generating irrelevant replies, skipping @{username}")
                        return False
                
                if reply_content:
                    # Remove any existing @username from the content to avoid duplicates
                    reply_content = re.sub(f'^@{username}\\s*', '', reply_content)
                    
                    # Now add @username at the start
                    reply_content = f"@{username} {reply_content}"
                    
                    logger.info(f"📝 Final validated reply content: {reply_content}")
                    logger.info(f"🎯 Confirmed replying to: @{username}")
                    return self.post_actual_reply(tweet_element, reply_content)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error replying to tweet: {e}")
            return False
    
    def post_actual_reply(self, tweet_element, content):
        """Post an actual reply using the Twitter reply interface with validation."""
        try:
            logger.info(f"🔗 Posting actual reply: {content}")
            
            # Final safety check - extract expected username from content
            username_match = re.search(r'^@(\w+)', content)
            if username_match:
                expected_username = username_match.group(1)
                logger.info(f"🎯 Final check: Posting reply to @{expected_username}")
            else:
                logger.warning("⚠️ No username found in reply content - this might be an issue")
                return False
            
            # ENHANCED STRATEGY: Use the tweet element directly to click its specific reply button
            try:
                # Scroll to ensure the tweet element is visible and clickable
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_element)
                time.sleep(2)
                
                # Find the reply button within this specific tweet element
                reply_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                
                # JavaScript click to bypass any interception
                logger.info(f"🎯 Clicking reply button for @{expected_username}'s specific tweet")
                self.driver.execute_script("arguments[0].click();", reply_button)
                logger.info("✅ Used JavaScript click on specific tweet's reply button")
                time.sleep(3)
                
            except Exception as click_e:
                logger.warning(f"⚠️ Failed to click specific tweet reply button: {click_e}")
                logger.info("🚫 Could not click reply button, skipping reply")
                return False
            
            # Wait for the reply modal to appear and validate it's for the right tweet
            try:
                # Look for the "Replying to" indicator in the reply modal
                replying_to_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Replying to')]"))
                )
                
                # Find the username in the "Replying to @username" text
                replying_to_text = replying_to_element.text
                logger.info(f"📋 Reply modal shows: {replying_to_text}")
                
                # Validate we're replying to the correct user
                if expected_username.lower() not in replying_to_text.lower():
                    logger.error(f"❌ Reply modal mismatch: Expected @{expected_username}, got {replying_to_text}")
                                    # Close the modal and skip reply
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="app-bar-close"]')
                    close_button.click()
                    time.sleep(1)
                except:
                    pass
                logger.info("🚫 Reply modal mismatch, skipping reply")
                return False
                
                logger.info(f"✅ VALIDATED: Reply modal confirmed for @{expected_username}")
                
            except Exception as validation_e:
                logger.warning(f"⚠️ Could not validate reply modal: {validation_e}")
                # Continue anyway but with caution
            
            # Find the reply textarea
            reply_textarea = None
            textarea_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea_1"]', 
                '.public-DraftEditor-content',
                '[role="textbox"]'
            ]
            
            for selector in textarea_selectors:
                try:
                    reply_textarea = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not reply_textarea:
                logger.error("❌ Could not find reply textarea, skipping reply")
                return False
            
            # Clear and type the reply content
            reply_textarea.click()
            time.sleep(1)
            reply_textarea.clear()
            reply_textarea.send_keys(content)
            
            time.sleep(2)
            
            # Final validation: Check the content in the textarea matches what we expect
            try:
                typed_content = reply_textarea.get_attribute('value') or reply_textarea.text or reply_textarea.get_attribute('textContent')
                logger.info(f"🔍 Textarea content check: '{typed_content}'")
                
                # More lenient validation - just check if content was typed successfully
                if len(typed_content.strip()) > 0:
                    logger.info("✅ Textarea content validated - content was typed successfully")
                else:
                    logger.warning("⚠️ Textarea appears empty, but continuing anyway")
            except Exception as validation_e:
                logger.warning(f"⚠️ Could not validate textarea content: {validation_e}, continuing anyway")
            
            # Find and click the reply button to post
            post_reply_button = None
            button_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                'div[role="button"][data-testid="tweetButtonInline"]',
                'button[data-testid="tweetButton"]'
            ]
            
            for selector in button_selectors:
                try:
                    post_reply_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    # Check if button is enabled
                    if post_reply_button.get_attribute('aria-disabled') != 'true':
                        break
                except:
                    continue
            
            if not post_reply_button or post_reply_button.get_attribute('aria-disabled') == 'true':
                logger.error("❌ Could not find enabled reply post button, skipping reply")
                return False
            
            # Final confirmation before posting
            logger.info(f"🚀 About to post reply to @{expected_username}: {content[:50]}...")
            post_reply_button.click()
            
            logger.info("✅ Reply posted successfully!")
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting actual reply: {e}")
            logger.info("🔄 Reply interface failed, skipping reply")
            return False
    
    def compose_mention_reply(self, content):
        """Fallback method - compose a new tweet as a mention/reply."""
        try:
            logger.info("📝 Using compose method as reply fallback")
            
            # Navigate to home and use the main compose box
            self.driver.get("https://twitter.com/home")
            time.sleep(3)
            
            # Find the main tweet compose box
            tweet_textarea = None
            selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea_1"]',
                '.public-DraftEditor-content',
                '[aria-label="Post text"]'
            ]
            
            for selector in selectors:
                try:
                    tweet_textarea = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not tweet_textarea:
                logger.error("❌ Could not find compose textarea")
                return False
            
            # Type the content (which should already include @username)
            tweet_textarea.click()
            time.sleep(1)
            tweet_textarea.clear()
            tweet_textarea.send_keys(content)
            
            time.sleep(2)
            
            # Find and click post button
            post_button = None
            button_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                'div[role="button"]:has-text("Post")'
            ]
            
            for selector in button_selectors:
                try:
                    post_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not post_button:
                logger.error("❌ Could not find post button")
                return False
            
            post_button.click()
            logger.info("✅ Posted mention reply successfully!")
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in compose mention reply: {e}")
            return False
    
    def check_mentions(self):
        """Check for mentions and respond selectively to newer, non-spam mentions."""
        try:
            logger.info("🔔 Checking mentions...")
            self.driver.get("https://twitter.com/notifications/mentions")
            time.sleep(3)
            
            # Use Selenium to find tweets instead of BeautifulSoup for better element handling
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            
            processed_mentions = 0
            for tweet_element in tweet_elements[:5]:  # Check first 5 mentions
                try:
                    # Extract tweet text and username using Selenium
                    try:
                        text_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                        mention_text = text_elem.text.strip()
                    except:
                        logger.warning("⚠️  Could not extract tweet text from mention")
                        continue
                    
                    try:
                        # Get the actual tweet author's username - improved accuracy (same as timeline)
                        tweet_author = None
                        try:
                            # Method 1: Most specific - look for the author link in the tweet header area only
                            username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"] [tabindex="-1"]')
                            href = username_element.get_attribute('href')
                            if href and '/' in href and not '/status/' in href:
                                tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                                    logger.debug(f"🎯 Mention Method 1 - Found author: @{tweet_author}")
                        except:
                            pass
                        
                        # Method 2: Alternative header selector - target the profile link specifically
                        if not tweet_author:
                            try:
                                username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"] a[tabindex="-1"]')
                                href = username_element.get_attribute('href')
                                if href and '/' in href and not '/status/' in href:
                                    tweet_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                    if tweet_author and not tweet_author.startswith('status') and len(tweet_author) > 0:
                                        logger.debug(f"🎯 Mention Method 2 - Found author: @{tweet_author}")
                            except:
                                pass
                        
                        # Method 3: Look specifically in the tweet header div (most reliable area)
                        if not tweet_author:
                            try:
                                # Find the tweet header section first
                                header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                                # Then look for the first username link within that header only
                                username_links = header_section.find_elements(By.CSS_SELECTOR, 'a[href^="/"]')
                                
                                for link in username_links[:1]:  # Only check the first link in header
                                    href = link.get_attribute('href')
                                    if (href and '/' in href and 
                                        not '/status/' in href and 
                                        not '/notifications' in href and 
                                        not '/messages' in href and
                                        not '/home' in href and
                                        not '/search' in href):
                                        
                                        potential_author = href.split('/')[-1].split('?')[0]  # Remove query params
                                        if (potential_author and 
                                            not potential_author.startswith('status') and
                                            len(potential_author) > 0 and
                                            not potential_author in ['i', 'compose', 'settings']):
                                            
                                            tweet_author = potential_author
                                            logger.debug(f"🎯 Mention Method 3 - Found author: @{tweet_author}")
                                            break
                            except:
                                pass
                        
                        # Method 4: Fallback - look for span with username format @username in header area
                        if not tweet_author:
                            try:
                                header_section = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"]')
                                username_spans = header_section.find_elements(By.TAG_NAME, 'span')
                                for span in username_spans:
                                    text = span.text.strip()
                                    if text.startswith('@') and len(text) > 1:
                                        tweet_author = text[1:]  # Remove @ symbol
                                        logger.debug(f"🎯 Mention Method 4 - Found author from @text: @{tweet_author}")
                                        break
                            except:
                                pass
                        
                        if not tweet_author:
                            logger.warning("⚠️  Could not extract username from mention")
                            continue
                        
                        username = tweet_author
                        
                        # Don't reply to our own mentions (but do process mentions of us)
                        if username.lower() == TWITTER_USERNAME.lower():
                            logger.info(f"🚫 Skipping mention from ourselves: @{username}")
                            continue
                        
                        # Create unique identifier for this mention to prevent duplicate replies
                        mention_id = f"mention:{username}:{hash(mention_text[:100])}"
                        
                        # Skip if we've already replied to this mention
                        if mention_id in self.engaged_tweets:
                            logger.info(f"🔄 Already replied to @{username}'s mention: {mention_text[:30]}...")
                            continue
                            
                    except:
                        logger.warning("⚠️  Could not extract username from mention")
                        continue
                    
                    logger.info(f"📩 Mention from @{username}: {mention_text[:50]}...")
                    
                    # SPAM FILTER - Skip obvious spam mentions
                    spam_indicators = [
                        "click here", "follow for follow", "dm me", "check this out",
                        "free money", "guaranteed profit", "investment opportunity",
                        "you're in the spotlight", "start your", "limited time"
                    ]
                    
                    if any(spam in mention_text.lower() for spam in spam_indicators):
                        logger.info(f"🚫 Skipping spam mention from @{username}")
                        continue
                    
                    # Skip mentions that are too short or just @mentions
                    if len(mention_text.strip()) < 10 or mention_text.strip().startswith('@'):
                        logger.info(f"🚫 Skipping low-quality mention from @{username}")
                        continue
                    
                    # Check if mention is part of a thread
                    is_thread = self.is_thread_tweet(tweet_element)
                    
                    if is_thread:
                        logger.info("🧵 Mention is part of a thread!")
                        thread_content = self.read_thread(tweet_element)
                        should_engage = self.should_engage_with_thread(thread_content)
                        content_to_analyze = thread_content
                    else:
                        should_engage = self.should_engage(mention_text, username)
                        content_to_analyze = mention_text
                    
                    if should_engage:
                        # Mark this mention as engaged with BEFORE attempting engagement
                        self.engaged_tweets.add(mention_id)
                        
                        engagement_style = get_engagement_style(content_to_analyze)
                        
                        if is_thread:
                            # Thread-aware mention reply - use actual reply function
                            reply_content = self.generate_thread_response(thread_content, username, engagement_style)
                            if reply_content:
                                # Validate thread reply relevance
                                if self.validate_reply_relevance(reply_content, thread_content, username):
                                    # Include @username in the reply content for fallback method
                                    full_reply = f"@{username} {reply_content}"
                                    self.post_actual_reply(tweet_element, full_reply)
                                    logger.info(f"🧵 Replied to thread mention from @{username}")
                                else:
                                    logger.warning(f"⚠️ Thread reply not relevant to @{username}, skipping")
                        else:
                            # Regular mention reply - use proper reply function with tweet element (already has validation)
                            self.reply_to_tweet(tweet_element, mention_text, username, engagement_style)
                            logger.info(f"💬 Replied to mention from @{username}")
                        
                        processed_mentions += 1
                        time.sleep(random.randint(15, 45))
                        
                        # Limit to 2 replies per cycle to avoid spam
                        if processed_mentions >= 2:
                            logger.info("✅ Processed maximum mentions for this cycle")
                            break
            
                except Exception as e:
                    logger.error(f"❌ Error processing mention: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error checking mentions: {e}")
    
    def create_original_tweet(self):
        """Generate and post a single original tweet using personality system."""
        try:
            logger.info("🐦 Creating single original tweet...")
            
            # Use personality system for single tweet generation
            prompt = get_random_tweet_prompt()
            content = self.generate_content(prompt, "original tweet")
            
            if content:
                return self.post_tweet(content)
            return False
            
        except Exception as e:
            logger.error(f"❌ Error creating original tweet: {e}")
            return False
    
    def cleanup_engagement_history(self):
        """Clean up old engagement history to prevent memory bloat."""
        if len(self.engaged_tweets) > 1000:  # If we have more than 1000 engaged tweets
            # Keep only the most recent 500 to prevent duplicate engagement in current session
            # but allow re-engagement with very old tweets
            logger.info(f"🧹 Cleaning up engagement history: {len(self.engaged_tweets)} -> 500")
            # Convert to list, keep last 500, convert back to set
            recent_engagements = list(self.engaged_tweets)[-500:]
            self.engaged_tweets = set(recent_engagements)
            
    def run_intelligent_cycle(self):
        """Run one cycle of intelligent bot behavior - focused on engagement."""
        logger.info("🔄 Starting intelligent cycle...")
        
        # Clean up engagement history periodically
        self.cleanup_engagement_history()
        
        # Randomly choose what to do - MUCH more selective to reduce API calls
        actions = []
        
        # Tweet extremely rarely (only 5% of the time)
        if self.should_tweet_now() and random.random() < 0.05:
            actions.append("tweet")
        
        # Check mentions even less frequently
        if random.random() < 0.2:  # 20% chance (was 40%)
            actions.append("mentions")
        
        # Scroll and engage much less frequently
        if random.random() < 0.4:  # 40% chance (was 70%)
            tab_choice = random.choice(["home", "following"])
            actions.append(("engage", tab_choice))
        
        # Update bio extremely rarely
        if self.should_update_bio() and random.random() < 0.1:  # Only 10% of the time when eligible
            actions.append("bio")
        
        # Execute chosen actions
        for action in actions:
            try:
                if action == "tweet":
                    logger.info("🐦 Creating single original tweet...")
                    self.create_original_tweet()
                    time.sleep(random.randint(120, 300))  # Much longer wait after tweeting (2-5 minutes)
                elif action == "mentions":
                    logger.info("🔔 Checking mentions...")
                    self.check_mentions()
                    time.sleep(random.randint(60, 120))  # Much longer wait after checking mentions (1-2 minutes)
                elif isinstance(action, tuple) and action[0] == "engage":
                    tab = action[1]
                    logger.info(f"📱 Scrolling and engaging with others on {tab.upper()} tab...")
                    self.scroll_and_engage(tab=tab)
                    # No wait - continuous scrolling
                elif action == "bio":
                    logger.info("📝 Updating bio...")
                    self.update_bio()
                    time.sleep(random.randint(60, 180))  # Much longer wait after bio update (1-3 minutes)
                    
            except Exception as e:
                logger.error(f"❌ Error in action {action}: {e}")
        
        logger.info("✅ Cycle completed")
    
    def run(self):
        """Main function to run the intelligent bot."""
        logger.info("🚀 Starting Intelligent Baggy Moonz Twitter Bot...")
        
        # Check credentials
        if not TWITTER_USERNAME or not TWITTER_PASSWORD:
            logger.error("❌ Twitter credentials not found")
            return
        
        if not OPENAI_API_KEY:
            logger.error("❌ OpenAI API key not found")
            return
        
        try:
            # Set up browser and login
            self.setup_driver()
            self.login_to_twitter()
            
            if not self.logged_in:
                logger.error("❌ Failed to log in to Twitter")
                return
            
            # Get initial followers
            self.get_followers()
            
            # Post initial tweet
            logger.info("🎯 Posting initial tweet...")
            self.create_original_tweet()
            
            # Main loop - continuously active
            logger.info("🔄 Starting continuous behavior loop...")
            while True:
                try:
                    # Run intelligent cycle immediately - no waiting
                    self.run_intelligent_cycle()
                    
                    # Very long pause to be extremely chill and natural
                    time.sleep(random.randint(300, 900))  # 5-15 minutes between cycles
                    
                except KeyboardInterrupt:
                    logger.info("👋 Bot stopped by user")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    time.sleep(10)  # Brief wait before retrying
                    
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🖥 Browser closed")

    def read_thread(self, tweet_element):
        """Read the full thread context for better responses."""
        try:
            logger.info("📖 Reading thread context...")
            
            # Find thread indicators
            thread_context = []
            
            # Get the main tweet text
            text_elem = tweet_element.find('div', {'data-testid': 'tweetText'})
            if text_elem:
                main_tweet = text_elem.get_text(strip=True)
                thread_context.append(main_tweet)
            
            # Look for "Show this thread" or thread continuation indicators
            thread_indicators = tweet_element.find_all(string=lambda text: text and 
                any(indicator in text.lower() for indicator in 
                    ["show this thread", "thread", "1/", "2/", "3/", "🧵"]))
            
            if thread_indicators:
                logger.info("🧵 Thread detected, reading full context...")
                
                # Try to click "Show this thread" if available
                try:
                    show_thread_link = tweet_element.find('a', string=lambda text: 
                        text and "show this thread" in text.lower())
                    if show_thread_link:
                        # In a real implementation, we'd click and read the full thread
                        logger.info("🔗 Would click 'Show this thread' link")
                except:
                    pass
                
                # For now, we'll simulate reading a thread by looking at nearby tweets
                # In a real implementation, this would navigate to the full thread
                
            return " ".join(thread_context) if len(thread_context) > 1 else thread_context[0] if thread_context else ""
            
        except Exception as e:
            logger.error(f"❌ Error reading thread: {e}")
            return ""
    
    def is_thread_tweet(self, tweet_element):
        """Check if a tweet is part of a thread."""
        try:
            # Look for thread indicators
            tweet_html = str(tweet_element)
            thread_indicators = [
                "show this thread",
                "🧵",
                "/",  # Like "1/5", "2/10"
                "thread",
                "continue reading",
                "read more"
            ]
            
            return any(indicator in tweet_html.lower() for indicator in thread_indicators)
            
        except Exception as e:
            logger.error(f"❌ Error checking if thread: {e}")
            return False
    
    def should_engage_with_thread(self, thread_content):
        """Decide if we should engage with a thread based on full context."""
        # Use personality system but consider full thread context
        should_engage = should_engage_with_content(thread_content)
        
        # Threads often have more context, so be slightly more likely to engage
        if should_engage and len(thread_content) > 200:  # Long threads
            boost_chance = random.random() < 0.3  # 30% boost
            if boost_chance:
                logger.info("🧵 Thread engagement boost applied")
                return True
        
        return should_engage
    
    def generate_thread_response(self, thread_content, username, engagement_style="agreement"):
        """Generate a response considering the full thread context."""
        try:
            logger.info(f"🧵 Generating thread response to @{username}")
            
            # Different prompts based on engagement style and thread nature
            if engagement_style == "tech":
                prompt = f"Reply to @{username}'s tech thread: '{thread_content}' - share your knowledge or experience casually considering the full context"
            elif engagement_style == "curious":
                prompt = f"Reply to @{username}'s thread: '{thread_content}' - ask a follow-up question or show interest in the thread topic"
            elif engagement_style == "funny":
                prompt = f"Reply to @{username}'s thread: '{thread_content}' - be playful and engaging, considering the full thread context"
            elif engagement_style == "disagreement":
                prompt = f"Reply to @{username}'s thread: '{thread_content}' - politely offer a different perspective on the thread topic"
            else:
                prompt = f"Reply to @{username}'s thread: '{thread_content}' - engage naturally and conversationally with the full thread context"
            
            return self.generate_content(prompt, "thread reply")
            
        except Exception as e:
            logger.error(f"❌ Error generating thread response: {e}")
            return None
    
    def continue_thread(self, original_tweet_content):
        """Continue someone else's thread with our own take."""
        try:
            logger.info("🧵 Continuing thread...")
            
            prompt = f"Add your thoughts to this thread: '{original_tweet_content}'. Be conversational and engaging. Share your perspective or ask a follow-up question."
            
            continuation = self.generate_content(prompt, "thread continuation")
            
            if continuation:
                return self.post_tweet(continuation)
            return False
            
        except Exception as e:
            logger.error(f"❌ Error continuing thread: {e}")
            return False
    
    def should_create_thread(self):
        """Always return False - we don't create our own threads anymore."""
        logger.info("🚫 Thread creation disabled - focusing on single tweets and replies")
        return False
    
    def create_thread(self):
        """Thread creation disabled - just create a single tweet instead."""
        logger.info("🚫 Thread creation disabled, creating single tweet instead")
        return self.create_original_tweet()
    
    def reply_to_own_tweet(self, content):
        """Reply to the bot's own most recent tweet with multiple strategies."""
        try:
            logger.info(f"🔗 Replying to own tweet: {content}")
            
            # STRATEGY 1: Go to our profile to find the latest tweet
            logger.info("📱 Going to profile to find latest tweet...")
            self.driver.get(f"https://twitter.com/{TWITTER_USERNAME}")
            time.sleep(4)
            
            # Find our latest tweet on our profile
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            
            if tweet_elements:
                latest_tweet = tweet_elements[0]  # First tweet should be our latest
                logger.info("📍 Found our latest tweet on profile")
                
                try:
                    # Scroll to the tweet and use JavaScript click
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", latest_tweet)
                    time.sleep(2)
                    
                    # Find the reply button and use JavaScript click to avoid interception
                    reply_button = latest_tweet.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                    self.driver.execute_script("arguments[0].click();", reply_button)
                    time.sleep(3)
                    
                    # Find the reply textarea with multiple strategies
                    reply_textarea = None
                    textarea_selectors = [
                        '[data-testid="tweetTextarea_0"]',
                        '[data-testid="tweetTextarea_1"]',
                        '.public-DraftEditor-content',
                        '[role="textbox"]'
                    ]
                    
                    for selector in textarea_selectors:
                        try:
                            reply_textarea = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if not reply_textarea:
                        logger.error("❌ Could not find reply textarea")
                        return self.use_compose_for_thread(content)
                    
                    # Type the content
                    reply_textarea.click()
                    time.sleep(1)
                    reply_textarea.clear()
                    reply_textarea.send_keys(content)
                    time.sleep(2)
                    
                    # Find and click post button
                    post_button = None
                    button_selectors = [
                        '[data-testid="tweetButtonInline"]',
                        '[data-testid="tweetButton"]',
                        'div[role="button"]:has-text("Reply")',
                        'div[role="button"]:has-text("Post")'
                    ]
                    
                    for selector in button_selectors:
                        try:
                            post_button = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if not post_button:
                        logger.error("❌ Could not find post button")
                        return self.use_compose_for_thread(content)
                    
                    post_button.click()
                    logger.info("✅ Reply to own tweet posted successfully!")
                    time.sleep(3)
                    return True
                    
                except Exception as profile_e:
                    logger.warning(f"⚠️ Profile strategy failed: {profile_e}")
                    return self.use_compose_for_thread(content)
            else:
                logger.warning("⚠️ No tweets found on profile")
                return self.use_compose_for_thread(content)
                
        except Exception as e:
            logger.error(f"❌ Error replying to own tweet: {e}")
            return self.use_compose_for_thread(content)
    
    def use_compose_for_thread(self, content):
        """Fallback: use compose to continue thread-like conversation."""
        try:
            logger.info("📝 Using compose method for thread continuation")
            
            # Add thread-like indicators to make it feel connected
            thread_indicators = ["Also,", "Plus,", "And", "Another thing:", "Speaking of which,"]
            indicator = random.choice(thread_indicators)
            
            threaded_content = f"{indicator} {content}"
            
            return self.post_tweet(threaded_content)
            
        except Exception as e:
            logger.error(f"❌ Error in compose fallback: {e}")
            return False

def main():
    bot = IntelligentTwitterBot()
    bot.run()

if __name__ == "__main__":
    main()
