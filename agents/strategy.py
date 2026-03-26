# agents/strategy.py
from database.db import update_dynamic_profile

def strategy_node(state: dict) -> dict:
    """
    LangGraph node
    Takes content strategy from pattern recognition
    Applies recommendations back to user profile
    Updates DB with new strategy
    """
    strategy = state["content_strategy"]
    user = state["user_profile"]
    performance = state["performance_history"]

    print(f"Applying strategy for {user['name']}...")

    if not strategy:
        return {"content_strategy": None}

    # boost top topics in dynamic profile
    top_topics = strategy.get("top_topics", [])
    for topic in top_topics:
        topic_lower = topic.lower()
        update_dynamic_profile(
            user_id=user["id"],
            topic=topic_lower,
            action="read_full"  # boost these topics
        )

    # update best format in dynamic profile
    best_format = strategy.get("best_format", "")
    if best_format:
        from database.db import update_best_format
        update_best_format(user["id"], best_format)

    print(f"✓ Strategy applied — best format: {best_format}")
    print(f"✓ Boosted topics: {top_topics}")

    return {"content_strategy": strategy}