import sqlite3
import json
import os

db_path = 'contentflow.db'
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    #users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        profession TEXT,
        interests TEXT,
        format_preference TEXT,
        language TEXT,
        creator_mode INTEGER,
        dynamic_profile TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #articles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        summary TEXT,
        full_text TEXT,
        image_url TEXT,
        article_url TEXT,
        topic TEXT,
        published_at TEXT,
        is_cached INTEGER DEFAULT 1,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #interactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        article_id INTEGER REFERENCES articles(id),
        action TEXT,
        time_spent INTEGER,
        topic TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #content
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS generated_content(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        article_id INTEGER REFERENCES articles(id),
        linkedin_post TEXT,
        twitter_post TEXT,
        insta_post TEXT,
        video_script TEXT,
        accuracy_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #performance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        content_id INTEGER REFERENCES generated_content(id),
        platform TEXT,
        views INTEGER,
        likes INTEGER,
        shares INTEGER,
        topic TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("database initialized")
        

def save_user(name, profession, interests, format_pref, language, creator_mode):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    dynamic_profile = json.dumps({
        "topic_scores": {topic: 0.5 for topic in interests},
        "best_format": format_pref,
        "total_interactions": 0
    })

    cursor.execute("""
        INSERT INTO users
        (name, profession, interests, format_preference, language, creator_mode, dynamic_profile)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, profession, json.dumps(interests), format_pref, language, int(creator_mode), dynamic_profile))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "name": row[1],
            "profession": row[2],
            "interests": json.loads(row[3]),
            "format_preference": row[4],
            "language": row[5],
            "creator_mode": bool(row[6]),
            "dynamic_profile": json.loads(row[7]),
            "created_at": row[8]
        }
    return None


def update_dynamic_profile(user_id, topic, action):
    weights = {
        "skipped":          -0.05,
        "clicked":          +0.05,
        "read_partial":     +0.10,
        "read_full":        +0.20,
        "created_content":  +0.35,
        "shared":           +0.30
    }

    user = get_user(user_id)
    if not user:
        return

    profile = user["dynamic_profile"]
    topic_scores = profile.get("topic_scores", {})

    current = topic_scores.get(topic, 0.5)
    updated = max(0.0, min(1.0, current + weights.get(action, 0)))
    topic_scores[topic] = round(updated, 2)
    profile["topic_scores"] = topic_scores
    profile["total_interactions"] = profile.get("total_interactions", 0) + 1

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET dynamic_profile = ? WHERE id = ?
    """, (json.dumps(profile), user_id))
    conn.commit()
    conn.close()


# ─── ARTICLE FUNCTIONS ─────────────────────────────

def save_article(title, summary, full_text, image_url, article_url, topic, published_at):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # avoid duplicates
    cursor.execute("SELECT id FROM articles WHERE article_url = ?", (article_url,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing[0]

    cursor.execute("""
        INSERT INTO articles
        (title, summary, full_text, image_url, article_url, topic, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, summary, full_text, image_url, article_url, topic, published_at))

    article_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return article_id


def get_cached_articles(topic, minutes=30):
    """Returns articles fetched within last X minutes for a topic"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM articles
        WHERE topic = ?
        AND fetched_at > datetime('now', ?)
        ORDER BY published_at DESC
        LIMIT 10
    """, (topic, f'-{minutes} minutes'))

    rows = cursor.fetchall()
    conn.close()
    return [_row_to_article(row) for row in rows]


def _row_to_article(row):
    return {
        "id": row[0],
        "title": row[1],
        "summary": row[2],
        "full_text": row[3],
        "image_url": row[4],
        "article_url": row[5],
        "topic": row[6],
        "published_at": row[7],
        "fetched_at": row[9]
    }


def cleanup_old_articles():
    """Delete articles older than 24 hours with no interactions"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM articles
        WHERE fetched_at < datetime('now', '-24 hours')
        AND id NOT IN (
            SELECT DISTINCT article_id FROM interactions
        )
    """)

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Cleaned up {deleted} old articles")


# ─── INTERACTION FUNCTIONS ─────────────────────────

def log_interaction(user_id, article_id, action, time_spent, topic):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interactions (user_id, article_id, action, time_spent, topic)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, article_id, action, time_spent, topic))

    conn.commit()
    conn.close()

    # silently update profile on every interaction
    update_dynamic_profile(user_id, topic, action)


def get_user_interactions(user_id, limit=50):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM interactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows


# ─── GENERATED CONTENT FUNCTIONS ───────────────────

def save_generated_content(user_id, article_id, linkedin, twitter, instagram, video_script, accuracy_score):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO generated_content
        (user_id, article_id, linkedin_post, twitter_post, instagram_post, video_script, accuracy_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, article_id, linkedin, twitter, instagram, video_script, accuracy_score))

    content_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return content_id


def get_user_generated_content(user_id, limit=20):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM generated_content
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows


# ─── PERFORMANCE FUNCTIONS ─────────────────────────

def save_performance(user_id, content_id, platform, views, likes, shares, topic):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO performance
        (user_id, content_id, platform, views, likes, shares, topic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, content_id, platform, views, likes, shares, topic))

    conn.commit()
    conn.close()


def get_user_performance(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM performance
        WHERE user_id = ?
        ORDER BY logged_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows