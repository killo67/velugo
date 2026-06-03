# Phase 1 Tracker — Foundation (0–8 weeks)

**Goal:** Make the platform genuinely useful for UPSC prep by adding real article context, more sources, automation, and archive navigation.

**Status legend:** `[ ]` todo · `[x]` done · `[-]` deferred

---

## 1. Article Text Extraction

> Fetch the article page for each headline, strip nav/ads, store body text (~1500 chars). Unlocks Phase 2 LLM enrichment and better excerpts for sources that don't provide RSS descriptions.

- [x] `fetch_article_text(url)` — HTTP fetch with 10s timeout, returns raw HTML
- [x] `extract_article_body(html)` — regex/heuristic strip of nav/scripts/ads, returns clean text
- [x] `truncate_article_text(text, max_chars=1500)` — clips at word boundary
- [x] `articleText` field added to edition JSON data contract
- [x] `--extract-text` flag on `fetch_india_headlines.py` (opt-in, off by default)
- [x] Parallel fetch via `ThreadPoolExecutor(max_workers=6)` — 141 articles in ~14s
- [x] Tested across active sources:
  - The Hindu: ✓ clean body extraction (648–1500 chars)
  - Livemint: ✓ excellent (1499 chars)
  - Hindustan Times: ✓ excellent (1493 chars)
  - NDTV: ✗ blocked (0 chars, falls back to RSS excerpt)
  - Indian Express: ✗ paywalled (returns "Expand", falls back to RSS excerpt)
  - Business Standard: ✗ 403 on feed itself
- [x] Fallback: when article fetch fails, `excerpt` populated from RSS; `articleText` = `""`
- [x] Fallback 2: if RSS excerpt empty and article text found, excerpt auto-filled from article text

---

## 2. PIB Integration

> Press Information Bureau — official Government of India press releases. High UPSC signal.

- [x] Investigated PIB feed: `RssMain.aspx?ModId=6&Lang=1&Regid=3` returns valid RSS 2.0 XML — but Hindi-only, no pubDate
- [x] Discovered two-step PRID resolution: Hindi RSS → fetch Hindi PRID page → find English PRID link → fetch English page
- [x] `fetch_pib_source()` — full parallel fetcher (6 workers), 20 Hindi PRIDs → ~15 English releases in ~8s
- [x] `_pib_extract_datetime()` — extracts actual release time ("29 MAY 2026 5:59PM") for correct ordering
- [x] `_pib_parse_english_content()` — uses og:title for authoritative English title, extracts ministry + body
- [x] HTML entity pre-decoding fixed: `&lt;i>suo motu` no longer leaks `>` into titles
- [x] Per-source cap (`MAX_PER_SOURCE = 15`) added to `dedupe_headlines()` to prevent The Hindu dominance
- [x] Total limit raised to 100; today's edition: 87 headlines across 8 sources
- [x] Add `pib.gov.in` source (`source_type="pib"`) to SOURCES; dispatched in `collect()` by type
- [x] Test confirmed: 15 PIB headlines, clean English titles, excerpts, article text, correct URLs

---

## 3. Automation (Daily Cron)

> Run fetch + extract automatically at 6:30am IST every day. No manual intervention.

- [x] Write `launchd` plist for macOS (`scripts/com.newagg.daily-fetch.plist`) — fires 6:30am local time; `sed` install command substitutes real PROJECT_DIR
- [x] Write `cron` equivalent for Linux/VPS — documented in README (`0 1 * * *` UTC = 6:30am IST)
- [x] `scripts/run-daily.sh` wrapper — resolves project root, writes dated log files, passes `--extract-text --allow-partial --notify`
- [x] `--notify` flag: `osascript display notification` on macOS, silently skipped on Linux
- [x] Document setup steps in README (load/unload, verify, manual test, logs)

---

## 4. Archive Navigation (UI)

> Let users browse past editions. Edition JSON files exist — just need UI to list and load them.

- [x] `write_payload()` now regenerates `assets/data/editions/index.json` after each fetch (sorted descending)
- [x] Archive nav added to topbar: `‹ [date select] ›` buttons + dropdown, dark-theme styled
- [x] `?edition=YYYY-MM-DD` URL param: loads that edition's JSON via `fetch()` before first render
- [x] Prev/Next buttons navigate adjacent editions; disabled at boundaries
- [x] `loadEdition()` updates URL via `history.pushState()` — no full page reload
- [x] Fallback: missing edition → 404 caught silently, stays on current edition
- [x] Tested: 3 editions served correctly, 0 title overlap across dates, missing edition 404s

---

## 5. Quality Bar

> Ensure the page never shows a broken or nearly-empty edition.

- [x] Hard-floor warning: always prints to stderr when `accepted < 10`, even with `--allow-partial` — ensures daily logs always capture very low counts
- [x] Multi-source failure alert: if `>3` sources fail simultaneously, prints a distinct `alert:` line to stderr; `--notify` message changes to "degraded edition" with failure count
- [x] Business Standard: `enabled=False` (feed returns HTTP 403 on every request; dropped from active sources until a working feed URL is confirmed)

---

## Phase 1 Definition of Done

- [ ] At least 30 headlines daily with >50% having article text
- [ ] PIB integrated and producing ≥3 daily headlines
- [ ] Automation running without manual intervention for 3 consecutive days
- [ ] Archive nav working: can browse last 7 days
- [ ] Source health shows ≤1 failed source on average

---

## Phase 2 — In Progress

