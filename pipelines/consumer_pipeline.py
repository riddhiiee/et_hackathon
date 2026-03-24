# pipelines/consumer_pipeline.py
from langgraph.graph import StateGraph, END
from state import AppState
from agents.news_fetch import news_fetcher_node
from agents.enrichment import enrichment_node
from agents.personalization import personalization_node

def build_consumer_pipeline():
    graph = StateGraph(AppState)

    # add nodes
    graph.add_node("news_fetcher", news_fetcher_node)
    graph.add_node("enrichment", enrichment_node)
    graph.add_node("personalization", personalization_node)

    # connect nodes
    graph.set_entry_point("news_fetcher")
    graph.add_edge("news_fetcher", "enrichment")
    graph.add_edge("enrichment", "personalization")
    graph.add_edge("personalization", END)

    return graph.compile()

# compiled pipeline — import this in app.py
consumer_pipeline = build_consumer_pipeline()