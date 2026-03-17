RSS={
    "market": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "economy":    "https://economictimes.indiatimes.com/news/economy/rssfeeds/20150316.cms",
    "startups":   "https://economictimes.indiatimes.com/tech/startups/rssfeeds/78570550.cms",
    "tech":       "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "wealth":     "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
    "top_stories":"https://economictimes.indiatimes.com/rssfeedstopstories.cms"   
}

def get_feed(interests: list) -> dict:
    selected = {}
    for i in interests:
        interest_lower = i.lower()
        if interest_lower in RSS:
            selected[i] = RSS[interest_lower]

    selected['top_stories'] = RSS['top_stories']  # Always include top stories
    return selected

