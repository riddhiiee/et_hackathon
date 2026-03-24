import json
import os
from groq import Groq
from dotenv import load_dotenv
from agents.prompts import PERSONALIZATION_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_KEY"))

def personalization_node(state: dict) -> dict:
    """
    LangGraph node
    Takes enriched_articles + user_profile from state
    Scores, ranks and rewrites each article for the user
    Returns personalized_feed in state
    """
    enriched_articles = state["enriched_articles"]
    user_profile = state["user_profile"]

    #filter out skipped articles
    from database.db import get_skipped_articles
    skipped_urls = get_skipped_articles(user_profile["id"])

    # remove any article user has previously skipped
    enriched_articles = [
        a for a in enriched_articles
        if a.get("article_url") not in skipped_urls
    ]

    print(f"After filtering skipped: {len(enriched_articles)} articles remain")

    print(f"Personalizing {len(enriched_articles)} articles for {user_profile['name']}...")

    # prepare articles for prompt
    articles_for_prompt = []
    for i, article in enumerate(enriched_articles):
        articles_for_prompt.append({
            "index": i,
            "title": article["title"],
            "summary": article["summary"],
            "topic": article["topic"],
            "text_preview": article["full_text"][:500]
        })

    # build prompt
    prompt = PERSONALIZATION_PROMPT.format(
        user_profile=json.dumps({
            "name": user_profile["name"],
            "profession": user_profile["profession"],
            "interests": user_profile["interests"],
            "format_preference": user_profile["format_preference"],
            "dynamic_scores": user_profile["dynamic_profile"]["topic_scores"]
        }, indent=2),
        articles=json.dumps(articles_for_prompt, indent=2)
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a personalization agent. Always return valid JSON only. No extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()

        # clean response in case model adds markdown
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        scored_articles = json.loads(raw)

        # merge scores back with full article data
        personalized_feed = []
        for scored in scored_articles:
            idx = scored["article_index"]
            if idx < len(enriched_articles):
                full_article = enriched_articles[idx].copy()
                full_article["relevance_score"] = scored["relevance_score"]
                full_article["personalized_summary"] = scored["personalized_summary"]
                full_article["why_relevant"] = scored["why_relevant"]
                personalized_feed.append(full_article)

        # sort by relevance score highest first
        personalized_feed.sort(
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        print(f"Personalization complete — top article: {personalized_feed[0]['title'][:60]}")
        return {"personalized_feed": personalized_feed}

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # fallback — return enriched articles as is
        return {"personalized_feed": enriched_articles}

    except Exception as e:
        print(f"Personalization error: {e}")
        return {"personalized_feed": enriched_articles}