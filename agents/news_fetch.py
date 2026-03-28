# agents/news_fetcher.py
import feedparser
from utils.rss_feed import get_feed
from datetime import datetime

def news_fetcher_node(state: dict) -> dict:
    """
    Fetches articles from ET RSS feeds
    based on user interests
    """
    user_profile = state["user_profile"]
    # normalize interests to match RSS keys
    interest_map = {
        "markets": "markets",
        "economy": "economy", 
        "banking": "banking",
        "startups": "startups",
        "tech": "tech",
        "wealth": "wealth",
        "wealth_personal_finance": "wealth",
        "real_estate": "top_stories",
        "global_markets": "top_stories"
    }
    
    user_interests = [
        interest_map.get(i.lower().replace(" ", "_"), "top_stories")
        for i in user_profile.get("interests", [])
    ]
    if "top_stories" not in user_interests:
        user_interests.append("top_stories")
    # get relevant feeds
    feeds = get_feed(user_interests)
    
    all_articles = []
    
    for topic, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:  # 5 per topic
                article = {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "topic": topic,
                    "image_url": "",
                    "full_text": ""
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error fetching {topic} feed: {e}")
            continue
    
    print(f"Fetched {len(all_articles)} articles")
    return {"raw_articles": all_articles}