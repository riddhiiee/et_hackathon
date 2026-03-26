# utils/chroma.py
import chromadb
from chromadb.utils import embedding_functions

# ── setup chromadb client (local, no server needed) ──
client = chromadb.PersistentClient(path="./chroma_db")

# use built-in sentence transformer — no API needed
embedder = embedding_functions.DefaultEmbeddingFunction()

# ── collections ───────────────────────────────────────
def get_articles_collection():
    return client.get_or_create_collection(
        name="et_articles",
        embedding_function=embedder
    )

def get_user_history_collection():
    return client.get_or_create_collection(
        name="user_reading_history",
        embedding_function=embedder
    )


# ── store article embedding ───────────────────────────
def store_article_embedding(article_id: int, title: str,
                             full_text: str, topic: str):
    try:
        collection = get_articles_collection()
        text = f"{title}. {full_text[:500]}"
        doc_id = f"article_{article_id}"

        # check if already stored
        existing = collection.get(ids=[doc_id])
        if existing["ids"]:
            return

        collection.add(
            documents=[text],
            metadatas=[{"topic": topic, "article_id": str(article_id)}],
            ids=[doc_id]
        )
    except Exception as e:
        print(f"ChromaDB store error: {e}")


# ── store what user read ──────────────────────────────
def store_user_reading(user_id: int, article_id: int,
                        title: str, full_text: str):
    try:
        collection = get_user_history_collection()
        text = f"{title}. {full_text[:500]}"
        doc_id = f"user_{user_id}_article_{article_id}"

        existing = collection.get(ids=[doc_id])
        if existing["ids"]:
            return

        collection.add(
            documents=[text],
            metadatas=[{"user_id": str(user_id),
                        "article_id": str(article_id)}],
            ids=[doc_id]
        )
    except Exception as e:
        print(f"ChromaDB user history store error: {e}")


# ── find similar articles ─────────────────────────────
def find_similar_articles(user_id: int, n_results: int = 10):
    """
    Finds articles semantically similar to
    what this user has been reading
    """
    try:
        history_collection = get_user_history_collection()
        articles_collection = get_articles_collection()

        # get user's reading history
        history = history_collection.get(
            where={"user_id": str(user_id)}
        )

        if not history["documents"]:
            return []

        # combine recent reading into one query
        recent_docs = history["documents"][-5:]
        query_text = " ".join(recent_docs)

        # find similar articles
        results = articles_collection.query(
            query_texts=[query_text],
            n_results=min(n_results, 10)
        )

        if not results["ids"][0]:
            return []

        # return article ids
        article_ids = []
        for metadata in results["metadatas"][0]:
            aid = metadata.get("article_id")
            if aid:
                article_ids.append(int(aid))

        return article_ids

    except Exception as e:
        print(f"ChromaDB similarity search error: {e}")
        return []