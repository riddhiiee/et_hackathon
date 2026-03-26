# agents/content_generation.py
import json
import os
from groq import Groq
from dotenv import load_dotenv
from agents.prompts import CONTENT_GENERATION_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_KEY"))

def content_generation_node(state: dict) -> dict:
    """
    LangGraph node
    Takes selected_article + user_profile from state
    Generates linkedin, twitter, instagram, video script
    Returns generated_content in state
    """
    article = state["selected_article"]
    user_profile = state["user_profile"]
    retry_count = state.get("retry_count", 0)

    print(f"Generating content for: {article['title'][:60]}...")
    print(f"Attempt: {retry_count + 1}")

    prompt = CONTENT_GENERATION_PROMPT.format(
        user_profile=json.dumps({
            "name": user_profile["name"],
            "profession": user_profile["profession"],
            "format_preference": user_profile["format_preference"],
            "dynamic_scores": user_profile["dynamic_profile"]["topic_scores"]
        }, indent=2),
        title=article["title"],
        content=article.get("full_text", article.get("summary", ""))[:2000]
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a content creation agent. Always return valid JSON only. No extra text. No markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()

        # clean markdown if model adds it
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        content = json.loads(raw)

        # validate all fields present
        required = ["linkedin", "twitter", "instagram", "video_script"]
        for field in required:
            if field not in content:
                content[field] = ""

        # ensure twitter is a list
        if isinstance(content["twitter"], str):
            content["twitter"] = [content["twitter"]]

        print(f"✓ Content generated successfully")
        return {
            "generated_content": content,
            "retry_count": retry_count
        }

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return {
            "generated_content": {
                "linkedin": "",
                "twitter": [],
                "instagram": "",
                "video_script": ""
            },
            "retry_count": retry_count
        }

    except Exception as e:
        print(f"Content generation error: {e}")
        return {
            "generated_content": None,
            "retry_count": retry_count
        }