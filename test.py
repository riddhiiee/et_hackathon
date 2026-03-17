# test.py
from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, save_user, get_user
from agents.news_fetch import news_fetcher_node

# init database
init_db()

# create test user
user_id = save_user(
    name="Rahul",
    profession="Finance Analyst",
    interests=["markets", "economy", "wealth"],
    format_pref="detailed",
    language="english",
    creator_mode=1
)

print(f"Created user with ID: {user_id}")

# get user back
user = get_user(user_id)
print(f"User profile: {user}")

# test news fetcher
state = {"user_profile": user}
result = news_fetcher_node(state)

print(f"\nFetched {len(result['raw_articles'])} articles")
for article in result['raw_articles'][:3]:
    print(f"\n→ {article['title']}")
    print(f"  Topic: {article['topic']}")
    print(f"  URL: {article['url']}")