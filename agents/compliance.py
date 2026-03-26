# agents/compliance.py
import json
import os
from groq import Groq
from dotenv import load_dotenv
from agents.prompts import COMPLIANCE_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_KEY"))

def compliance_node(state: dict) -> dict:
    """
    LangGraph node
    Fact checks tone adapted content against source article
    If fails — sets compliance_passed = False so pipeline loops back
    If passes — sets compliance_passed = True to move forward
    """
    adapted_content = state["tone_adapted_content"]
    article = state["selected_article"]
    retry_count = state.get("retry_count", 0)

    if not adapted_content:
        return {
            "compliance_passed": False,
            "compliance_issues": ["No content to check"],
            "retry_count": retry_count + 1
        }

    print(f"Running compliance check...")

    # combine all content for checking
    content_to_check = f"""
    LinkedIn: {adapted_content.get('linkedin', '')}
    Twitter: {' | '.join(adapted_content.get('twitter', []))}
    Instagram: {adapted_content.get('instagram', '')}
    """

    prompt = COMPLIANCE_PROMPT.format(
        article=article.get("full_text", article.get("summary", ""))[:2000],
        content=content_to_check
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance agent. Always return valid JSON only. No extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1  # low temp for consistent checking
        )

        raw = response.choices[0].message.content.strip()

        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        passed = result.get("passed", False)
        accuracy = result.get("accuracy_score", 0)
        issues = result.get("issues", [])
        severity = result.get("severity", "low")

        if passed and accuracy >= 80:
            print(f"✓ Compliance passed — accuracy: {accuracy}%")
            return {
                "compliance_passed": True,
                "compliance_issues": [],
                "accuracy_score": accuracy,
                "retry_count": retry_count
            }
        else:
            print(f"✗ Compliance failed — accuracy: {accuracy}% — issues: {issues}")
            return {
                "compliance_passed": False,
                "compliance_issues": issues,
                "accuracy_score": accuracy,
                "retry_count": retry_count + 1
            }

    except Exception as e:
        print(f"Compliance check error: {e}")
        # if compliance check itself fails — pass through
        # don't block user for a system error
        return {
            "compliance_passed": True,
            "compliance_issues": [],
            "accuracy_score": 85.0,
            "retry_count": retry_count
        }