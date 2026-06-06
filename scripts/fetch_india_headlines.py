#!/usr/bin/env python3
"""Refresh the India headlines MVP data from public RSS feeds.

Stage 1 architecture:
- dependency-free Python collector
- source-level fetch status
- conservative dedupe
- auditable JSON edition artifact
- browser-loadable JS data artifact for src/index.html
"""

from __future__ import annotations

import argparse
import concurrent.futures
import email.utils
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")

CLUSTER_STOPWORDS = frozenset({
    # Articles, conjunctions, prepositions
    "the", "and", "for", "not", "but", "nor", "yet", "its", "our",
    "with", "from", "into", "over", "under", "after", "before", "amid",
    "that", "this", "upon", "than", "then", "else", "till", "until",
    # Auxiliary and common verbs
    "says", "said", "told", "asks", "will", "have", "been", "were",
    "was", "are", "has", "had", "may", "can", "could", "would", "should",
    "gets", "got", "set", "put", "let", "keep", "kept", "show", "shows",
    "move", "call", "hold", "holds", "ask", "need",
    # Determiners and numbers
    "all", "any", "few", "more", "most", "one", "two", "three", "four",
    "five", "six", "some", "each", "per", "here", "there",
    # News filler words
    "new", "day", "days", "now", "ago", "week", "year", "years", "month",
    "latest", "first", "last", "next", "just", "even", "only", "also",
    "much", "many", "such", "very", "well", "long", "high", "low", "big",
    "use", "used", "open", "opened", "public", "come", "coming",
    # Common Indian news context words (too generic to cluster on)
    "india", "indian", "nation", "national", "state", "govt", "government",
    "centre", "central", "report", "news", "amid", "claim", "claims",
})

CLUSTER_MIN_WORD_LEN = 3
CLUSTER_MIN_SHARED = 2
CLUSTER_JACCARD = 0.20

TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "pfrom",
}


@dataclass(frozen=True)
class FeedSource:
    id: str
    name: str
    feed_url: str
    site_url: str
    source_type: str = "newspaper"
    section: str = "India"
    country_scope: str = "India"
    is_free_to_read: bool = True
    policy_notes: str = "Official public feed for online India news."
    category: str = "India"
    enabled: bool = True
    allow_missing_date: bool = False  # treat items with no pubDate as edition-date items


SOURCES = [
    FeedSource(
        id="indian-express",
        name="The Indian Express",
        feed_url="https://indianexpress.com/section/india/feed/",
        site_url="https://indianexpress.com/section/india/",
        section="India",
        policy_notes="Indian newspaper; official public India section RSS feed.",
    ),
    FeedSource(
        id="times-of-india",
        name="The Times of India",
        feed_url="https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        site_url="https://timesofindia.indiatimes.com/india",
        section="India",
        policy_notes="Indian newspaper; public India RSS feed. Feed omits pubDate — items assumed current.",
        allow_missing_date=True,
    ),
    FeedSource(
        id="ndtv",
        name="NDTV",
        feed_url="https://feeds.feedburner.com/ndtvnews-india-news",
        site_url="https://www.ndtv.com/india-news",
        source_type="digital_news_publisher",
        section="India",
        policy_notes=(
            "Free public India news feed; included as online source data but not a "
            "strict newspaper source."
        ),
    ),
    FeedSource(
        id="hindustan-times",
        name="Hindustan Times",
        feed_url="https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        site_url="https://www.hindustantimes.com/india-news",
        section="India",
        policy_notes="Indian newspaper; official public India news RSS feed.",
    ),
    FeedSource(
        id="the-hindu",
        name="The Hindu",
        feed_url="https://www.thehindu.com/news/national/feeder/default.rss",
        site_url="https://www.thehindu.com/news/national/",
        section="National",
        policy_notes="Indian newspaper; official public national news RSS feed.",
    ),
    FeedSource(
        id="business-standard",
        name="Business Standard",
        feed_url="https://www.business-standard.com/rss/latest.rss",
        site_url="https://www.business-standard.com/india-news",
        section="Latest",
        policy_notes=(
            "Indian business newspaper; public feed returns HTTP 403 — disabled until a "
            "working feed URL is confirmed."
        ),
        category="Business",
        enabled=False,
    ),
    FeedSource(
        id="the-hindu-environment",
        name="The Hindu – Environment",
        feed_url="https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss",
        site_url="https://www.thehindu.com/sci-tech/energy-and-environment/",
        source_type="newspaper",
        section="Environment",
        category="Environment",
        policy_notes="Indian newspaper; official public environment section RSS feed. Includes international environment news relevant to GS3.",
    ),
    FeedSource(
        id="the-hindu-science",
        name="The Hindu – Science & Tech",
        feed_url="https://www.thehindu.com/sci-tech/science/feeder/default.rss",
        site_url="https://www.thehindu.com/sci-tech/science/",
        source_type="newspaper",
        section="Science",
        category="Science",
        policy_notes="Indian newspaper; official public science and technology RSS feed. Includes international science news relevant to GS3.",
    ),
    FeedSource(
        id="livemint",
        name="Mint",
        feed_url="https://www.livemint.com/rss/economy",
        site_url="https://www.livemint.com/economy",
        source_type="newspaper",
        section="Economy",
        category="Business",
        policy_notes="Indian business newspaper; official public economy section RSS feed.",
    ),
    FeedSource(
        id="pib",
        name="PIB",
        feed_url="https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        site_url="https://pib.gov.in/",
        source_type="pib",
        section="Government",
        category="India",
        policy_notes=(
            "Press Information Bureau — official Government of India press releases. "
            "RSS is Hindi-only; fetches English companion releases via two-step PRID resolution."
        ),
    ),
]


def source_metadata(source: FeedSource) -> dict[str, Any]:
    return {
        "sourceType": source.source_type,
        "section": source.section,
        "countryScope": source.country_scope,
        "isFreeToRead": source.is_free_to_read,
        "policyNotes": source.policy_notes,
    }


def clean_text(value: Optional[str]) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(clean_text(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST)


def parse_edition_date(value: Optional[str]) -> date:
    if not value:
        return datetime.now(IST).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = urllib.parse.urlencode(
        [(key, val) for key, val in query_pairs if key.lower() not in TRACKING_QUERY_KEYS]
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), query, "")
    )


def normalize_title(value: str) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:90] or "headline"


def significant_words(title: str) -> frozenset[str]:
    tokens = re.findall(r"[a-z0-9]+", title.lower())
    return frozenset(
        t for t in tokens
        if len(t) >= CLUSTER_MIN_WORD_LEN and t not in CLUSTER_STOPWORDS
    )


