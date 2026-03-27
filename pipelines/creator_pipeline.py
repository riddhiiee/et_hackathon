# pipelines/creator_pipeline.py
from langgraph.graph import StateGraph, END
from state import AppState
from agents.content_generation import content_generation_node
from agents.tone_adaptation import tone_adaptation_node
from agents.compliance import compliance_node
from agents.distribution import distribution_node

def should_retry_or_continue(state: dict) -> str:
    """
    Conditional edge after compliance check
    If failed and retries < 3 → go back to content generation
    If passed or retries >= 3 → move to distribution
    """
    compliance_passed = state.get("compliance_passed", False)
    retry_count = state.get("retry_count", 0)

    if not compliance_passed and retry_count < 3:
        print(f"Retrying content generation (attempt {retry_count + 1}/3)...")
        return "content_generation"
    else:
        return "distribution"


def build_creator_pipeline():
    graph = StateGraph(AppState)

    # add nodes
    graph.add_node("content_generation", content_generation_node)
    graph.add_node("tone_adaptation", tone_adaptation_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("distribution", distribution_node)

    # connect nodes
    graph.set_entry_point("content_generation")
    graph.add_edge("content_generation", "tone_adaptation")
    graph.add_edge("tone_adaptation", "compliance")

    # self correction loop
    graph.add_conditional_edges(
        "compliance",
        should_retry_or_continue,
        {
            "content_generation": "content_generation",
            "distribution": "distribution"
        }
    )

    graph.add_edge("distribution", END)

    return graph.compile()

creator_pipeline = build_creator_pipeline()