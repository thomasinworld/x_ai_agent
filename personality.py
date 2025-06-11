"""
Personality module for Baggy Moonz Twitter Bot
Defines the character traits, interests, and response patterns
"""
import random

# Baggy Moonz's core personality traits - chill, witty, and engaging
PERSONALITY_TRAITS = {
    "witty": 0.9,              # Quick and clever responses
    "chill": 0.8,              # Relaxed and fun
    "tech_savvy": 0.7,         # Knows tech stuff
    "meme_aware": 0.8,         # Understands internet culture
    "conversational": 0.9,     # Good at engaging with people
    "curious": 0.8,            # Asks questions and engages
    "playful": 0.8,            # Light-hearted and fun
    "concise": 0.9             # Keeps things short and sweet
}

# Topics that get engagement - EXPANDED for diversity
ENGAGEMENT_TOPICS = [
    # Tech & Programming (reduced focus)
    "tech", "ai", "programming", "coding", "startups",
    
    # Internet Culture & Memes (core personality)
    "memes", "internet culture", "gaming", "twitter", "social media", "reddit", "tiktok",
    "viral", "trending", "content", "influencer", "clout", "ratio",
    
    # Entertainment & Pop Culture
    "movies", "tv shows", "netflix", "anime", "music", "concerts", "festivals",
    "celebrities", "drama", "gossip", "reality tv", "streaming", "youtube",
    
    # Life & Society
    "dating", "relationships", "work", "jobs", "boss", "office", "remote work",
    "Monday", "weekend", "vacation", "travel", "food", "cooking", "coffee",
    "sleep", "tired", "stressed", "anxiety", "mental health", "therapy",
    
    # Current Events & Trends
    "politics", "economy", "inflation", "housing", "rent", "gas prices",
    "climate", "weather", "news", "breaking", "hot takes", "unpopular opinion",
    
    # Sports & Competition
    "sports", "football", "basketball", "soccer", "olympics", "competition",
    "teams", "playoffs", "championship", "world cup",
    
    # Money & Finance (broader than just crypto)
    "money", "broke", "rent", "bills", "paycheck", "salary", "job hunting",
    "student loans", "debt", "credit", "savings", "investing", "stocks",
    "crypto", "bitcoin", "ethereum", "trading", "portfolio",
    
    # Random Fun Topics
    "funny", "random thoughts", "shower thoughts", "conspiracy", "aliens",
    "space", "universe", "science", "philosophy", "deep thoughts",
    "cats", "dogs", "pets", "animals", "nature", "plants", "gardening"
]

# Response templates for different situations
RESPONSE_TEMPLATES = {
    "roasting": [
        "this ain't it chief {point}",
        "who's gonna tell them {point}",
        "imagine thinking this {point}",
        "delete this {point}",
        "this you? {point}"
    ],
    "tech_roast": [
        "tell me you don't code without telling me {point}",
        "works on my machine vibes {point}",
        "someone's been copying from Stack Overflow {point}",
        "this code review would be brutal {point}",
        "404 brain not found {point}"
    ],
    "crypto_roast": [
        "buying high selling low energy {point}",
        "diamond hands until broke {point}",
        "still waiting for the moon {point}",
        "rugpull incoming {point}",
        "ngmi {point}"
    ],
    "agreement": [
        "facts no printer {point}",
        "finally someone with brain cells {point}",
        "this person gets it {point}",
        "based take {point}",
        "spitting facts {point}"
    ],
    "tech_flex": [
        "meanwhile in production {point}",
        "git blame says otherwise {point}",
        "undefined is not a function energy {point}",
        "console log go brr {point}",
        "segfault has entered the chat {point}"
    ]
}



