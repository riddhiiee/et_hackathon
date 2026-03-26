# agents/tone_adaptation.py
import json
import os
from groq import Groq
from dotenv import load_dotenv
from agents.prompts import TONE_ADAPTATION_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_KEY"))

def adapt_single_platform(content: str, platform: str, user_profile: dict) -> str:
    """Adapts content tone for a single platform"""
    try:
        prompt = TONE_ADAPTATION_PROMPT.format(
            user_profile=json.dumps({
                "name": user_profile["name"],
                "profession": user_profile["profession"],
                "format_preference": user_profile["format_preference"]
            }, indent=2),
            platform=platform,
            content=content
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a tone adaptation agent. Return only the rewritten content. No explanations. No markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Tone adaptation error for {platform}: {e}")
        return content  # return original if adaptation fails


def tone_adaptation_node(state: dict) -> dict:
    """
    LangGraph node
    Takes generated_content + user_profile from state
    Adapts tone for each platform to sound like the user
    Returns tone_adapted_content in state
    """
    generated = state["generated_content"]
    user_profile = state["user_profile"]

    if not generated:
        return {"tone_adapted_content": None}

    print(f"Adapting tone for {user_profile['profession']}...")

    # adapt each platform
    linkedin = adapt_single_platform(
        generated.get("linkedin", ""),
        "LinkedIn",
        user_profile
    )

    # for twitter adapt each tweet
    tweets = generated.get("twitter", [])
    adapted_tweets = []
    for tweet in tweets:
        adapted = adapt_single_platform(tweet, "Twitter", user_profile)
        adapted_tweets.append(adapted)

    instagram = adapt_single_platform(
        generated.get("instagram", ""),
        "Instagram",
        user_profile
    )

    video_script = adapt_single_platform(
        generated.get("video_script", ""),
        "Video Script",
        user_profile
    )

    adapted_content = {
        "linkedin": linkedin,
        "twitter": adapted_tweets,
        "instagram": instagram,
        "video_script": video_script
    }

    print(f"✓ Tone adaptation complete")
    return {"tone_adapted_content": adapted_content}