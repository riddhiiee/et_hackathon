from typing import TypedDict, List, Optional

class AppState(TypedDict):
    # user
    user_profile: dict

    # pipeline 1 - consumer
    raw_articles: List[dict]
    enriched_articles: List[dict]
    personalized_feed: List[dict]

    # pipeline 2 - creator
    selected_article: Optional[dict]
    generated_content: Optional[dict]
    tone_adapted_content: Optional[dict]
    compliance_passed: Optional[bool]
    compliance_issues: Optional[list]
    final_content: Optional[dict]
    retry_count: int

    # pipeline 3 - strategist
    performance_history: Optional[list]
    content_strategy: Optional[dict]