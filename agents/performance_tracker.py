# agents/performance_tracker.py
from database.db import get_user_interactions, get_user_generated_content, get_user_performance

def performance_tracker_node(state: dict) -> dict:
    """
    LangGraph node
    Pulls all user interactions + content performance from DB
    Builds a performance history object for pattern recognition
    """
    user = state["user_profile"]
    user_id = user["id"]

    print(f"Tracking performance for {user['name']}...")

    # get interactions
    interactions = get_user_interactions(user_id, limit=50)
    
    # get generated content history
    content_history = get_user_generated_content(user_id, limit=20)
    
    # get performance data
    performance = get_user_performance(user_id)

    # summarize interactions by topic
    topic_summary = {}
    action_summary = {}

    for interaction in interactions:
        topic = interaction[5]  # topic column
        action = interaction[3]  # action column

        if topic not in topic_summary:
            topic_summary[topic] = {
                "reads": 0,
                "skips": 0,
                "creates": 0,
                "total": 0
            }

        topic_summary[topic]["total"] += 1

        if action == "read_full":
            topic_summary[topic]["reads"] += 1
        elif action == "skipped":
            topic_summary[topic]["skips"] += 1
        elif action == "created_content":
            topic_summary[topic]["creates"] += 1

        action_summary[action] = action_summary.get(action, 0) + 1

    # summarize performance by platform
    platform_summary = {}
    for perf in performance:
        platform = perf[3]  # platform column
        views = perf[4] or 0
        likes = perf[5] or 0
        shares = perf[6] or 0

        if platform not in platform_summary:
            platform_summary[platform] = {
                "total_views": 0,
                "total_likes": 0,
                "total_shares": 0,
                "post_count": 0
            }

        platform_summary[platform]["total_views"] += views
        platform_summary[platform]["total_likes"] += likes
        platform_summary[platform]["total_shares"] += shares
        platform_summary[platform]["post_count"] += 1

    performance_history = {
        "user_id": user_id,
        "total_interactions": len(interactions),
        "total_content_created": len(content_history),
        "topic_summary": topic_summary,
        "action_summary": action_summary,
        "platform_summary": platform_summary,
        "dynamic_profile": user["dynamic_profile"]
    }

    print(f"✓ Performance tracked — {len(interactions)} interactions, {len(performance)} posts")
    return {"performance_history": performance_history}