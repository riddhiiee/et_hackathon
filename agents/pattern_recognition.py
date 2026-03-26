import json
import os
from groq import Groq
from dotenv import load_dotenv
from agents.prompts import PATTERN_RECOGNITION_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_KEY"))

def pattern_recognition_node(state: dict) -> dict:
    """
    LangGraph node
    Takes performance history
    Uses Groq to find patterns
    Returns insights and recommendations
    """
    performance_history = state["performance_history"]
    user = state["user_profile"]

    print(f"Recognizing patterns for {user['name']}...")

    # need at least some data to recognize patterns
    if not performance_history or performance_history["total_interactions"] < 3:
        print("Not enough data yet — using defaults")
        return {
            "content_strategy": {
                "best_format": user["format_preference"],
                "top_topics": user["interests"][:2],
                "best_style": "data-heavy with clear takeaways",
                "insights": [
                    "Keep reading and creating content to unlock personalized insights",
                    "Your feed will get smarter with every interaction",
                    "Try different content formats to find what works best"
                ],
                "next_suggestions": [
                    f"Create a LinkedIn post about {user['interests'][0] if user['interests'] else 'markets'}",
                    "Try a Twitter thread — they typically get more engagement",
                    "Read 5 more articles to unlock pattern recognition"
                ]
            }
        }

    prompt = PATTERN_RECOGNITION_PROMPT.format(
        history=json.dumps(performance_history, indent=2)
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a content strategy analyst. Always return valid JSON only. No extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4
        )

        raw = response.choices[0].message.content.strip()

        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        strategy = json.loads(raw)
        print(f"✓ Patterns recognized")
        return {"content_strategy": strategy}

    except Exception as e:
        print(f"Pattern recognition error: {e}")
        return {
            "content_strategy": {
                "best_format": "twitter",
                "top_topics": user["interests"][:2],
                "best_style": "data-heavy",
                "insights": ["Keep interacting to unlock insights"],
                "next_suggestions": ["Create more content to see patterns"]
            }
        }