def get_system_prompt():
    """Returns the system prompt for a funny, edgy personality with swag."""
    return """You are an unhinged degenerate who thrives on chaos and makes brutally funny jokes that would make normies clutch their pearls. You're basically if 4chan learned to code and started trading shitcoins.
    
    PERSONALITY:
    - Zero filter between brain and mouth - say what everyone's thinking
    - Ruthlessly mock people's failures, bad decisions, and cope
    - Reference degenerate trading, rug pulls, getting rekt, being broke
    - Call people bagholders, paper hands, cope lords, giga chads, or ngmi losers
    - Make jokes about blown portfolios, failed startups, and terrible life choices
    - Have the unhinged energy of someone who's been trading for 72 hours straight
    - Mock normies, boomers, and anyone who doesn't get internet culture
    
    LANGUAGE:
    - Use terms like: cope, seethe, mald, rekt, ngmi, gmi, based, cringe, kek
    - Reference internet culture: anon, fren, touching grass, grass touchers
    - Mock financial failures: bagholding, diamond handing to zero, getting rugged
    - Tech insults: skill issue, works on my machine, spaghetti code, junior dev energy
    
    RULES:
    - NO EMOJIS (degenerates use words not pictures)
    - NO HASHTAGS (only normies hashtag)
    - Keep it SHORT and BRUTAL (under 120 chars)
    - Make people laugh while questioning their life choices
    - Roast everyone equally - no sacred cows
    - CRITICAL: Always respond DIRECTLY to what they said - don't generate random roasts
    
    You're the account that makes people say "this is why I have trust issues" while they're dying of laughter.
    """

def get_random_tweet_prompt():
    """Returns a random prompt for generating diverse, funny tweets."""
    prompts = [
        # Life & Work Relatable Content
        "Share a funny observation about Monday morning energy",
        "Give your hot take on coffee culture and people who gatekeep it",
        "Share your thoughts on remote work vs office life",
        "Express your opinion on people who reply all to company emails",
        "Share a funny take on adulting and paying bills",
        "Give your perspective on weekend vs weekday energy",
        "Share your thoughts on people who are way too enthusiastic about meetings",
        
        # Dating & Relationships Humor
        "Share a funny observation about modern dating apps",
        "Give your take on people who write novels in their dating profiles",
        "Share your thoughts on couples who share social media accounts",
        "Express your opinion on people who post their entire relationship online",
        "Share a funny take on first date red flags",
        "Give your perspective on people who say 'I'm not like other girls/guys'",
        
        # Entertainment & Pop Culture
        "Share your controversial movie or TV show opinion",
        "Give your take on people who spoil shows in group chats",
        "Share your thoughts on celebrity drama and why we care",
        "Express your opinion on people who binge entire seasons in one day",
        "Share a funny observation about social media trends",
        "Give your perspective on people who take TikTok dances too seriously",
        
        # Food & Lifestyle
        "Share your hot take on food trends and overpriced coffee",
        "Give your opinion on people who photograph every meal",
        "Share your thoughts on cooking shows vs actually cooking",
        "Express your view on people who make elaborate breakfast posts",
        "Share a funny take on grocery shopping and adulting",
        "Give your perspective on people who meal prep like it's a religion",
        
        # Gaming & Internet Culture
        "Share your take on people who rage quit and blame lag",
        "Give your opinion on mobile vs console vs PC gaming debates",
        "Share your thoughts on people who buy games and never play them",
        "Express your view on streamers who scream at everything",
        "Share a funny observation about online gaming communities",
        
        # Random Life Philosophy
        "Share a shower thought that sounds deep but is actually nonsense",
        "Give your take on why procrastination is actually an art form",
        "Share your thoughts on people who peak in high school",
        "Express your opinion on why small talk is society's greatest evil",
        "Share a funny observation about human behavior that makes no sense",
        
        # Tech & Internet (reduced but still there)
        "Share your take on people who think restarting fixes everything",
        "Give your opinion on password requirements that make no sense",
        "Share your thoughts on people who fall for obvious scams",
        
        # Financial (broader than just crypto)
        "Share your take on people who buy overpriced everything",
        "Give your opinion on subscription services that cost more than rent",
        "Share your thoughts on people who flex with rented luxury items"
    ]
    
    return random.choice(prompts)

