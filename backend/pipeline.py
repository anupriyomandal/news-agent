from __future__ import annotations

import json
from ast import literal_eval
from collections import OrderedDict
from datetime import datetime
from functools import lru_cache
from typing import Any

from openai import OpenAI

from .config import LLM_MODEL, OPENAI_API_KEY


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def _extract_json(text: str) -> Any:
    text = text.strip()
    if not text:
        raise ValueError("Empty model output")

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    candidates = [text]
    first = min([i for i in [text.find("["), text.find("{")] if i != -1], default=-1)
    last_arr = text.rfind("]")
    last_obj = text.rfind("}")
    last = max(last_arr, last_obj)
    if first != -1 and last != -1 and last > first:
        candidates.append(text[first : last + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        try:
            parsed = literal_eval(candidate)
            if isinstance(parsed, (dict, list)):
                return parsed
        except Exception:  # noqa: BLE001
            pass

    raise ValueError("Model output was not parseable as JSON")


def _ask_json(prompt: str, payload: Any) -> Any:
    client = _client()
    response = client.responses.create(
        model=LLM_MODEL,
        temperature=0,
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Return valid JSON only. Do not include markdown or commentary.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": f"{prompt}\n\nINPUT:\n{json.dumps(payload)}"}],
            },
        ],
    )
    return _extract_json(response.output_text)


def _article_payload(article: dict[str, Any]) -> dict[str, str]:
    return {
        "title": article.get("title", ""),
        "description": article.get("description", ""),
        "content": article.get("content", ""),
        "source": article.get("source", ""),
        "url": article.get("url", ""),
        "published_at": str(article.get("published_at", "")),
    }


def _normalize_sections(grouped: Any, deduped_facts: list[str]) -> OrderedDict[str, list[str]]:
    sections: OrderedDict[str, list[str]] = OrderedDict()

    if isinstance(grouped, dict):
        for heading, value in grouped.items():
            key = str(heading).strip()
            if not key:
                continue
            if isinstance(value, list):
                facts = [str(item).strip() for item in value if str(item).strip()]
            elif isinstance(value, str) and value.strip():
                facts = [value.strip()]
            else:
                facts = []
            if facts:
                sections[key] = facts
    elif isinstance(grouped, list):
        for item in grouped:
            if not isinstance(item, dict):
                continue
            key = str(item.get("heading", "")).strip()
            value = item.get("facts", [])
            if not key:
                continue
            if isinstance(value, list):
                facts = [str(f).strip() for f in value if str(f).strip()]
            elif isinstance(value, str) and value.strip():
                facts = [value.strip()]
            else:
                facts = []
            if facts:
                sections[key] = facts

    if not sections:
        fallback = [fact for fact in deduped_facts if str(fact).strip()][:12]
        if fallback:
            sections["Key Developments"] = [str(f).strip() for f in fallback]
        else:
            sections["Key Developments"] = []

    return sections


def _normalize_implications(value: Any) -> str:
    if isinstance(value, list):
        return "\n\n".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return "\n\n".join(f"{k}: {v}" for k, v in value.items() if str(v).strip())

    text = str(value or "").strip()
    if not text:
        return ""

    # Handle JSON/list-like serialized output returned as string.
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return "\n\n".join(str(item).strip() for item in parsed if str(item).strip())
        except Exception:  # noqa: BLE001
            pass
        try:
            parsed = literal_eval(text)
            if isinstance(parsed, list):
                return "\n\n".join(str(item).strip() for item in parsed if str(item).strip())
        except Exception:  # noqa: BLE001
            pass
        text = text.strip("[]").strip()

    return text.strip("'\"").strip()


