# pipelines/strategist_pipeline.py
from langgraph.graph import StateGraph, END
from state import AppState
from agents.performance_tracker import performance_tracker_node
from agents.pattern_recognition import pattern_recognition_node
from agents.strategy import strategy_node

def build_strategist_pipeline():
    graph = StateGraph(AppState)

    graph.add_node("performance_tracker", performance_tracker_node)
    graph.add_node("pattern_recognition", pattern_recognition_node)
    graph.add_node("strategy", strategy_node)

    graph.set_entry_point("performance_tracker")
    graph.add_edge("performance_tracker", "pattern_recognition")
    graph.add_edge("pattern_recognition", "strategy")
    graph.add_edge("strategy", END)

    return graph.compile()

strategist_pipeline = build_strategist_pipeline()