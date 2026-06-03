#!/usr/bin/env python3
"""Generate daily UPSC brief from a Velugo edition and post to Telegram.

Reads the latest (or specified) edition JSON, writes a Markdown brief to
assets/data/briefs/YYYY-MM-DD.md, and optionally posts to a Telegram channel.

Usage:
    python3 scripts/post_telegram.py                    # generate + post
    python3 scripts/post_telegram.py --dry-run          # preview only, no save/post
    python3 scripts/post_telegram.py --save-only        # write .md, skip Telegram
    python3 scripts/post_telegram.py --date 2026-06-01  # specific edition

Environment (not needed for --dry-run or --save-only):
    TELEGRAM_BOT_TOKEN   Bot token from @BotFather
    TELEGRAM_CHANNEL_ID  @channelname or numeric chat ID
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

EDITIONS_DIR = Path("assets/data/editions")
BRIEFS_DIR = Path("assets/data/briefs")
TELEGRAM_API = "https://api.telegram.org"
TELEGRAM_MAX_CHARS = 4096

TOP_MUST_KNOW = 7
TOP_FACTS = 8
TOP_ONGOING = 5

# Compact GS tagging rules — used when enrichment data is absent
_GS_RULES: list[tuple[str, list[str], list[str]]] = [
    ("GS2", ["Polity", "Governance"], [
        "court", "supreme court", "high court", "parliament", "lok sabha", "rajya sabha",
        "bill", "constitution", "constitutional", "amendment", "ordinance", "governor",
        "chief minister", "minister", "ministry", "cabinet", "president", "prime minister",
        "election", "electoral", "bypolls", "cag", "cbi", "enforcement directorate",
        "lokpal", "tribunal", "verdict", "judgment", "rti", "mla", "panchayat",
    ]),
    ("GS2", ["International Relations"], [
        "diplomacy", "china", "pakistan", "treaty", "united nations", "nato", "quad",
        "sco", "brics", "asean", "g20", "g7", "foreign minister", "external affairs",
        "foreign policy", "bilateral", "multilateral", "indo-pacific", "geopolitical",
        "fta", "ceasefire", "humanitarian", "strategic partnership",
    ]),
    ("GS3", ["Economy"], [
        "rbi", "inflation", "gdp", "trade", "exports", "imports", "budget", "tax",
        "economy", "bank", "banking", "repo rate", "monetary policy", "fiscal", "revenue",
        "fdi", "investment", "sebi", "manufacturing", "infrastructure", "msme", "tariff",
        "startup", "logistics", "port", "railway", "niti aayog", "economic survey",
    ]),
    ("GS3", ["Environment"], [
        "climate", "pollution", "forest", "wildlife", "renewable", "solar", "carbon",
        "emission", "biodiversity", "flood", "drought", "cyclone", "national park",
        "net zero", "paris agreement", "air quality", "aqi", "wetland", "coral",
        "ocean", "marine", "plastic", "waste", "ndrf", "ecology", "ecosystem",
    ]),
    ("GS3", ["Internal Security"], [
        "terrorism", "insurgency", "cybercrime", "naxal", "maoist", "militant",
        "terror", "terrorist", "encounter", "nia", "crpf", "bsf", "narcotics",
        "money laundering", "infiltration", "separatist",
    ]),
    ("GS3", ["Science & Technology"], [
        "space", "satellite", "semiconductor", "biotechnology", "isro", "chandrayaan",
        "gaganyaan", "artificial intelligence", "5g", "quantum", "gene editing",
        "nuclear", "drone", "cybersecurity", "digital india", "patent",
    ]),
    ("GS1/GS2", ["Society", "Social Justice"], [
        "labour", "caste", "women", "education", "health", "poverty", "dalit",
        "tribal", "adivasi", "obc", "reservation", "backward class", "minority",
        "gender", "domestic violence", "child labour", "maternal health",
        "malnutrition", "sanitation", "disability", "welfare", "human rights",
    ]),
    ("GS1", ["History & Culture"], [
        "heritage", "archaeological", "museum", "monument", "world heritage",
        "unesco", "excavation", "ancient", "medieval", "freedom fighter",
        "classical dance", "classical music", "folk art", "civilization",
    ]),
]

_FACT_EMOJI = {
    "constitution": "📋",
    "appointment": "👤",
    "money": "💰",
    "stat": "📈",
    "rank": "🏆",
}


def _kw_match(kw: str, text: str) -> bool:
    return bool(re.search(r"\b" + re.escape(kw) + r"\b", text))


def _tag(title: str) -> tuple[str, list[str]]:
    low = title.lower()
    for gs, tags, kws in _GS_RULES:
        if any(_kw_match(k, low) for k in kws):
            return gs, tags
    return "", []


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _trunc(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _fmt_date(date_str: str) -> str:
    try:
        d = date.fromisoformat(date_str)
        return d.strftime("%-d %b %Y")
    except ValueError:
        return date_str


# ── Brief selectors ────────────────────────────────────────────────────────────

def _must_know(headlines: list[dict], n: int = TOP_MUST_KNOW) -> list[dict]:
    def score(h: dict) -> int:
        rel = (h.get("enrichment") or {}).get("upscRelevance", "")
        if rel == "High":
            return 3
        if h.get("priority") == "High":
            return 2
        if rel == "Medium" or h.get("priority") == "Medium":
            return 1
        return 0

    worthy = [h for h in headlines if score(h) > 0]
    return sorted(worthy, key=score, reverse=True)[:n]


def _ongoing(headlines: list[dict], n: int = TOP_ONGOING) -> list[dict]:
    threaded = [h for h in headlines if (h.get("storyDayCount") or 0) > 1]
    return sorted(threaded, key=lambda h: h.get("storyDayCount", 0), reverse=True)[:n]


def _key_facts(headlines: list[dict], n: int = TOP_FACTS) -> list[tuple[dict, dict]]:
    """Return up to n (fact, headline) pairs, prioritised by fact type."""
    TYPE_ORDER = ["constitution", "appointment", "money", "stat", "rank"]
    seen: set[str] = set()
    by_type: dict[str, list[tuple[dict, dict]]] = {t: [] for t in TYPE_ORDER}
    for h in headlines:
        for f in h.get("facts") or []:
            key = f"{f['type']}:{f['text']}"
            if key not in seen:
                seen.add(key)
                bucket = by_type.setdefault(f["type"], [])
                bucket.append((f, h))
    ordered: list[tuple[dict, dict]] = []
    for t in TYPE_ORDER:
        ordered.extend(by_type.get(t, []))
    for t, items in by_type.items():
        if t not in TYPE_ORDER:
            ordered.extend(items)
    return ordered[:n]


def _gs_breakdown(headlines: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for h in headlines:
        gs, _ = _tag(h.get("title", ""))
        label = gs if gs else "General"
        counts[label] = counts.get(label, 0) + 1
    return counts


# ── Telegram format ────────────────────────────────────────────────────────────

def build_telegram_parts(data: dict) -> list[str]:
    edition_date = data.get("editionDate", "")
    headlines = data.get("headlines", [])
    sources = data.get("sources", [])
    source_statuses = data.get("sourceStatus", [])

    failed = [s["source"] for s in source_statuses if s.get("status") != "ok"]
    health = (
        f"⚠️ {len(failed)} source(s) failed: {_esc(', '.join(failed[:3]))}"
        if failed
        else "✅ All sources healthy"
    )

    must_know = _must_know(headlines)
    ongoing = _ongoing(headlines)
    facts = _key_facts(headlines)
    gs = _gs_breakdown(headlines)

    # ── Part 1: Header + Must-Know ──────────────────────────────────────────
    p1: list[str] = []
    p1.append(f"📰 <b>Velugo Daily Brief — {_fmt_date(edition_date)}</b>")
    p1.append(f"<i>{len(headlines)} headlines · {len(sources)} sources · UPSC Current Affairs</i>")
    p1.append("")

    if must_know:
        p1.append("🎯 <b>MUST-KNOW TODAY</b>")
        p1.append("")
        for i, h in enumerate(must_know, 1):
            enrich = h.get("enrichment") or {}
            topic = enrich.get("topic") or ", ".join(_tag(h.get("title", ""))[1]) or "General"
            angle = enrich.get("examAngle") or ""
            gs_label, _ = _tag(h.get("title", ""))
            label = " · ".join(p for p in [topic, gs_label] if p)

            title = _trunc(h.get("title", ""), 80)
            url = h.get("url", "")
            p1.append(f"{i}. <a href=\"{url}\">{_esc(title)}</a>")
            if label:
                p1.append(f"   <i>{_esc(_trunc(label, 80))}</i>")
            if angle:
                p1.append(f"   📌 <i>{_esc(_trunc(angle, 80))}</i>")
            p1.append("")

    # ── Part 2: Ongoing + Facts + GS + Footer ───────────────────────────────
    p2: list[str] = []

    if ongoing:
        p2.append("🔁 <b>ONGOING STORIES</b>")
        for h in ongoing:
            title = _trunc(h.get("title", ""), 65)
            day = h.get("storyDayCount", 2)
            p2.append(f"• {_esc(title)} → Day {day}")
        p2.append("")

    if facts:
        p2.append("📊 <b>KEY FACTS FOR PRELIMS</b>")
        for f, h in facts:
            emoji = _FACT_EMOJI.get(f["type"], "•")
            headline_title = _trunc(h.get("title", ""), 55)
            p2.append(f"{emoji} {_esc(f['text'])} — <i>{_esc(headline_title)}</i>")
        p2.append("")

    if gs:
        gs_line = "  ".join(
            f"{paper}: {count}"
            for paper, count in sorted(gs.items())
            if paper != "General"
        )
        if "General" in gs:
            gs_line += f"  General: {gs['General']}"
        p2.append("📚 <b>GS PAPER BREAKDOWN</b>")
        p2.append(gs_line)
        p2.append("")

    p2.append(health)
    p2.append("")
    p2.append("<i>Source-linked India current affairs for UPSC prep · #Velugo</i>")

    parts = ["\n".join(p1), "\n".join(p2)]
    # Trim any part that exceeds Telegram's limit
    return [p[:TELEGRAM_MAX_CHARS] for p in parts if p.strip()]


# ── Markdown format ────────────────────────────────────────────────────────────

def build_markdown(data: dict) -> str:
    edition_date = data.get("editionDate", "")
    headlines = data.get("headlines", [])
    sources = data.get("sources", [])
    source_statuses = data.get("sourceStatus", [])

    failed = [s["source"] for s in source_statuses if s.get("status") != "ok"]

    must_know = _must_know(headlines)
    ongoing = _ongoing(headlines)
    facts = _key_facts(headlines)
    gs = _gs_breakdown(headlines)

    lines: list[str] = []
    lines.append(f"# Velugo Daily Brief — {_fmt_date(edition_date)}")
    lines.append(f"*{len(headlines)} headlines · {len(sources)} sources · UPSC Current Affairs*")
    lines.append("")
    lines.append("---")
    lines.append("")

    if must_know:
        lines.append("## 🎯 Must-Know Today")
        lines.append("")
        for i, h in enumerate(must_know, 1):
            enrich = h.get("enrichment") or {}
            topic = enrich.get("topic") or ", ".join(_tag(h.get("title", ""))[1])
            gs_label, _ = _tag(h.get("title", ""))
            angle = enrich.get("examAngle") or ""
            why = enrich.get("whyItMatters") or ""
            relevance = enrich.get("upscRelevance") or h.get("priority", "")

            lines.append(f"### {i}. {h.get('title', '')}")
            meta_parts = []
            if topic:
                meta_parts.append(f"**Topic:** {topic}")
            if gs_label:
                meta_parts.append(f"**GS:** {gs_label}")
            if relevance:
                meta_parts.append(f"**Relevance:** {relevance}")
            if meta_parts:
                lines.append(" | ".join(meta_parts))
            if angle:
                lines.append(f"> {angle}")
            if h.get("excerpt"):
                lines.append(f"*{h['excerpt'][:200]}*")
            if why:
                lines.append(f"**Why it matters:** {why}")
            lines.append(f"[Read more →]({h.get('url', '')})")
            lines.append("")

        lines.append("---")
        lines.append("")

    if ongoing:
        lines.append("## 🔁 Ongoing Stories")
        lines.append("")
        for h in ongoing:
            day = h.get("storyDayCount", 2)
            lines.append(f"- **{h.get('title', '')}** → Day {day}")
            for e in h.get("storyEditions", [])[:3]:
                d_short = e.get("date", "")[5:]  # MM-DD
                lines.append(
                    f"  - {d_short}: [{_trunc(e.get('title', ''), 65)}]({e.get('url', '')})"
                )
        lines.append("")
        lines.append("---")
        lines.append("")

    if facts:
        lines.append("## 📊 Key Facts for Prelims")
        lines.append("")
        for f, h in facts:
            emoji = _FACT_EMOJI.get(f["type"], "•")
            lines.append(f"- {emoji} **{f['text']}** — {_trunc(h.get('title', ''), 70)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    if gs:
        lines.append("## 📚 GS Paper Breakdown")
        lines.append("")
        lines.append("| GS Paper | Headlines |")
        lines.append("|----------|-----------|")
        for paper, count in sorted(gs.items()):
            lines.append(f"| {paper} | {count} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    health_line = f"⚠️ Failed sources: {', '.join(failed)}" if failed else "✅ All sources healthy"
    lines.append(f"*{health_line} · Generated by [Velugo](https://github.com/)*")
    lines.append("")

    return "\n".join(lines)


# ── Telegram API ───────────────────────────────────────────────────────────────

def _send(token: str, channel_id: str, text: str) -> None:
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
    except Exception as exc:
        print(f"error: Telegram API unreachable: {exc}", file=sys.stderr)
        sys.exit(1)
    if not resp.get("ok"):
        print(f"error: Telegram API: {resp.get('description', resp)}", file=sys.stderr)
        sys.exit(1)


# ── Main ───────────────────────────────────────────────────────────────────────

def _load_edition(editions_dir: Path, date_str: str | None) -> dict:
    if date_str:
        path = editions_dir / f"{date_str}.json"
        if not path.exists():
            raise FileNotFoundError(f"Edition not found: {path}")
    else:
        editions = sorted(
            [p for p in editions_dir.glob("*.json") if p.stem != "index"],
            reverse=True,
        )
        if not editions:
            raise FileNotFoundError(f"No editions in {editions_dir}")
        path = editions[0]
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate UPSC brief and post to Telegram.")
    parser.add_argument("--date", help="Edition date YYYY-MM-DD. Defaults to latest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview Telegram messages and Markdown brief. Does not save or post.",
    )
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Write .md brief to assets/data/briefs/ but skip posting to Telegram.",
    )
    parser.add_argument("--editions-dir", default="assets/data/editions")
    parser.add_argument("--briefs-dir", default="assets/data/briefs")
    args = parser.parse_args()

    try:
        data = _load_edition(Path(args.editions_dir), args.date)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    edition_date = data.get("editionDate", "unknown")
    tg_parts = build_telegram_parts(data)
    md_text = build_markdown(data)

    if args.dry_run:
        print(f"── Telegram preview ({edition_date}) ──")
        for i, part in enumerate(tg_parts, 1):
            print(f"\n[Part {i}/{len(tg_parts)} — {len(part)} chars]\n")
            print(part)
        print(f"\n── Markdown brief ({len(md_text)} chars) ──\n")
        print(md_text)
        return 0

    # Save .md brief
    brief_dir = Path(args.briefs_dir)
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / f"{edition_date}.md"
    brief_path.write_text(md_text, encoding="utf-8")
    print(f"wrote brief to {brief_path}")

    if args.save_only:
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not token or not channel_id:
        print(
            "error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set to post.",
            file=sys.stderr,
        )
        print("       Use --dry-run to preview or --save-only to just write the .md.", file=sys.stderr)
        return 1

    for part in tg_parts:
        _send(token, channel_id, part)
    print(f"posted {len(tg_parts)} message(s) to {channel_id} for {edition_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
