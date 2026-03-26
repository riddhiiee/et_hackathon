# agents/distribution.py
import json
from database.db import save_generated_content

def distribution_node(state: dict) -> dict:
    """
    LangGraph node
    Formats final content for each platform
    Saves to database
    Returns final_content in state
    """
    content = state["tone_adapted_content"]
    user = state["user_profile"]
    article = state["selected_article"]
    accuracy = state.get("accuracy_score", 85.0)

    if not content:
        return {"final_content": None}

    print("Formatting for distribution...")

    # format linkedin
    linkedin = content.get("linkedin", "")
    if linkedin and not any(tag in linkedin for tag in ["#"]):
        linkedin += "\n\n#EconomicTimes #Finance #India"

    # format twitter thread
    tweets = content.get("twitter", [])
    formatted_tweets = []
    for i, tweet in enumerate(tweets):
        if not tweet.startswith(f"{i+1}/"):
            tweet = f"{i+1}/{len(tweets)} {tweet}"
        formatted_tweets.append(tweet)

    # format instagram
    instagram = content.get("instagram", "")
    if instagram and "#" not in instagram:
        instagram += "\n\n#ET #IndianMarkets #Finance #BusinessNews #Investing"

    # format video script
    video_script = content.get("video_script", "")
    if video_script:
        video_script = f"[HOOK - 0:00-0:05]\n{video_script[:100]}\n\n[MAIN - 0:05-0:50]\n{video_script[100:400]}\n\n[CTA - 0:50-1:00]\nFollow for more business insights from ET."

    final = {
        "linkedin": linkedin,
        "twitter": formatted_tweets,
        "instagram": instagram,
        "video_script": video_script,
        "accuracy_score": accuracy
    }

    # save to database
    if article.get("id") and user.get("id"):
        content_id = save_generated_content(
            user_id=user["id"],
            article_id=article["id"],
            linkedin=linkedin,
            twitter=json.dumps(formatted_tweets),
            instagram=instagram,
            video_script=video_script,
            accuracy_score=accuracy
        )
        final["content_id"] = content_id
        print(f"✓ Content saved to DB — ID: {content_id}")

    print("✓ Distribution formatting complete")
    return {"final_content": final}