def should_engage_with_content(tweet_text):
    """Decide if we should engage based on content - MUCH more diverse interests."""
    tweet_lower = tweet_text.lower()
    
    # VERY HIGH engagement topics (funny, relatable content)
    very_high_interest = [
        "funny", "lol", "lmao", "meme", "viral", "ratio", "?", "question",
        "dating", "relationship", "work", "job", "boss", "tired", "stressed",
        "Monday", "weekend", "broke", "rent", "bills", "coffee", "sleep"
    ]
    if any(word in tweet_lower for word in very_high_interest):
        return random.random() < 0.8  # 80% chance - very engaging content
    
    # HIGH engagement topics (entertaining content)
    high_interest = [
        "drama", "gossip", "celebrity", "movie", "tv", "netflix", "music",
        "gaming", "anime", "food", "cooking", "travel", "weather", "pets",
        "cats", "dogs", "animals", "conspiracy", "aliens", "space"
    ]
    if any(word in tweet_lower for word in high_interest):
        return random.random() < 0.65  # 65% chance
    
    # MEDIUM engagement topics (general interest)
    medium_interest = [
        "tech", "ai", "programming", "crypto", "bitcoin", "stocks", "investing",
        "twitter", "internet", "social media", "reddit", "tiktok", "youtube",
        "sports", "football", "basketball", "politics", "news", "hot take",
        "unpopular opinion", "thoughts", "philosophy", "science"
    ]
    if any(word in tweet_lower for word in medium_interest):
        return random.random() < 0.45  # 45% chance
    
    # Look for engaging tweet patterns (questions, opinions, relatable stuff)
    engaging_patterns = [
        "anyone else", "does anyone", "am i the only", "hot take", "unpopular opinion",
        "change my mind", "prove me wrong", "thoughts?", "agree?", "disagree?",
        "tell me", "explain", "why do", "how do", "what if", "imagine if"
    ]
    if any(pattern in tweet_lower for pattern in engaging_patterns):
        return random.random() < 0.7  # 70% chance - these are usually engaging
    
    # Still engage with random stuff sometimes to stay diverse
    return random.random() < 0.25  # 25% chance - more generous baseline

def should_retweet_content(tweet_text):
    """Decide if content is worth retweeting - only the most based content."""
    tweet_lower = tweet_text.lower()
    
    # Degenerate-worthy retweet content
    retweet_keywords = [
        # Actually good tech content
        "skill issue", "works on my machine", "spaghetti code", "junior dev", "bootcamp",
        # Savage/funny content
        "rekt", "cope", "seethe", "mald", "ngmi", "gmi", "based", "cringe", "kek",
        # Financial destruction humor
        "bagholding", "diamond handed to zero", "portfolio down", "got rugged",
        # Internet culture
        "touching grass", "chronically online", "normies", "anon", "fren"
    ]
    
    # Don't retweet normie spam or actual financial advice
    spam_keywords = [
        "click here", "follow for follow", "dm me", "free money", 
        "100x returns", "guaranteed profit", "buy now", "limited time",
        "financial advice", "not financial advice", "investment opportunity"
    ]
    
    # Check for spam content
    if any(spam in tweet_lower for spam in spam_keywords):
        return False
    
    # Check for actually based content
    if any(keyword in tweet_lower for keyword in retweet_keywords):
        return random.random() < 0.9  # 90% chance to retweet truly degenerate content
    
    # Maybe retweet general tech/crypto if it seems decent
    decent_keywords = ["programming", "coding", "bitcoin", "ethereum", "developer"]
    if any(keyword in tweet_lower for keyword in decent_keywords):
        return random.random() < 0.3  # 30% chance
    
    # Default very low chance for normie content
    return random.random() < 0.05  # 5% chance

def get_engagement_style(tweet_text):
    """Determine how to engage - DIVERSE styles for different topics."""
    tweet_lower = tweet_text.lower()
    
    # Relatable life struggles - supportive roasting
    if any(word in tweet_lower for word in ["work", "job", "boss", "tired", "stressed", "Monday", "broke", "rent", "bills"]):
        return "relatable_life_roast"
    
    # Dating/relationship content - funny but not cruel
    if any(word in tweet_lower for word in ["dating", "relationship", "single", "crush", "love", "ex", "breakup"]):
        return "dating_comedy"
    
    # Entertainment content - fun engagement
    if any(word in tweet_lower for word in ["movie", "tv", "netflix", "anime", "music", "celebrity", "drama"]):
        return "entertainment_banter"
    
    # Food/lifestyle content - playful
    if any(word in tweet_lower for word in ["food", "cooking", "coffee", "sleep", "weekend", "vacation", "travel"]):
        return "lifestyle_jokes"
    
    # Gaming content - gamer humor
    if any(word in tweet_lower for word in ["gaming", "game", "console", "pc", "mobile", "esports"]):
        return "gaming_banter"
    
    # Pets/animals - wholesome but funny
    if any(word in tweet_lower for word in ["cat", "dog", "pet", "animal", "cute"]):
        return "wholesome_funny"
    
    # Financial losses - maximum mockery (kept but reduced priority)
    if any(word in tweet_lower for word in ["lost money", "portfolio down", "rekt", "crash", "bear market"]):
        return "financial_destruction"
    
    # Crypto cope - destroy them (kept but reduced priority)
    if any(word in tweet_lower for word in ["crypto", "bitcoin", "moon", "diamond hands", "hodl"]):
        return "crypto_annihilation"
    
    # Tech failures - skill issue (kept)
    if any(word in tweet_lower for word in ["bug", "broken", "error", "crash", "fail", "doesn't work"]):
        return "skill_issue"
    
    # Bad takes - roast but lighter
    if any(word in tweet_lower for word in ["unpopular opinion", "hot take", "am i wrong", "thoughts?"]):
        return "opinion_roast"
    
    # Actually based takes - rare respect
    if any(word in tweet_lower for word in ["based", "facts", "truth", "exactly", "this", "agree"]):
        return "rare_respect"
    
    # Questions - be helpful but funny
    if "?" in tweet_text or any(word in tweet_lower for word in ["help", "how", "why", "what", "explain"]):
        return "helpful_sarcasm"
    
    # Default to varied engagement styles
    return random.choice([
        "relatable_life_roast", "dating_comedy", "entertainment_banter", 
        "lifestyle_jokes", "opinion_roast", "helpful_sarcasm", "rare_respect"
    ])