def run_pipeline(query: str, articles: list[dict[str, Any]]) -> dict[str, Any]:
    if not articles:
        raise ValueError("No articles supplied for pipeline")

    stage1_facts: list[str] = []
    stage1_prompt = (
        "For each article, extract all key factual developments. "
        "Return a JSON object where each key is article_url and each value is a JSON array of distinct factual bullet points. "
        "Each fact must be one sentence. Neutral tone. No summarization. No interpretation."
    )
    stage1_payload = {"articles": [_article_payload(article) for article in articles]}
    stage1_result = _ask_json(stage1_prompt, stage1_payload)
    if isinstance(stage1_result, dict):
        for facts in stage1_result.values():
            if isinstance(facts, list):
                stage1_facts.extend([str(f).strip() for f in facts if str(f).strip()])
    elif isinstance(stage1_result, list):
        stage1_facts.extend([str(f).strip() for f in stage1_result if str(f).strip()])
    if not stage1_facts:
        stage1_facts = [
            f"{article.get('source', 'Source')}: {(article.get('title') or '').strip()}"
            for article in articles
            if (article.get("title") or "").strip()
        ]

    dedup_prompt = (
        "Merge semantically identical facts. Remove duplicates. "
        "Preserve all distinct information. Output JSON array."
    )
    deduped = _ask_json(dedup_prompt, stage1_facts)
    deduped_facts = deduped if isinstance(deduped, list) else stage1_facts
    deduped_facts = [str(item).strip() for item in deduped_facts if str(item).strip()]

    section_prompt = (
        "Create dynamic report sections from these facts. "
        "Generate 4 to 8 concise, content-specific section headings derived from the facts. "
        "Do not use boilerplate headings unless facts clearly support them. "
        "Do not add sections that have no evidence. "
        "Return JSON object with heading as key and value as array of factual bullets assigned to that heading."
    )
    grouped = _ask_json(section_prompt, deduped_facts)
    structured_sections = _normalize_sections(grouped, deduped_facts)

    tldr_prompt = (
        "From structured facts, generate 4 to 6 critical takeaways. "
        "Bullet format. Analytical journalistic tone. No speculation. "
        "Only use provided facts. Output JSON array."
    )
    tldr = _ask_json(tldr_prompt, structured_sections)
    if not isinstance(tldr, list):
        tldr = []
    tldr = [str(item).strip() for item in tldr if str(item).strip()][:6]

    report_prompt = (
        "You are an experienced analytical journalist. Use only the supplied facts. "
        "Return JSON object with keys: headline, section_writeups, implications. "
        "section_writeups must be an object with exactly the same headings as structured_facts keys. "
        "Write detailed analytical prose per heading with attribution where relevant. Do not use phrases like the supplied facts state, etc."
        "Across section_writeups plus implications, target a total length between 200 and 500 words. "
        "Use depth, chronology, actor analysis, and evidence-based contrasts. "
        "If evidence is thin, stay precise and avoid placeholder language such as 'no updates' unless explicitly in facts. "
        "No speculation or emotional language."
    )
    report = _ask_json(
        report_prompt,
        {
            "query": query,
            "structured_facts": structured_sections,
            "sources": [{"title": a.get("title"), "source": a.get("source")} for a in articles],
        },
    )
    if not isinstance(report, dict):
        report = {}

    section_writeups = report.get("section_writeups", {}) if isinstance(report.get("section_writeups"), dict) else {}
    sections: OrderedDict[str, str] = OrderedDict()
    for heading, facts in structured_sections.items():
        fallback = " ".join(facts)
        content = section_writeups.get(heading, fallback)
        text = str(content).strip()
        if text:
            sections[heading] = text

    if not sections:
        sections["Key Developments"] = " ".join(deduped_facts[:8]).strip()

    source_count = len({a.get("url") for a in articles if a.get("url")})
    metadata = f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | {source_count} sources"

    implications = _normalize_implications(
        report.get("implications")
        or "Analysts are monitoring incoming confirmed updates and source-level consistency across coverage."
    )

    return {
        "headline": str(report.get("headline") or f"News Intelligence Report: {query}").strip(),
        "metadata": metadata,
        "tldr": tldr,
        "sections": sections,
        "implications": implications,
    }
