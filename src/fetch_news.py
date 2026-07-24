"""
fetch_news.py
Pulls AI-related news from NewsAPI and a curated list of RSS feeds.
Returns a deduplicated list of article dicts:
    { "title": str, "url": str, "source": str, "published": str, "description": str }
"""

import os
import requests
import feedparser
from datetime import datetime, timedelta, timezone

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Queries used against NewsAPI — tweak these to change topic focus
QUERIES = [
    "artificial intelligence",
    "AI model release",
    "large language model",
    "AI regulation",
    "generative AI",
]

# Curated worldwide AI-focused RSS feeds — add/remove as you like
RSS_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
}

MAX_ARTICLES = 15  # total number of stories to keep per day


def fetch_from_newsapi():
    if not NEWSAPI_KEY:
        print("No NEWSAPI_KEY set, skipping NewsAPI fetch.")
        return []

    since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    articles = []

    for query in QUERIES:
        params = {
            "q": query,
            "from": since,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 10,
            "apiKey": NEWSAPI_KEY,
        }
        try:
            resp = requests.get(NEWSAPI_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("articles", []):
                articles.append({
                    "title": item.get("title", "").strip(),
                    "url": item.get("url", ""),
                    "source": item.get("source", {}).get("name", "Unknown"),
                    "published": item.get("publishedAt", ""),
                    "description": (item.get("description") or "").strip(),
                })
        except requests.RequestException as e:
            print(f"NewsAPI fetch failed for query '{query}': {e}")

    return articles


def fetch_from_rss():
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    for name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                    pub_str = pub_dt.isoformat()
                else:
                    pub_str = ""

                articles.append({
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "source": name,
                    "published": pub_str,
                    "description": (entry.get("summary") or "").strip(),
                })
        except Exception as e:
            print(f"RSS fetch failed for {name}: {e}")

    return articles


def dedupe(articles):
    """Remove near-duplicate stories based on normalized title."""
    seen = set()
    unique = []
    for a in articles:
        key = a["title"].lower().strip()
        key = "".join(ch for ch in key if ch.isalnum() or ch == " ")
        if key and key not in seen and len(a["title"]) > 10:
            seen.add(key)
            unique.append(a)
    return unique


def get_daily_articles():
    articles = fetch_from_newsapi() + fetch_from_rss()
    articles = dedupe(articles)
    # Sort newest first when we have a timestamp
    articles.sort(key=lambda a: a.get("published") or "", reverse=True)
    return articles[:MAX_ARTICLES]


if __name__ == "__main__":
    results = get_daily_articles()
    print(f"Fetched {len(results)} unique articles.")
    for a in results:
        print(f"- [{a['source']}] {a['title']}")
