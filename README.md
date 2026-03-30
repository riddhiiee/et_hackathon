# 🚀 ET ContentFlow

> **ET AI Hackathon 2026 — Problem Statements #1 + #8**
> *Read. Create. Grow.*

An AI-native platform that **personalizes news** and **instantly generates multi-platform content** using LLMs and multi-agent pipelines.

---

## 📌 Overview

**ET ContentFlow** solves two major problems:

* 📰 **For Readers:** Delivers a personalized news feed based on interests and behavior
* ✍️ **For Creators:** Converts any article into LinkedIn posts, Twitter threads, Instagram captions, and video scripts in seconds

---

## ⚡ Features

* Personalized news ranking (0–10 relevance score)
* Multi-agent pipelines using LangGraph
* One-click content generation (4 formats)
* Self-correcting AI fact-checking (compliance agent)
* Behavior-based adaptive learning
* Semantic search using ChromaDB

---

## 🎥 Demo Flow

```text
Register → Set Interests → Load Feed
↓
Articles ranked based on profile
↓
Click “Create Content”
↓
Generate 4 formats in ~20 seconds
↓
Compliance agent verifies & corrects
```

---

## 🏗️ Architecture

### 🔹 Three-Pipeline System

**1. Consumer Pipeline (Personalization Engine)**
```text
news_fetcher → enrichment → personalization → feed
```

**2. Creator Pipeline (Content Engine)**
```text
content_generation → tone_adaptation → compliance → distribution
```

**3. Strategist Pipeline (Learning Engine)**
```text
performance_tracker → pattern_recognition → strategy → profile update
```

---

## 🛠️ Tech Stack

| Layer       | Technology                        |
| ----------- | --------------------------------- |
| LLM         | LLaMA 3.3-70B via Groq            |
| Agents      | LangGraph                         |
| News Source | ET RSS + feedparser + newspaper3k |
| Vector DB   | ChromaDB                          |
| Database    | SQLite                            |
| Frontend    | Streamlit                         |
| Auth        | Gmail SMTP + OTP                  |

---

## 📂 Project Structure

```text
et-contentflow/
├── app.py
├── state.py
├── agents/
├── pipelines/
├── database/
├── utils/
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone Repo

```bash
git clone https://github.com/your-username/et-contentflow.git
cd et-contentflow
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file:

```env
GROQ_API_KEY=your_api_key
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

### 5. Initialize Database

```bash
python -c "from database.db import init_db; init_db()"
```

### 6. Run Application

```bash
streamlit run app.py
```

Open 👉 [http://localhost:8501](http://localhost:8501)

---

## ⚠️ First Run Notes

* ChromaDB downloads ~100MB model on first run
* Initial feed load: **30–45 seconds**
* Subsequent loads are faster due to caching

---

## 📦 Requirements

```text
streamlit
langgraph
langchain-groq
feedparser
newspaper3k
chromadb
python-dotenv
requests
```

---

## 🔐 Environment Variables

| Variable           | Description        |
| ------------------ | ------------------ |
| GROQ_API_KEY       | LLM API key        |
| GMAIL_EMAIL        | Email for OTP      |
| GMAIL_APP_PASSWORD | Gmail App Password |

---

## ⚠️ Known Issues

* ⏳ Groq free tier limit: 100K tokens/day

---

## 📈 Impact

* ⏱️ Content creation time reduced from **hours → seconds**
* 🎯 Personalized feed improves engagement
* 🤖 Fully automated AI-native workflow

---

## 🏁 Built At

**ET AI Hackathon 2026 — March 2026**
*Economic Times × AI*
