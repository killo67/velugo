---
type: final-prd
project: newAgg
feature: India Headline MVP
author: Havishakillo
date: 2026-04-22
status: final
source_of_truth:
  - original free public online source pages and feeds
input_artifacts:
  - _bmad-output/planning-artifacts/prd-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/architecture-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/research/llm-wiki-fit-analysis-2026-04-22.md
  - _bmad-output/planning-artifacts/next-steps-india-headline-mvp-2026-04-22.md
implementation_artifacts:
  - scripts/fetch_india_headlines.py
  - src/index.html
  - src/app.js
  - src/styles.css
  - assets/data/india-headlines.js
  - assets/data/editions/2026-04-22.json
---

# Final PRD - newAgg India Headline MVP

## Product Summary

newAgg is a dependency-free static MVP for collecting and displaying India news headlines from free public online sources. The product helps a reader or maintainer scan current India headlines, see which sources contributed, and open the original source link for verification.

The app does not summarize, rewrite, or infer news. The source of truth is always the original newspaper or public news source.

## Problem

Readers need a quick way to scan India headlines across multiple public sources without losing source traceability. Maintainers need to know whether a daily edition was actually collected well or whether missing coverage is caused by feed failures, stale feeds, or out-of-scope sources.

## Goals

- Collect source-linked India headlines from free public online sources.
- Prefer strict newspaper sources where available.
- Keep broader free public news publishers available only when clearly classified.
- Show source health and source eligibility metadata in the generated artifact and UI.
- Preserve auditable daily edition files.
- Keep the app simple: static HTML/CSS/JS plus a dependency-free Python collector.

## Non-Goals

- No backend API.
- No database.
- No login or personalization.
- No article body scraping.
- No AI summaries.
- No LLM wiki in the MVP.
- No model-generated claims.
- No ranking based on unsupported assumptions.

## Users

Primary user: maintainer/editorial researcher.

Primary job:

- "Generate a fresh India headline board and know which free public sources succeeded, failed, or may be outside strict newspaper scope."

Secondary user: reader/researcher.

Secondary job:

- "Scan India headlines quickly and open the original source for verification."

## Source Policy

The MVP uses free public online source data, especially official RSS feeds.

Each source must declare:

- `sourceType`: for example `newspaper` or `digital_news_publisher`
- `section`: source section used, for example `India` or `National`
- `countryScope`: expected scope, currently `India`
- `isFreeToRead`: whether the linked public source is expected to be freely accessible
- `policyNotes`: human-readable source eligibility note

Strict newspaper sources are preferred. Non-newspaper sources may remain enabled if they are free public India news sources and are clearly classified.

## Functional Requirements

### FR1 - Source Registry

The collector shall maintain configured source definitions in code for the MVP.

Each enabled source shall include:

- `id`
- `name`
- `feed_url`
- `site_url`
- `source_type`
- `section`
- `country_scope`
- `is_free_to_read`
- `policy_notes`
- `category`
- `enabled`

### FR2 - Public Feed Collection

The collector shall fetch enabled public feeds with a user agent and timeout.

A single source failure shall not abort the run. Source failures shall be recorded in `sourceStatus`.

### FR3 - RSS And Atom Parsing

The collector shall parse common RSS and Atom fields:

- title
- link
- publication date
- updated date when applicable

Entries without title, link, or parseable publication date shall be skipped and counted.

### FR4 - India Edition Date Filtering

The collector shall default to today's date in Asia/Kolkata and support `--date YYYY-MM-DD`.

Only items whose publication date matches the requested India edition date shall be included.

### FR5 - Deduplication

The collector shall deduplicate obvious repeats using:

- canonical URL with common tracking parameters removed
- normalized title

Duplicates shall be counted by source and omitted from final headlines.

### FR6 - Data Artifacts

The collector shall write:

- `assets/data/india-headlines.js`
- `assets/data/editions/YYYY-MM-DD.json`

Both artifacts shall use the same payload shape.

### FR7 - Source Health

The payload and UI shall expose source health:

- source status
- feed URL
- fetched count
- accepted count
- skipped count
- duplicate count
- error message
- source policy metadata

### FR8 - Reader Scan Board

The static UI shall display:

- edition timestamp
- headline count
- source count
- lead count
- source health cards
- source filter
- category filter
- headline search
- headline cards linking to original source pages

### FR9 - CLI Controls

The collector shall support:

- `--date YYYY-MM-DD`
- `--limit N`
- `--min-headlines N`
- `--allow-partial`
- `--output PATH`
- `--edition-dir PATH`

### FR10 - Failure Policy

The collector shall exit non-zero when collected headlines are below `--min-headlines`, unless `--allow-partial` is passed.

Partial artifacts may still be written for inspection.

## Data Contract

Required top-level fields:

- `generatedAt`
- `editionDate`
- `region`
- `note`
- `fetchStatus`
- `sourceStatus`
- `sources`
- `headlines`

Required source fields:

- `id`
- `name`
- `url`
- `feedUrl`
- `sourceType`
- `section`
- `countryScope`
- `isFreeToRead`
- `policyNotes`

Required source status fields:

- `sourceId`
- `source`
- `status`
- `feedUrl`
- `sourceType`
- `section`
- `countryScope`
- `isFreeToRead`
- `policyNotes`
- `fetched`
- `accepted`
- `skipped`
- `duplicates`
- `error`

Required headline fields:

- `id`
- `sourceId`
- `source`
- `title`
- `category`
- `priority`
- `url`
- `publishedAt`

## Source-Grounded Interestingness

The MVP may make the board more useful using deterministic metadata:

- latest first
- source filtering
- category filtering
- visible source diversity
- visible source health
- lead labels based on recency order

The MVP shall not generate claims about why a story is important unless that reason is explicitly supported by stored source metadata or future article text.

## Current Source Notes

Current enabled sources include:

- The Indian Express: strict newspaper source
- The Times of India: strict newspaper source
- Hindustan Times: strict newspaper source
- The Hindu: strict newspaper source
- Business Standard: newspaper source, current feed is generic/latest and may fail
- NDTV: free public digital news publisher, not a strict newspaper

## Acceptance Criteria

- The collector writes both JS and JSON edition artifacts.
- Generated artifacts include source policy metadata.
- Generated artifacts include `fetchStatus` and `sourceStatus`.
- The UI renders source health cards.
- A failed feed is visible in the UI.
- Every headline title comes from source feed data.
- Every headline links to the original source URL.
- Date filtering uses Asia/Kolkata.
- Validation commands pass:
  - `node --check src/app.js`
  - `node --check assets/data/india-headlines.js`
  - `PYTHONPYCACHEPREFIX=/tmp/newagg-pycache python3 -m py_compile scripts/fetch_india_headlines.py`

## Final MVP Decision

The MVP is complete enough for the next BMAD phase when:

- source health is visible
- source policy metadata is present
- generated artifacts are auditable
- the board remains static and dependency-free
- all news facts remain sourced to original public online source pages