def cluster_headlines(headlines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n = len(headlines)
    if n == 0:
        return headlines

    word_sets = [significant_words(h["title"]) for h in headlines]
    cluster_of = list(range(n))

    for i in range(n):
        for j in range(i + 1, n):
            if cluster_of[i] == cluster_of[j]:
                continue
            shared = word_sets[i] & word_sets[j]
            if len(shared) < CLUSTER_MIN_SHARED:
                continue
            union_size = len(word_sets[i] | word_sets[j])
            if union_size and len(shared) / union_size >= CLUSTER_JACCARD:
                old_id, new_id = cluster_of[j], cluster_of[i]
                for k in range(n):
                    if cluster_of[k] == old_id:
                        cluster_of[k] = new_id

    groups: dict[int, list[int]] = {}
    for idx, cid in enumerate(cluster_of):
        groups.setdefault(cid, []).append(idx)

    for members in groups.values():
        size = len(members)
        cluster_slug = headlines[members[0]]["id"][:50] if size > 1 else None
        for rank, idx in enumerate(members):
            headlines[idx]["clusterId"] = cluster_slug
            headlines[idx]["clusterSize"] = size
            headlines[idx]["isClusterLead"] = rank == 0

    return headlines


def truncate_excerpt(text: str, max_chars: int = 300) -> str:
    if not text or len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:
        cut = cut[:last_space]
    return cut + "…"


ARTICLE_TEXT_MAX_CHARS = 1500

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# Strip entire tag subtrees that are pure noise before content extraction
_STRIP_SUBTREE_RE = re.compile(
    r"<(script|style|nav|header|footer|aside|form|figure|figcaption|noscript)"
    r"(\s[^>]*)?>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)

# Known article body container patterns (class/id substrings)
_CONTENT_PATTERNS = re.compile(
    r'(?:article[_-]?(?:body|content|text)|story[_-]?(?:body|content|text)'
    r'|entry[_-]?content|post[_-]?content|field-body|art-body'
    r'|article__body|td-post-content|artText|articleBody)',
    re.IGNORECASE,
)
_CONTENT_BLOCK_RE = re.compile(
    r'<(?:div|article|section|main)([^>]*)>(.*?)</(?:div|article|section|main)>',
    re.IGNORECASE | re.DOTALL,
)


def _text_from_html(fragment: str) -> str:
    text = _HTML_TAG_RE.sub(" ", fragment)
    text = html.unescape(text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _looks_like_json(text: str) -> bool:
    sample = text.lstrip()[:20]
    return sample.startswith("{") or sample.startswith("[")


def _extract_article_body(raw_html: str) -> str:
    cleaned = _STRIP_SUBTREE_RE.sub(" ", raw_html)

    # Find all block elements whose class/id suggests article body
    best = ""
    for m in _CONTENT_BLOCK_RE.finditer(cleaned):
        attrs, inner = m.group(1), m.group(2)
        if _CONTENT_PATTERNS.search(attrs):
            text = _text_from_html(inner)
            if not _looks_like_json(text) and len(text) > len(best):
                best = text

    if best:
        return best

    # Fallback: find the longest <p>…</p> run in the page
    paras = re.findall(r"<p[^>]*>(.*?)</p>", cleaned, re.IGNORECASE | re.DOTALL)
    para_texts = [_text_from_html(p) for p in paras if len(p) > 80]
    if para_texts:
        return " ".join(para_texts)

    return ""


def fetch_article_text(url: str, timeout: int = 10) -> str:
    """Fetch article page and return heuristically extracted body text."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; newAgg/0.1; +https://github.com/local/newAgg)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                return ""
            raw = resp.read(512 * 1024).decode("utf-8", errors="replace")
    except Exception:
        return ""
    body = _extract_article_body(raw)
    return truncate_excerpt(body, ARTICLE_TEXT_MAX_CHARS)


_PIB_DATETIME_RE = re.compile(
    r"(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})"
    r"(?:\s+(\d{1,2}):(\d{2})(AM|PM))?",
    re.IGNORECASE,
)
_PIB_MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
_PIB_ENGLISH_PRID_RE = re.compile(
    r"PRID=(\d+)[^>]{0,60}>\s*English\s*</a>", re.IGNORECASE
)


def _pib_fetch_page(prid: int) -> str:
    url = f"https://pib.gov.in/PressReleaseIframePage.aspx?PRID={prid}&reg=3&lang=2"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _pib_extract_datetime(raw: str) -> Optional[datetime]:
    clean = re.sub(r"<[^>]+>", " ", raw)
    m = _PIB_DATETIME_RE.search(clean)
    if not m:
        return None
    try:
        day = int(m.group(1))
        month = _PIB_MONTHS[m.group(2).upper()]
        year = int(m.group(3))
        hour, minute = 9, 0
        if m.group(4) and m.group(5) and m.group(6):
            hour = int(m.group(4))
            minute = int(m.group(5))
            if m.group(6).upper() == "PM" and hour != 12:
                hour += 12
            elif m.group(6).upper() == "AM" and hour == 12:
                hour = 0
        return datetime(year, month, day, hour, minute, 0, tzinfo=IST)
    except (ValueError, KeyError):
        return None


def _pib_strip_html(raw: str) -> str:
    """Remove scripts/styles and return visible text.

    Unescapes HTML entities before stripping tags so that encoded tags
    like `&lt;i>` inside attribute values don't short-circuit the
    tag-stripping regex via their embedded `>` characters.
    """
    # Decode entities first so <meta content="&lt;i>foo"> becomes <meta content="<i>foo">
    raw = html.unescape(raw)
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", raw)
    # Second unescape for double-encoded entities; second strip for any revealed tags
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text)


def _pib_parse_english_content(raw: str) -> dict[str, str]:
    """Extract title, ministry, excerpt, articleText from English PRID page HTML."""
    # Use og:title as the authoritative title — it's the full English headline
    # and avoids the text-extraction heuristics picking up partial fragments
    og_m = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\'<>]+)["\']',
        raw, re.IGNORECASE,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\'<>]+)["\'][^>]+property=["\']og:title["\']',
        raw, re.IGNORECASE,
    )
    title = html.unescape(og_m.group(1)).strip() if og_m else ""

    text = _pib_strip_html(raw)
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]
    skip_patterns = re.compile(
        r"^(Press (Release:|Information)|function |var |if\s*\(|Read this|Visitor|Release ID|\*\*\*\*)",
        re.IGNORECASE,
    )
    date_line_re = re.compile(r"^\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{4}", re.IGNORECASE)

    ministry = ""
    body_parts: list[str] = []
    # Deduplicate lines (PIB pages often repeat content twice)
    seen_lines: set[str] = set()

    for line in lines:
        if skip_patterns.match(line):
            continue
        if date_line_re.match(line):
            continue
        norm = re.sub(r"\s+", " ", line[:80])
        if norm in seen_lines:
            continue
        seen_lines.add(norm)
        if not ministry and re.match(r"Ministry|Department|Cabinet|PMO|NHRC|Commission", line, re.IGNORECASE):
            ministry = line
            continue
        # Skip lines that are substrings of the title (og:title fragments)
        if title and line in title:
            continue
        if len(body_parts) < 6 and len(line) > 40:
            body_parts.append(line)

    body = " ".join(body_parts)
    body = re.sub(r"\s+", " ", body).strip()[:ARTICLE_TEXT_MAX_CHARS]
    return {
        "title": title,
        "ministry": ministry,
        "excerpt": truncate_excerpt(body, 300),
        "articleText": body,
    }


def _pib_resolve_one(hindi_prid: int, edition_date: date) -> Optional[dict[str, Any]]:
    """
    Fetch Hindi PRID page → find English PRID → fetch English page → return headline dict.
    Returns None if no English companion or wrong date.
    """
    hindi_raw = _pib_fetch_page(hindi_prid)
    if not hindi_raw:
        return None

    release_dt = _pib_extract_datetime(hindi_raw)
    if release_dt is None or release_dt.date() != edition_date:
        return None

    m = _PIB_ENGLISH_PRID_RE.search(hindi_raw)
    if not m:
        return None  # No English version of this release
    eng_prid = int(m.group(1))

    eng_raw = _pib_fetch_page(eng_prid)
    if not eng_raw:
        return None

    content = _pib_parse_english_content(eng_raw)
    if not content.get("title"):
        return None
    url = f"https://pib.gov.in/PressReleasePage.aspx?PRID={eng_prid}"
    return {
        "id": slugify(f"pib-{content['title']}"),
        "sourceId": "pib",
        "source": "PIB",
        "title": content["title"],
        "excerpt": content["excerpt"],
        "articleText": content["articleText"],
        "category": "India",
        "priority": "Medium",
        "url": canonical_url(url),
        "publishedAt": release_dt.isoformat(timespec="seconds"),
        "_dedupeTitle": normalize_title(content["title"]),
        "_dedupeUrl": canonical_url(url),
    }


def fetch_pib_source(
    source: FeedSource, edition_date: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    status: dict[str, Any] = {
        "sourceId": source.id,
        "source": source.name,
        "status": "ok",
        "feedUrl": source.feed_url,
        **source_metadata(source),
        "fetched": 0,
        "accepted": 0,
        "skipped": 0,
        "duplicates": 0,
        "error": None,
    }

    # Step 1: Fetch Hindi RSS to get list of PRIDs
    # PIB's RSS endpoint requires a browser-like UA (rejects custom bot strings)
    request = urllib.request.Request(
        source.feed_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; newAgg/0.1)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as r:
            payload = r.read().decode("utf-8", errors="replace").lstrip("﻿")
        root = ET.fromstring(payload)
    except Exception as exc:
        status["status"] = "error"
        status["error"] = str(exc)
        return [], status

    items = root.findall("./channel/item")
    status["fetched"] = len(items)

    hindi_prids: list[int] = []
    for item in items:
        link = child_text(item, ["link"])
        m = re.search(r"PRID=(\d+)", link, re.IGNORECASE)
        if m:
            hindi_prids.append(int(m.group(1)))

    if not hindi_prids:
        return [], status

    # Step 2: Resolve each Hindi PRID → English content (parallel)
    accepted: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_pib_resolve_one, prid, edition_date): prid for prid in hindi_prids}
        for fut in concurrent.futures.as_completed(futures):
            result = fut.result()
            if result is None:
                status["skipped"] += 1
            else:
                accepted.append(result)

    status["accepted"] = len(accepted)
    return accepted, status


def child_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        node = element.find(name)
        if node is not None and node.text:
            return clean_text(node.text)

    for node in list(element):
        local_name = node.tag.rsplit("}", 1)[-1]
        if local_name in names and node.text:
            return clean_text(node.text)

    return ""


def child_link(element: ET.Element) -> str:
    rss_link = child_text(element, ["link"])
    if rss_link:
        return rss_link

    for node in list(element):
        local_name = node.tag.rsplit("}", 1)[-1]
        if local_name == "link":
            href = node.attrib.get("href")
            if href:
                return clean_text(href)
    return ""


def feed_entries(root: ET.Element) -> list[ET.Element]:
    rss_items = root.findall("./channel/item")
    if rss_items:
        return rss_items

    atom_entries = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "entry":
            atom_entries.append(node)
    return atom_entries


def parse_entry(
    source: FeedSource, entry: ET.Element, fallback_date: Optional[date] = None
) -> Optional[dict[str, Any]]:
    title = child_text(entry, ["title"])
    link = child_link(entry)
    published_raw = child_text(entry, ["pubDate", "published", "updated"])
    published = parse_date(published_raw)

    if published is None and fallback_date is not None:
        # Feed omits pubDate (e.g. Times of India). Treat items as belonging to
        # the edition date so they aren't silently dropped.
        published = datetime(
            fallback_date.year, fallback_date.month, fallback_date.day,
            6, 0, 0, tzinfo=IST,
        )

    if not title or not link or published is None:
        return None

    raw_desc = child_text(entry, ["description", "summary"])
    title_norm = normalize_title(title)
    desc_norm = normalize_title(raw_desc)
    # Discard description when it is blank or merely repeats the title
    excerpt = truncate_excerpt(raw_desc) if raw_desc and not desc_norm.startswith(title_norm[:50]) else ""

    clean_link = canonical_url(link)
    return {
        "id": slugify(f"{source.id}-{title}"),
        "sourceId": source.id,
        "source": source.name,
        "title": title,
        "excerpt": excerpt,
        "category": source.category,
        "priority": "Medium",
        "url": clean_link,
        "publishedAt": published.isoformat(timespec="seconds"),
        "_dedupeTitle": normalize_title(title),
        "_dedupeUrl": clean_link,
    }


def fetch_source(source: FeedSource, edition_date: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    status = {
        "sourceId": source.id,
        "source": source.name,
        "status": "ok",
        "feedUrl": source.feed_url,
        **source_metadata(source),
        "fetched": 0,
        "accepted": 0,
        "skipped": 0,
        "duplicates": 0,
        "error": None,
    }

    request = urllib.request.Request(
        source.feed_url,
        headers={
            "User-Agent": "newAgg-headline-fetcher/0.1 (+https://github.com/local/newAgg)"
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
        root = ET.fromstring(payload)
    except Exception as exc:
        status["status"] = "error"
        status["error"] = str(exc)
        return [], status

    accepted = []
    entries = feed_entries(root)
    status["fetched"] = len(entries)

    fallback = edition_date if source.allow_missing_date else None
    for entry in entries:
        item = parse_entry(source, entry, fallback_date=fallback)
        if item is None:
            status["skipped"] += 1
            continue

        published = datetime.fromisoformat(item["publishedAt"])
        if published.astimezone(IST).date() != edition_date:
            status["skipped"] += 1
            continue

        accepted.append(item)

    status["accepted"] = len(accepted)
    return accepted, status


MAX_PER_SOURCE = 15


def dedupe_headlines(
    headlines: list[dict[str, Any]], statuses: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    source_counts: dict[str, int] = {}
    deduped = []
    status_by_source = {status["sourceId"]: status for status in statuses}

    for item in sorted(headlines, key=lambda record: record["publishedAt"], reverse=True):
        source_status = status_by_source[item["sourceId"]]
        is_duplicate = item["_dedupeUrl"] in seen_urls or item["_dedupeTitle"] in seen_titles

        if is_duplicate:
            source_status["duplicates"] += 1
            continue

        sid = item["sourceId"]
        if source_counts.get(sid, 0) >= MAX_PER_SOURCE:
            status_by_source[sid]["skipped"] += 1
            continue

        seen_urls.add(item["_dedupeUrl"])
        seen_titles.add(item["_dedupeTitle"])
        source_counts[sid] = source_counts.get(sid, 0) + 1
        clean_item = {key: val for key, val in item.items() if not key.startswith("_")}
        deduped.append(clean_item)

    for index, item in enumerate(deduped):
        if index < 5:
            item["priority"] = "Lead"
        elif index < 12:
            item["priority"] = "High"
        else:
            item["priority"] = "Medium"

    return deduped


def build_payload(
    edition_date: date,
    headlines: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    configured_sources = [source for source in SOURCES if source.enabled]
    sources_succeeded = sum(1 for status in statuses if status["status"] == "ok")
    sources_failed = sum(1 for status in statuses if status["status"] != "ok")
    fetched = sum(status["fetched"] for status in statuses)
    skipped = sum(status["skipped"] for status in statuses)
    duplicates = sum(status["duplicates"] for status in statuses)
    errors = sum(1 for status in statuses if status["error"])

    final_headlines = headlines[:limit]
    fetch_status = {
        "status": "complete" if final_headlines else "empty",
        "sourcesConfigured": len(configured_sources),
        "sourcesSucceeded": sources_succeeded,
        "sourcesFailed": sources_failed,
        "fetched": fetched,
        "accepted": len(final_headlines),
        "skipped": skipped,
        "duplicates": duplicates,
        "errors": errors,
    }

    return {
        "generatedAt": datetime.now(IST).isoformat(timespec="seconds"),
        "editionDate": edition_date.isoformat(),
        "region": "India",
        "note": "Generated from public RSS feeds; verify source links before editorial use.",
        "fetchStatus": fetch_status,
        "sourceStatus": statuses,
        "sources": [
            {
                "id": source.id,
                "name": source.name,
                "url": source.site_url,
                "feedUrl": source.feed_url,
                **source_metadata(source),
            }
            for source in configured_sources
        ],
        "headlines": final_headlines,
    }


def write_payload(payload: dict[str, Any], output: Path, edition_dir: Path) -> Path:
    edition_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    edition_path = edition_dir / f"{payload['editionDate']}.json"
    json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    edition_path.write_text(json_payload + "\n", encoding="utf-8")
    output.write_text(f"window.__INDIA_HEADLINES__ = {json_payload};\n", encoding="utf-8")

    # Keep editions/index.json up to date so the UI can list available dates
    all_dates = sorted(
        [p.stem for p in edition_dir.glob("*.json") if p.stem != "index"],
        reverse=True,
    )
    index_path = edition_dir / "index.json"
    index_path.write_text(
        json.dumps({"editions": all_dates}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return edition_path


_ARTICLE_TEXT_MIN_CHARS = 80  # shorter than this is likely a paywall button or nav fragment


def enrich_with_article_text(
    headlines: list[dict[str, Any]], max_workers: int = 6
) -> list[dict[str, Any]]:
    """Fetch article text for each headline in parallel. Mutates in place.

    Skips headlines that already have articleText (e.g. PIB sets it during its
    own two-step PRID pipeline). Discards fetched text shorter than
    _ARTICLE_TEXT_MIN_CHARS to avoid storing paywall noise like "Expand".
    """
    def _fetch(headline: dict[str, Any]) -> None:
        if headline.get("articleText"):
            return  # already populated (PIB or prior run)
        text = fetch_article_text(headline["url"])
        if len(text) < _ARTICLE_TEXT_MIN_CHARS:
            return  # discard paywall fragments / nav noise
        headline["articleText"] = text
        if not headline.get("excerpt"):
            headline["excerpt"] = truncate_excerpt(text, 300)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(_fetch, headlines))

    return headlines


_FACT_RANK_RE = re.compile(
    r'\b(?:rank(?:ed)?|placed?|stood|slipped|jumped?|climbed?|rose)\s+'
    r'(?:at\s+|to\s+)?(?:the\s+)?(\d+)(?:st|nd|rd|th)\b',
    re.IGNORECASE,
)
_FACT_RANK_ORDINAL_RE = re.compile(
    r'\b(\d+)(?:st|nd|rd|th)\s+(?:rank|place|position|spot)\b',
    re.IGNORECASE,
)
_FACT_MONEY_RE = re.compile(
    r'(?:Rs\.?\s*|₹\s*|INR\s*)([\d,]+(?:\.\d+)?)\s*'
    r'(crore|lakh|thousand|million|billion)',
    re.IGNORECASE,
)
_FACT_ARTICLE_RE = re.compile(
    r'\bArticle\s+(\d+[A-Za-z]?(?:\(\d+[A-Za-z]?\))?)\b',
)
_FACT_SCHEDULE_RE = re.compile(
    r'\bSchedule\s+(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I|\d+)\b',
    re.IGNORECASE,
)
_FACT_AMENDMENT_RE = re.compile(
    r'\b(\d+)(?:st|nd|rd|th)\s+(?:Constitutional\s+)?Amendment\b',
    re.IGNORECASE,
)
_FACT_PERCENT_RE = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(?:per\s*cent|%)',
    re.IGNORECASE,
)
_FACT_APPT_RE = re.compile(
    r'\bappointed\b[^.;]{0,50}?\b'
    r'(chairman|chairperson|director(?:\s+general)?|minister|secretary(?:\s+general)?|'
    r'commissioner|governor|ambassador|chief|president|ceo|cmd|dgp|cag|cji|chair)\b',
    re.IGNORECASE,
)


def _ordinal_suffix(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def extract_facts(headline: dict[str, Any]) -> list[dict[str, str]]:
    parts = [
        headline.get("title", ""),
        headline.get("excerpt", ""),
        (headline.get("articleText") or "")[:500],
    ]
    text = " ".join(p for p in parts if p)

    facts: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(type_: str, label: str) -> None:
        key = f"{type_}:{label}"
        if key not in seen and len(facts) < 3:
            seen.add(key)
            facts.append({"type": type_, "text": label})

    for m in _FACT_RANK_RE.finditer(text):
        n = int(m.group(1))
        add("rank", f"Ranked {n}{_ordinal_suffix(n)}")
    for m in _FACT_RANK_ORDINAL_RE.finditer(text):
        n = int(m.group(1))
        add("rank", f"Ranked {n}{_ordinal_suffix(n)}")

    for m in _FACT_MONEY_RE.finditer(text):
        add("money", f"₹{m.group(1)} {m.group(2).title()}")

    for m in _FACT_ARTICLE_RE.finditer(text):
        add("constitution", f"Article {m.group(1)}")
    for m in _FACT_SCHEDULE_RE.finditer(text):
        add("constitution", f"Schedule {m.group(1).upper()}")
    for m in _FACT_AMENDMENT_RE.finditer(text):
        n = int(m.group(1))
        add("constitution", f"{n}{_ordinal_suffix(n)} Amendment")

    for m in _FACT_PERCENT_RE.finditer(text):
        add("stat", f"{m.group(1)}%")

    for m in _FACT_APPT_RE.finditer(text):
        role = m.group(1).title()
        add("appointment", f"Appointment: {role}")

    return facts


# --- LLM Enrichment ---

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ENRICH_MODEL = "claude-haiku-4-5-20251001"
ENRICH_BATCH_SIZE = 10

_ENRICH_PROMPT_PREFIX = """\
You are a UPSC (Union Public Service Commission) civil services exam assistant for Indian students.

Analyse each headline and return enrichment data for exam preparation.

For each headline provide:
- topic: UPSC subject path using this taxonomy:
    Polity > Constitutional Bodies | Polity > Parliament & Legislation | Polity > Federalism |
    Polity > Elections & Governance | Polity > Judiciary |
    Economy > Monetary Policy | Economy > Fiscal Policy | Economy > Banking & Finance |
    Economy > Trade & External Sector | Economy > Agriculture & Food Security |
    Economy > Industry & Manufacturing | Economy > Infrastructure |
    International Relations > Bilateral Relations | International Relations > Multilateral Forums |
    International Relations > Security & Defence |
    Environment > Climate Change | Environment > Biodiversity | Environment > Pollution & Waste |
    Science & Technology > Space | Science & Technology > Defence Technology |
    Science & Technology > Health & Biotech | Science & Technology > Digital & AI |
    Social Issues > Health | Social Issues > Education |
    Social Issues > Women & Children | Social Issues > Tribal & Marginalized |
    Security > Internal Security | Security > Border Issues |
    History & Culture > Art & Culture | Disaster Management |
    Current Events > State Politics | Current Events > Crime & Courts
- upscRelevance: "High" (core syllabus, frequently tested), "Medium" (useful context), or "Low" (general awareness only)
- examAngle: Key exam angles in one concise line (e.g. "Prelims: Article 148, CAG powers. Mains GS2: parliamentary oversight.")
- whyItMatters: 1-2 sentences explaining the UPSC significance
- storyPhase: the arc of this story — exactly one of: "escalating" (situation intensifying or worsening), "developing" (actively unfolding, more updates expected), "resolving" (moving toward a conclusion or solution), "resolved" (concluded, outcome is known)
- storyUpdate: if previousTitles is provided, write one concise line (under 15 words) capturing what is new today compared to the earlier coverage. If no previousTitles, return empty string "".
- lensA: a single plain English word a common person understands (e.g. "Progress", "Help", "Win", "Needed"). Neutral framing of a genuine trade-off — not partisan, no policy jargon.
- lensB: a single plain English word that directly contrasts lensA (e.g. "Problem", "Harm", "Gamble", "Forced"). Must be immediately understood without explanation.

Respond with ONLY a JSON array — no markdown, no code fences, no explanation:
[{"id":"...","topic":"...","upscRelevance":"...","examAngle":"...","whyItMatters":"...","storyPhase":"...","storyUpdate":"...","lensA":"...","lensB":"..."}, ...]

Headlines:
"""


def _enrich_batch(batch: list[dict[str, Any]], api_key: str) -> None:
    to_enrich = [h for h in batch if not h.get("enrichment")]
    if not to_enrich:
        return

    items = []
    for h in to_enrich:
        item: dict[str, Any] = {
            "id": h["id"],
            "title": h["title"],
            "excerpt": h.get("excerpt") or "",
            "text": (h.get("articleText") or "")[:400],
        }
        if h.get("storyEditions"):
            item["previousTitles"] = [e["title"] for e in h["storyEditions"]]
        items.append(item)

    prompt = _ENRICH_PROMPT_PREFIX + json.dumps(items, ensure_ascii=False)

    payload = json.dumps({
        "model": ENRICH_MODEL,
        "max_tokens": 3072,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        _ANTHROPIC_API_URL,
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            response_body = json.loads(resp.read())
    except Exception as exc:
        print(f"warning: Claude API call failed: {exc}", file=sys.stderr)
        return

    try:
        text = response_body["content"][0]["text"].strip()
        if not text.startswith("["):
            m = re.search(r"\[.+\]", text, re.DOTALL)
            if m:
                text = m.group(0)
        enrichments = json.loads(text)
    except Exception as exc:
        print(f"warning: failed to parse enrichment response: {exc}", file=sys.stderr)
        return

    enrichment_by_id = {
        e["id"]: e for e in enrichments if isinstance(e, dict) and "id" in e
    }

    for h in to_enrich:
        e = enrichment_by_id.get(h["id"])
        if e:
            h["enrichment"] = {
                "topic": str(e.get("topic", "")),
                "upscRelevance": str(e.get("upscRelevance", "")),
                "examAngle": str(e.get("examAngle", "")),
                "whyItMatters": str(e.get("whyItMatters", "")),
                "storyPhase": str(e.get("storyPhase", "developing")),
                "storyUpdate": str(e.get("storyUpdate", "")),
                "lensA": str(e.get("lensA", "")),
                "lensB": str(e.get("lensB", "")),
            }


_OLLAMA_API_URL = "http://localhost:11434/api/chat"
ENRICH_LOCAL_DEFAULT_MODEL = "qwen2.5:7b"
ENRICH_LOCAL_BATCH_SIZE = 5  # smaller batches — local models are slower

_ENRICH_LOCAL_PROMPT_PREFIX = """\
You are a UPSC (Union Public Service Commission) exam assistant for Indian civil services students.

Classify each headline and return a JSON object with an 'enrichments' array.

Each enrichment must have:
- id: same as input
- topic: "Area > Subtopic" from this list:
    Polity > Constitutional Bodies | Polity > Parliament & Legislation | Polity > Federalism |
    Polity > Elections & Governance | Polity > Judiciary |
    Economy > Monetary Policy | Economy > Fiscal Policy | Economy > Banking & Finance |
    Economy > Trade & External Sector | Economy > Agriculture & Food Security |
    Economy > Industry & Manufacturing | Economy > Infrastructure |
    International Relations > Bilateral Relations | International Relations > Multilateral Forums |
    International Relations > Security & Defence |
    Environment > Climate Change | Environment > Biodiversity | Environment > Pollution & Waste |
    Science & Technology > Space | Science & Technology > Defence Technology |
    Science & Technology > Health & Biotech | Science & Technology > Digital & AI |
    Social Issues > Health | Social Issues > Education | Social Issues > Women & Children |
    Security > Internal Security | Security > Border Issues |
    Current Events > State Politics | Current Events > Crime & Courts
- upscRelevance: exactly "High", "Medium", or "Low"
- examAngle: one line (e.g. "Prelims: Article 32, writ jurisdiction. Mains GS2: judicial review.")
- whyItMatters: 1-2 sentences for a UPSC aspirant
- storyPhase: the arc of this story — exactly one of: "escalating" (intensifying/worsening), "developing" (unfolding, more updates expected), "resolving" (moving toward conclusion), "resolved" (concluded, outcome known)
- storyUpdate: if previousTitles is provided, write one concise line (under 15 words) on what is new today vs. earlier coverage. Otherwise return "".
- lensA: a single plain English word a common person understands. Neutral, no jargon.
- lensB: a single plain English word that directly contrasts lensA. Must be immediately understood.

Example response format:
{"enrichments": [{"id": "abc", "topic": "Polity > Judiciary", "upscRelevance": "High", "examAngle": "Prelims: Article 32. Mains GS2: judicial review.", "whyItMatters": "Landmark ruling on writs affects GS2 preparation.", "storyPhase": "developing", "storyUpdate": "Supreme Court issues stay on lower court order.", "lensA": "Judicial independence", "lensB": "Executive overreach"}]}

Headlines to classify:
"""


def _check_ollama_running() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _enrich_batch_local(batch: list[dict[str, Any]], model: str) -> None:
    to_enrich = [h for h in batch if not h.get("enrichment")]
    if not to_enrich:
        return

    items = []
    for h in to_enrich:
        item: dict[str, Any] = {
            "id": h["id"],
            "title": h["title"],
            "excerpt": h.get("excerpt") or "",
        }
        if h.get("storyEditions"):
            item["previousTitles"] = [e["title"] for e in h["storyEditions"]]
        items.append(item)

    prompt = _ENRICH_LOCAL_PROMPT_PREFIX + json.dumps(items, ensure_ascii=False)

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        _OLLAMA_API_URL,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            response_body = json.loads(resp.read())
    except Exception as exc:
        print(f"warning: Ollama call failed: {exc}", file=sys.stderr)
        return

    try:
        text = response_body["message"]["content"].strip()
        parsed = json.loads(text)
        enrichments = parsed.get("enrichments", parsed) if isinstance(parsed, dict) else parsed
        if not isinstance(enrichments, list):
            raise ValueError("expected list")
    except Exception as exc:
        print(f"warning: failed to parse Ollama enrichment response: {exc}", file=sys.stderr)
        return

    enrichment_by_id = {
        e["id"]: e for e in enrichments if isinstance(e, dict) and "id" in e
    }

    for h in to_enrich:
        e = enrichment_by_id.get(h["id"])
        if e:
            h["enrichment"] = {
                "topic": str(e.get("topic", "")),
                "upscRelevance": str(e.get("upscRelevance", "")),
                "examAngle": str(e.get("examAngle", "")),
                "whyItMatters": str(e.get("whyItMatters", "")),
                "storyPhase": str(e.get("storyPhase", "developing")),
                "storyUpdate": str(e.get("storyUpdate", "")),
                "lensA": str(e.get("lensA", "")),
                "lensB": str(e.get("lensB", "")),
            }


def enrich_headlines_local(headlines: list[dict[str, Any]], model: str) -> None:
    batches = [
        headlines[i: i + ENRICH_LOCAL_BATCH_SIZE]
        for i in range(0, len(headlines), ENRICH_LOCAL_BATCH_SIZE)
    ]
    total = len(batches)
    for i, batch in enumerate(batches, 1):
        print(f"  batch {i}/{total}…", file=sys.stderr, end="\r")
        _enrich_batch_local(batch, model)
    print(file=sys.stderr)  # newline after progress


def mock_enrich_headlines(headlines: list[dict[str, Any]]) -> None:
    """Fill mock enrichment for UI testing — no API calls, no cost."""
    _TOPIC_BY_CATEGORY: dict[str, str] = {
        "India": "Polity > Governance",
        "Business": "Economy > Industry & Manufacturing",
        "Government": "Polity > Parliament & Legislation",
        "World": "International Relations > Bilateral Relations",
        "Technology": "Science & Technology > Digital & AI",
        "Science": "Science & Technology > Health & Biotech",
        "Environment": "Environment > Climate Change",
        "Sports": "Current Events > State Politics",
    }
    _EXAM_ANGLE_BY_TOPIC: dict[str, str] = {
        "Polity": "Prelims: constitutional provisions, key articles. Mains GS2: governance, accountability mechanisms.",
        "Economy": "Prelims: key terms and data. Mains GS3: economic implications, policy impact.",
        "International Relations": "Prelims: agreements, organisations. Mains GS2: India's foreign policy, bilateral significance.",
        "Environment": "Prelims: conventions, reports, species. Mains GS3: environmental governance, climate commitments.",
        "Science & Technology": "Prelims: missions, discoveries. Mains GS3: applications, India's capabilities.",
        "Social Issues": "Prelims: schemes, data. Mains GS1/GS2: social justice, welfare policy.",
        "Security": "Prelims: forces, legislation. Mains GS3: internal security, border management.",
        "Current Events": "General awareness — useful for interview and Essay paper.",
    }
    _RELEVANCE: dict[str, str] = {"Lead": "High", "High": "High", "Medium": "Medium"}

    for h in headlines:
        if h.get("enrichment"):
            continue
        cat = h.get("category", "")
        topic = _TOPIC_BY_CATEGORY.get(cat, "Current Events > State Politics")
        gs_area = topic.split(" > ")[0]
        subtopic = topic.split(" > ")[1] if " > " in topic else topic
        exam_angle = _EXAM_ANGLE_BY_TOPIC.get(gs_area, "General awareness — relevant to current affairs.")
        relevance = _RELEVANCE.get(h.get("priority", ""), "Medium")
        _LENS_MOCK: dict[str, tuple[str, str]] = {
            "Polity": ("Progress", "Problem"),
            "Economy": ("Opportunity", "Risk"),
            "International Relations": ("Win", "Gamble"),
            "Environment": ("Needed", "Costly"),
            "Science & Technology": ("Breakthrough", "Concern"),
            "Social Issues": ("Help", "Harm"),
            "Security": ("Safety", "Overreach"),
            "History & Culture": ("Preserve", "Resist"),
            "Current Events": ("Fix", "Flaw"),
            "Disaster Management": ("Prepared", "Delayed"),
        }
        lens_pair = _LENS_MOCK.get(gs_area, ("Opportunity", "Risk"))
        _PHASE_BY_PRIORITY = {"Lead": "escalating", "High": "developing"}
        phase = _PHASE_BY_PRIORITY.get(h.get("priority", ""), "developing")
        editions = h.get("storyEditions") or []
        if editions:
            first_title = editions[0].get("title", "")[:60]
            story_update = f"Follow-up: situation updated since “{first_title}…”"
        else:
            story_update = ""
        h["enrichment"] = {
            "topic": topic,
            "upscRelevance": relevance,
            "examAngle": exam_angle,
            "whyItMatters": (
                f"This development relates to {subtopic.lower()} under {gs_area} — "
                "a recurring theme in UPSC Prelims and Mains. "
                "Track the policy/legal dimensions for exam preparation."
            ),
            "storyPhase": phase,
            "storyUpdate": story_update,
            "lensA": lens_pair[0],
            "lensB": lens_pair[1],
        }


def enrich_headlines(
    headlines: list[dict[str, Any]], api_key: str, max_workers: int = 4
) -> None:
    batches = [
        headlines[i: i + ENRICH_BATCH_SIZE]
        for i in range(0, len(headlines), ENRICH_BATCH_SIZE)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(lambda b: _enrich_batch(b, api_key), batches))


STORY_LOOKBACK_DAYS = 7
MAX_ACTIVE_THREADS = 20   # platform cap: at most this many stories threaded simultaneously
THREAD_QUIET_DAYS  = 4   # days without a new edition before a thread is marked closed


def load_thread_registry(edition_dir: Path) -> dict[str, Any]:
    """Load the platform thread registry. Returns empty registry if not found."""
    path = edition_dir / "thread_registry.json"
    if not path.exists():
        return {"version": 1, "threads": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return {"version": 1, "threads": {}}


def save_thread_registry(registry: dict[str, Any], edition_dir: Path) -> None:
    path = edition_dir / "thread_registry.json"
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")


def expire_threads(registry: dict[str, Any], edition_date: date) -> int:
    """Mark threads quiet for THREAD_QUIET_DAYS+ as closed. Returns count expired."""
    cutoff = (edition_date - timedelta(days=THREAD_QUIET_DAYS)).isoformat()
    expired = 0
    for thread in registry.get("threads", {}).values():
        if thread["status"] == "active" and thread["lastEditionDate"] < cutoff:
            thread["status"] = "closed"
            expired += 1
    return expired


def update_registry_from_headlines(
    registry: dict[str, Any],
    headlines: list[dict[str, Any]],
    edition_date: date,
) -> None:
    """After threading: add new threads to registry and refresh lastEditionDate for continuing ones."""
    threads = registry.setdefault("threads", {})
    for h in headlines:
        story_id = h.get("storyId")
        if not story_id:
            continue
        if story_id in threads:
            threads[story_id]["lastEditionDate"] = edition_date.isoformat()
            threads[story_id]["dayCount"] = h.get("storyDayCount", 1)
            threads[story_id]["status"] = "active"
        else:
            threads[story_id] = {
                "storyId": story_id,
                "title": h.get("title", ""),
                "firstEditionDate": edition_date.isoformat(),
                "lastEditionDate": edition_date.isoformat(),
                "dayCount": 1,
                "status": "active",
            }


def propagate_storyid_within_clusters(headlines: list[dict[str, Any]]) -> int:
    """Spread storyId from any cluster member that has one to the entire cluster.

    thread_stories() matches headlines individually by keyword overlap, which can
    miss cluster members whose title wording diverges (e.g. 'LIVE:' prefixes,
    spelling variants).  After threading, if any member of a cluster has a
    storyId, all other members in that cluster should share it.
    Uses the member with the highest storyDayCount as the source of truth.
    """
    # Build clusterId → best (storyId, editions, dayCount) from members that matched
    best: dict[str, tuple[str, list, int]] = {}
    for h in headlines:
        cid = h.get("clusterId")
        sid = h.get("storyId")
        if not cid or not sid:
            continue
        day_count = h.get("storyDayCount", 1)
        if cid not in best or day_count > best[cid][2]:
            best[cid] = (sid, h.get("storyEditions", []), day_count)

    filled = 0
    for h in headlines:
        cid = h.get("clusterId")
        if cid and not h.get("storyId") and cid in best:
            sid, editions, day_count = best[cid]
            h["storyId"] = sid
            h["storyEditions"] = editions
            h["storyDayCount"] = day_count
            filled += 1
    return filled


def carry_forward_enrichment(
    headlines: list[dict[str, Any]],
    past_editions: list[tuple[str, list[dict[str, Any]]]],
) -> int:
    """Copy enrichment from past editions for headlines that share the same storyId.

    Iterates past editions most-recent-first so the freshest enrichment wins.
    Only fills headlines that have no enrichment yet.  Returns the count carried.
    """
    story_enrichment: dict[str, dict[str, Any]] = {}
    for _date_str, past_headlines in reversed(past_editions):  # most recent first
        for h in past_headlines:
            sid = h.get("storyId")
            enrich = h.get("enrichment")
            if sid and enrich and sid not in story_enrichment:
                story_enrichment[sid] = enrich

    carried = 0
    for h in headlines:
        if h.get("enrichment"):
            continue
        sid = h.get("storyId")
        if sid and sid in story_enrichment:
            h["enrichment"] = story_enrichment[sid]
            carried += 1
    return carried


def load_past_editions(
    edition_dir: Path, edition_date: date, lookback_days: int = STORY_LOOKBACK_DAYS
) -> list[tuple[str, list[dict[str, Any]]]]:
    """Return [(date_str, headlines), ...] for up to lookback_days past editions, oldest-first."""
    results = []
    for days_back in range(lookback_days, 0, -1):
        past_date = edition_date - timedelta(days=days_back)
        path = edition_dir / f"{past_date.isoformat()}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append((past_date.isoformat(), data.get("headlines", [])))
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def thread_stories(
    today_headlines: list[dict[str, Any]],
    past_editions: list[tuple[str, list[dict[str, Any]]]],
    known_thread_ids: set[str] | None = None,
    active_thread_count: int = 0,
) -> None:
    """Match today's headlines to past editions by keyword overlap. Mutates in place.

    known_thread_ids: storyIds the platform has ever tracked (from registry).
                      Continuations of these are always allowed.
    active_thread_count: current number of active threads.
                         Brand-new threads are blocked once this hits MAX_ACTIVE_THREADS.
    """
    if not past_editions:
        return

    known = known_thread_ids or set()
    new_threads_added = 0   # tracks brand-new threads created this run

    # Flatten past headlines: (date_str, headline, word_set)
    past_items: list[tuple[str, dict[str, Any], frozenset[str]]] = []
    for date_str, headlines in past_editions:
        for h in headlines:
            ws = significant_words(h.get("title", ""))
            if ws:
                past_items.append((date_str, h, ws))

    if not past_items:
        return

    today_word_sets = [significant_words(h.get("title", "")) for h in today_headlines]

    for i, h in enumerate(today_headlines):
        ws_today = today_word_sets[i]
        if not ws_today:
            continue

        # Find matching past headlines, keyed by date (best match per day)
        by_date: dict[str, tuple[dict[str, Any], int]] = {}
        for date_str, past_h, ws_past in past_items:
            shared = ws_today & ws_past
            if len(shared) < CLUSTER_MIN_SHARED:
                continue
            union_size = len(ws_today | ws_past)
            if not union_size or len(shared) / union_size < CLUSTER_JACCARD:
                continue
            existing = by_date.get(date_str)
            if existing is None or len(shared) > existing[1]:
                by_date[date_str] = (past_h, len(shared))

        if not by_date:
            continue

        sorted_dates = sorted(by_date.keys())
        story_editions = [
            {
                "date": d,
                "title": by_date[d][0].get("title", ""),
                "url": by_date[d][0].get("url", ""),
            }
            for d in sorted_dates
        ]

        earliest = by_date[sorted_dates[0]][0]
        story_id = (earliest.get("id") or slugify(earliest.get("title", "")))[:50]

        is_known = story_id in known
        at_cap = (active_thread_count + new_threads_added) >= MAX_ACTIVE_THREADS

        # Continuations of known threads always allowed.
        # Brand-new threads blocked when platform is at capacity.
        if not is_known and at_cap:
            continue

        if not is_known:
            new_threads_added += 1

        h["storyId"] = story_id
        h["storyEditions"] = story_editions
        h["storyDayCount"] = len(story_editions) + 1


def collect(
    edition_date: date, extract_text: bool = False
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_headlines = []
    statuses = []

    for source in SOURCES:
        if not source.enabled:
            continue
        if source.source_type == "pib":
            source_headlines, status = fetch_pib_source(source, edition_date)
        else:
            source_headlines, status = fetch_source(source, edition_date)
        all_headlines.extend(source_headlines)
        statuses.append(status)

    deduped = dedupe_headlines(all_headlines, statuses)
    clustered = cluster_headlines(deduped)

    if extract_text:
        print(f"fetching article text for {len(clustered)} headlines…", file=sys.stderr)
        enrich_with_article_text(clustered)

    for h in clustered:
        h["facts"] = extract_facts(h)

    return clustered, statuses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="assets/data/india-headlines.js",
        help="Path to write the browser-loadable JS data file.",
    )
    parser.add_argument(
        "--edition-dir",
        default="assets/data/editions",
        help="Directory for JSON edition artifacts.",
    )
    parser.add_argument("--date", help="Edition date in YYYY-MM-DD format. Defaults to today IST.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--min-headlines", type=int, default=20)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Write artifacts even if collected headlines are below --min-headlines.",
    )
    parser.add_argument(
        "--extract-text",
        action="store_true",
        help="Fetch and extract article body text for each headline. Slower (parallel HTTP). Adds 'articleText' field to each headline.",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send a macOS desktop notification on completion (requires osascript; silently skipped on other platforms).",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help=(
            "Enrich headlines with UPSC metadata (topic, examAngle, upscRelevance, whyItMatters) "
            "via Claude API. Requires ANTHROPIC_API_KEY env var. "
            "Skips headlines that already have enrichment data (safe to re-run)."
        ),
    )
    parser.add_argument(
        "--enrich-mock",
        action="store_true",
        help="Fill mock enrichment data for UI testing — no API key required, no cost.",
    )
    parser.add_argument(
        "--enrich-local",
        action="store_true",
        help=(
            "Enrich headlines using a locally running Ollama model. "
            "Requires Ollama running at http://localhost:11434. "
            "No API key or cost. Use --local-model to specify the model."
        ),
    )
    parser.add_argument(
        "--local-model",
        default=ENRICH_LOCAL_DEFAULT_MODEL,
        metavar="MODEL",
        help=f"Ollama model name for --enrich-local. Default: {ENRICH_LOCAL_DEFAULT_MODEL}",
    )
    args = parser.parse_args()

    try:
        edition_date = parse_edition_date(args.date)
    except ValueError:
        print("error: --date must use YYYY-MM-DD", file=sys.stderr)
        return 2

    headlines, statuses = collect(edition_date, extract_text=args.extract_text)

    # Thread before enrichment so the LLM receives previousTitles context
    edition_dir_path = Path(args.edition_dir)
    past_editions = load_past_editions(edition_dir_path, edition_date)

    registry = load_thread_registry(edition_dir_path)
    expired_count = expire_threads(registry, edition_date)
    known_ids = set(registry.get("threads", {}).keys())
    active_count = sum(1 for t in registry.get("threads", {}).values() if t["status"] == "active")

    thread_stories(headlines, past_editions, known_ids, active_count)

    # Spread storyId to all cluster members when only some matched via keywords.
    cluster_filled = propagate_storyid_within_clusters(headlines)
    if cluster_filled:
        print(f"cluster propagation: {cluster_filled} headline(s) inherited storyId from cluster sibling.", file=sys.stderr)

    update_registry_from_headlines(registry, headlines, edition_date)
    save_thread_registry(registry, edition_dir_path)

    threaded = sum(1 for h in headlines if h.get("storyId"))
    new_active = sum(1 for t in registry.get("threads", {}).values() if t["status"] == "active")
    if expired_count:
        print(f"thread registry: {expired_count} thread(s) closed (quiet ≥{THREAD_QUIET_DAYS} days).", file=sys.stderr)
    print(f"thread registry: {new_active}/{MAX_ACTIVE_THREADS} active threads.", file=sys.stderr)

    # Phase 1: write baseline immediately so the UI is never stale while enrichment runs.
    baseline_payload = build_payload(edition_date, headlines, statuses, args.limit)
    write_payload(baseline_payload, Path(args.output), Path(args.edition_dir))

    # Carry forward enrichment from past editions for continuing story threads.
    # This runs before any API call so threaded stories reuse previous enrichment
    # (including lensA/lensB) even when today's enrichment fails.
    carried = carry_forward_enrichment(headlines, past_editions)
    if carried:
        print(f"enrichment carry-forward: {carried} headline(s) reused from past editions.", file=sys.stderr)

    if args.enrich_mock:
        mock_enrich_headlines(headlines)
        print(f"mock enrichment applied to {len(headlines)} headlines (UI test mode).", file=sys.stderr)
    elif args.enrich_local:
        if not _check_ollama_running():
            print(
                "error: Ollama is not running. Start it with: ollama serve\n"
                "       Then pull a model: ollama pull qwen2.5:7b",
                file=sys.stderr,
            )
        else:
            to_enrich = sum(1 for h in headlines if not h.get("enrichment"))
            print(
                f"enriching {to_enrich} headlines via Ollama ({args.local_model})…",
                file=sys.stderr,
            )
            enrich_headlines_local(headlines, args.local_model)
            enriched = sum(1 for h in headlines if h.get("enrichment"))
            print(f"enriched {enriched}/{len(headlines)} headlines.", file=sys.stderr)
    elif args.enrich:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("warning: --enrich requires ANTHROPIC_API_KEY env var; skipping.", file=sys.stderr)
        else:
            to_enrich = sum(1 for h in headlines if not h.get("enrichment"))
            print(f"enriching {to_enrich} headlines via Claude API ({ENRICH_MODEL})…", file=sys.stderr)
            enrich_headlines(headlines, api_key)
            enriched = sum(1 for h in headlines if h.get("enrichment"))
            print(f"enriched {enriched}/{len(headlines)} headlines.", file=sys.stderr)
    if threaded:
        print(f"threaded {threaded} headlines across {len(past_editions)} past edition(s).", file=sys.stderr)

    payload = build_payload(edition_date, headlines, statuses, args.limit)
    edition_path = write_payload(payload, Path(args.output), Path(args.edition_dir))

    failed_sources = [s for s in statuses if s["status"] != "ok"]
    for status in failed_sources:
        print(f"warning: failed to fetch {status['source']}: {status['error']}", file=sys.stderr)

    if len(failed_sources) > 3:
        print(
            f"alert: {len(failed_sources)} sources failed simultaneously — "
            "edition may be significantly incomplete. Check network and feed URLs.",
            file=sys.stderr,
        )

    accepted = payload["fetchStatus"]["accepted"]

    if accepted < 10:
        print(
            f"warning: very low headline count ({accepted}) — "
            "edition may be nearly empty. Check source health.",
            file=sys.stderr,
        )

    if accepted < args.min_headlines and not args.allow_partial:
        print(
            f"error: collected {accepted} headlines, below minimum {args.min_headlines}. "
            "Use --allow-partial for development or low-volume days.",
            file=sys.stderr,
        )
        print(f"wrote partial artifacts to {args.output} and {edition_path}")
        return 1

    print(f"wrote {accepted} headlines to {args.output}")
    print(f"wrote edition artifact to {edition_path}")

    if args.notify:
        if len(failed_sources) > 3:
            _send_macos_notification(
                title="newAgg — degraded edition",
                message=f"{accepted} headlines · {len(failed_sources)} sources failed",
            )
        else:
            _send_macos_notification(
                title="newAgg — edition ready",
                message=f"{accepted} headlines · {edition_date.isoformat()}",
            )

    return 0


def _send_macos_notification(title: str, message: str) -> None:
    if sys.platform != "darwin":
        return
    script = (
        f'display notification "{message}" with title "{title}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            timeout=5,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
