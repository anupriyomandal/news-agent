import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "news.db"
FAISS_INDEX_PATH = DATA_DIR / "news.index"
FAISS_META_PATH = DATA_DIR / "news_index_meta.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-5.2")

RSS_SOURCES_BY_TOPIC = {
    "general": [
        {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews"},
        {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "NPR World", "url": "https://feeds.npr.org/1004/rss.xml"},
        {"name": "DW World", "url": "https://rss.dw.com/rdf/rss-en-world"},
        {"name": "The Hindu National", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
    ],
    "geopolitics": [
        {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews"},
        {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "Al Jazeera World", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        {"name": "UN News", "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"},
        {"name": "The Diplomat", "url": "https://thediplomat.com/feed/"},
        {"name": "The Hindu National", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
    ],
    "markets": [
        {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
        {"name": "CNBC Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        {"name": "MarketWatch Top Stories", "url": "http://feeds.marketwatch.com/marketwatch/topstories/"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "ET Markets", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"},
    ],
    "sports": [
        {"name": "Reuters Sports", "url": "https://feeds.reuters.com/reuters/sportsNews"},
        {"name": "ESPN Top News", "url": "https://www.espn.com/espn/rss/news"},
        {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/rss.xml?edition=uk"},
        {"name": "Sky Sports", "url": "https://www.skysports.com/rss/12040"},
        {"name": "Cricbuzz", "url": "https://www.cricbuzz.com/cricket-news/rss"},
    ],
    "technology": [
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "Ars Technica", "url": "http://feeds.arstechnica.com/arstechnica/index"},
        {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
        {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    ],
}


def _flatten_sources() -> list[dict[str, str]]:
    seen = set()
    merged: list[dict[str, str]] = []
    for sources in RSS_SOURCES_BY_TOPIC.values():
        for src in sources:
            name = src["name"]
            if name in seen:
                continue
            seen.add(name)
            merged.append(src)
    return merged


RSS_SOURCES = _flatten_sources()

INGEST_INTERVAL_MINUTES = int(os.getenv("INGEST_INTERVAL_MINUTES", "15"))
ENABLE_INTERNAL_SCHEDULER = os.getenv("ENABLE_INTERNAL_SCHEDULER", "true").lower() in {"1", "true", "yes", "on"}
INGEST_ON_STARTUP = os.getenv("INGEST_ON_STARTUP", "true").lower() in {"1", "true", "yes", "on"}
INGEST_API_TOKEN = os.getenv("INGEST_API_TOKEN", "")
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "20"))
PIPELINE_MAX_ARTICLES = int(os.getenv("PIPELINE_MAX_ARTICLES", "12"))
QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "600"))
FRESH_SEARCH_ONLY = os.getenv("FRESH_SEARCH_ONLY", "true").lower() in {"1", "true", "yes", "on"}

DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
CORS_ORIGINS = [item.strip() for item in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",") if item.strip()]
