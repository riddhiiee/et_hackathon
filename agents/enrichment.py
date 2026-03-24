# agents/enrichment.py
import concurrent.futures
from newspaper import Article
from database.db import save_article


def enrich_single_article(article: dict) -> dict:
    """Enriches one article — runs in parallel with others"""
    try:
        news_article = Article(article["url"])
        news_article.download()
        news_article.parse()

        full_text = news_article.text.strip()
        image_url = news_article.top_image
        authors = news_article.authors

        article_id = save_article(
            title=article["title"],
            summary=article["summary"],
            full_text=full_text,
            image_url=image_url,
            article_url=article["url"],
            topic=article["topic"],
            published_at=article["published"]
        )

        # ── store in chromadb for semantic search ──
        if article_id:
            try:
                from utils.chroma import store_article_embedding
                store_article_embedding(
                    article_id=article_id,
                    title=article["title"],
                    full_text=full_text,
                    topic=article["topic"]
                )
            except Exception as e:
                print(f"ChromaDB store skipped: {e}")

        return {
            "id": article_id,
            "title": article["title"],
            "summary": article["summary"],
            "full_text": full_text[:3000],
            "image_url": image_url,
            "article_url": article["url"],
            "topic": article["topic"],
            "published": article["published"],
            "authors": authors
        }

    except Exception as e:
        print(f"Enrichment failed for {article.get('url', '')}: {e}")
        return {
            "id": None,
            "title": article["title"],
            "summary": article["summary"],
            "full_text": article["summary"],
            "image_url": "",
            "article_url": article["url"],
            "topic": article["topic"],
            "published": article["published"],
            "authors": []
        }

def enrichment_node(state: dict) -> dict:
    """
    LangGraph node — parallel enrichment
    Fetches all articles simultaneously
    Cuts time from ~20s to ~5s
    """
    raw_articles = state["raw_articles"]
    print(f"Enriching {len(raw_articles)} articles in parallel...")

    enriched = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(enrich_single_article, article): article
            for article in raw_articles
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                enriched.append(result)
                print(f"✓ {result['title'][:60]}...")
            except Exception as e:
                print(f"Thread error: {e}")

    print(f"Enrichment complete — {len(enriched)} articles ready")
    return {"enriched_articles": enriched}