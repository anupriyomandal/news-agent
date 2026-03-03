from __future__ import annotations

import re
from collections import defaultdict

from .config import RSS_SOURCES_BY_TOPIC

TOPIC_KEYWORDS = {
    "sports": {
        "cricket",
        "t20",
        "ipl",
        "semi",
        "semifinal",
        "semi-final",
        "final",
        "finals",
        "fifa",
        "uefa",
        "football",
        "soccer",
        "tennis",
        "nba",
        "nfl",
        "olympics",
        "world cup",
        "match",
        "team",
        "tournament",
        "icc",
    },
    "markets": {
        "stock",
        "stocks",
        "share",
        "shares",
        "market",
        "markets",
        "nasdaq",
        "dow",
        "sensex",
        "nifty",
        "adani",
        "earnings",
        "inflation",
        "gdp",
        "oil",
        "bond",
        "rupee",
        "forex",
    },
    "geopolitics": {
        "war",
        "conflict",
        "israel",
        "iran",
        "ukraine",
        "russia",
        "china",
        "military",
        "missile",
        "defense",
        "diplomacy",
        "sanctions",
        "election",
        "minister",
        "summit",
        "ceasefire",
        "un",
        "nato",
    },
    "technology": {
        "ai",
        "artificial intelligence",
        "startup",
        "startups",
        "tech",
        "technology",
        "chip",
        "chips",
        "semiconductor",
        "openai",
        "google",
        "microsoft",
        "apple",
        "cyber",
        "software",
        "llm",
        "model",
        "regulation",
    },
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _topic_scores(query: str) -> dict[str, int]:
    q = query.lower()
    tokens = set(_tokenize(query))
    scores: dict[str, int] = defaultdict(int)

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if " " in keyword:
                if keyword in q:
                    scores[topic] += 2
            elif keyword in tokens:
                scores[topic] += 1
    return dict(scores)


def infer_topics(query: str) -> list[str]:
    scores = _topic_scores(query)

    if not scores:
        return ["general"]

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_score = ranked[0][1]
    selected = [topic for topic, score in ranked if score >= max(1, best_score - 1)]
    selected = selected[:2]

    # Always blend general coverage with domain-specific feeds.
    if "general" not in selected:
        selected.append("general")
    return selected


def sources_for_query(query: str) -> list[dict[str, str]]:
    scores = _topic_scores(query)
    # Sports queries are strict: only sports feeds.
    if scores:
        top_topic, top_score = sorted(scores.items(), key=lambda item: item[1], reverse=True)[0]
        second_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
        if top_topic == "sports" and top_score >= max(1, second_score + 1):
            topics = ["sports"]
        else:
            topics = infer_topics(query)
    else:
        topics = ["general"]

    seen = set()
    selected_sources: list[dict[str, str]] = []
    for topic in topics:
        for src in RSS_SOURCES_BY_TOPIC.get(topic, []):
            name = src["name"]
            if name in seen:
                continue
            seen.add(name)
            selected_sources.append(src)
    return selected_sources


def allowed_source_names(query: str) -> set[str]:
    return {src["name"] for src in sources_for_query(query)}