### P2.1 Prelims Fact Extraction ✓

- [x] `extract_facts(headline)` — regex patterns over title + excerpt + first 500 chars of articleText
- [x] Patterns: rank (ordinal-required), money (Rs/₹/INR + crore/lakh/million), constitutional (Article N, Schedule N, Nth Amendment), stat (N%), appointment (role keywords)
- [x] `facts: [{"type": str, "text": str}]` field on every headline (empty list if none)
- [x] Cap: 3 facts per headline, deduped by type+label
- [x] Called always in `collect()` — zero overhead (pure regex, no HTTP)
- [x] UI: `renderFacts()` helper, `.fact-chip--{type}` chips below excerpt on all cards
- [x] Chip colours: rank=teal, money=amber, constitution=purple, stat=blue, appointment=yellow

### P2.2 Key Terms Glossary ✓

- [x] `assets/data/glossary.json` — 209 terms across 10 categories (constitutional, economic, legal, scheme, international, environment, science, defence, education, infrastructure)
- [x] Case-sensitive matching to prevent false positives (e.g. "COP" vs "cop", "WHO" vs "who") — Indian news always capitalises abbreviations
- [x] Single-pass regex (longest-term-first alternation) — no double-replacement problem
- [x] `loadGlossary()` fetches on startup, awaited before first render; degrades silently if missing
- [x] `applyGlossary(text)` escapes HTML, then wraps matched terms in `<abbr class="gloss-term" data-def="...">`
- [x] Pure CSS tooltip via `::after { content: attr(data-def) }` — no JS library needed
- [x] Applied to headline titles and excerpts in both must-know and all-headlines card templates
- [x] Coverage on June 1 edition: 15/98 headlines, all legitimate matches

### P2.3 LLM Enrichment (`--enrich` flag) ✓

- [x] `enrich_headlines(headlines, api_key)` — parallel batched calls (batch=10, workers=4) via `ThreadPoolExecutor`
- [x] `_enrich_batch()` — calls `claude-haiku-4-5-20251001`; prompt includes UPSC topic taxonomy; parses JSON array response
- [x] Output per headline: `enrichment: {topic, upscRelevance, examAngle, whyItMatters}`
- [x] Caching: skips headlines that already have `enrichment` — safe to re-run after partial failure
- [x] Graceful degradation: warns if `ANTHROPIC_API_KEY` missing; UI falls back to rule-based data when enrichment absent
- [x] `augmentData()` overrides `studyPriority` with `enrichment.upscRelevance` when present (High→High-yield, Medium→Useful, Low→General update)
- [x] UI: `.topic-path` breadcrumb above card title; `.exam-angle` italic line below excerpt; `whyItMatters` replaces rule-based `whyStudy`
- [x] `run-daily.sh` loads `scripts/.env` for `ANTHROPIC_API_KEY` and passes `--enrich` to daily run
- [x] Estimated cost: ~$0.03–0.05 per full edition (Haiku pricing)

### P2.4 Story Threads ✓
- [x] `load_past_editions()` — reads last 7 edition JSONs from `assets/data/editions/`
- [x] `thread_stories()` — Jaccard matching (CLUSTER_MIN_SHARED=2, CLUSTER_JACCARD=0.20) against past headlines
- [x] `storyId`, `storyEditions: [{date, title, url}]`, `storyDayCount` fields on matched headlines
- [x] UI: `renderStoryThread()` using `<details>/<summary>` — "Ongoing · Day N" indigo pill badge, click expands past appearances
- [x] Applied to both must-know and all-headlines cards
- [x] Tested: 15 headlines threaded across 3 past editions; accurate matches (Annamalai/BJP, NEET, Great Nicobar)

---

## Phase 3 — In Progress

### P3.A+B Telegram Distribution + Daily Brief ✓

- [x] `scripts/post_telegram.py` — full rewrite using edition enrichment, facts, story threads
- [x] Brief structure: Header + Must-Know (Telegram Part 1) / Ongoing Stories + Prelims Facts + GS Breakdown (Part 2)
- [x] Must-Know selection: enrichment.upscRelevance=High (score 3) > rule-based priority=High (score 2) > Medium (score 1)
- [x] Ongoing Stories: headlines with storyDayCount > 1, sorted by day count desc
- [x] Key Facts: aggregated fact chips across all headlines, type-prioritised (constitution > appointment > money > stat > rank)
- [x] GS Breakdown: rule-based tagging of all headlines by GS paper
- [x] Two output modes: `--save-only` (writes `assets/data/briefs/YYYY-MM-DD.md`) and default (post to Telegram)
- [x] `--dry-run` previews both Telegram messages and Markdown brief
- [x] `--date` flag to generate brief for any past edition
- [x] Part sizing: 1955 + 804 chars (well within Telegram 4096 limit)
- [x] `scripts/run-daily.sh` updated: calls `post_telegram.py` after fetch; posts if `TELEGRAM_BOT_TOKEN` set, else saves .md only
- [x] Telegram setup: needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHANNEL_ID` in `scripts/.env`

**Telegram setup steps:**
1. Message @BotFather → `/newbot` → copy token
2. Create a Telegram channel → add bot as admin → copy @channelname or numeric ID
3. Add to `scripts/.env`: `TELEGRAM_BOT_TOKEN=xxx` and `TELEGRAM_CHANNEL_ID=@channelname`
4. Test: `python3 scripts/post_telegram.py --dry-run`
5. First real post: `python3 scripts/post_telegram.py`