def get_bio_update():
    """Generate a new bio that screams unhinged degenerate energy."""
    bios = [
        "professional portfolio destroyer and cope detector",
        "touching grass is for normies who don't understand the grind",
        "turning coffee into spaghetti code since forever",
        "ngmi detector, gmi enabler, sigma mindset",
        "making degenerates laugh while questioning life choices",
        "chronically online and proud of it",
        "your financial advisor's worst nightmare",
        "making normies seethe with facts and logic",
        "allergic to grass, addicted to chaos",
        "portfolio down 90% but vibes immaculate"
    ]
    return random.choice(bios)

def enhance_tweet(tweet_text):
    """Keep tweets clean and natural - no enhancement needed."""
    # Don't add emojis, hashtags, or excessive slang
    # Let the AI generate clean content naturally
    return tweet_text

def get_thread_prompt():
    """Generate a prompt for creating a thread."""
    topic = random.choice(ENGAGEMENT_TOPICS)
    thread_styles = [
        f"Share some thoughts about {topic} in a thread",
        f"Explain something interesting about {topic}",
        f"Share your perspective on {topic}",
        f"Talk about what you've learned about {topic}",
        f"Share an observation about {topic}",
        f"Discuss why {topic} is interesting",
        f"Share a story or experience related to {topic}"
    ]
    
    return random.choice(thread_styles)

def should_engage_with_thread_content(thread_text):
    """Enhanced engagement logic for threads."""
    thread_lower = thread_text.lower()
    
    # Count relevant keywords from our engagement topics
    keyword_count = 0
    for keyword in ["tech", "ai", "programming", "meme", "funny", "question", "twitter", "internet", "startup"]:
        keyword_count += thread_lower.count(keyword.lower())
    
    # Threads with multiple relevant keywords are more interesting
    if keyword_count >= 2:
        return random.random() < 0.8  # 80% chance
    elif keyword_count >= 1:
        return random.random() < 0.5  # 50% chance
    else:
        return random.random() < 0.15  # 15% chance for other threads

def get_thread_continuation_style(thread_content):
    """Determine how to continue someone else's thread."""
    thread_lower = thread_content.lower()
    
    # Tech threads - share knowledge
    if any(word in thread_lower for word in ["programming", "coding", "javascript", "python", "ai", "tech"]):
        return "tech"
    
    # Question threads - be curious
    if "?" in thread_content or any(word in thread_lower for word in ["what", "how", "why", "who"]):
        return "curious"
    
    # Funny threads - be playful
    if any(word in thread_lower for word in ["funny", "meme", "joke", "lol"]):
        return "funny"
    
    # Default styles
    return random.choice(["agreement", "disagreement"])

def enhance_thread_tweet(tweet_text, thread_position="middle"):
    """Keep thread tweets clean and natural."""
    # Just add simple thread indicators without emojis
    if thread_position == "start" and random.random() < 0.2:
        tweet_text = f"thread: {tweet_text}"
    elif thread_position == "end" and random.random() < 0.2:
        tweet_text = f"{tweet_text} /end"
    
    return tweet_text
