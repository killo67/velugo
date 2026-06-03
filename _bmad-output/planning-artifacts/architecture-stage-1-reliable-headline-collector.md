---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/product/mirofish-mvp-fit-assessment-2026-04-22.md
  - docs/mirofish-design-reference.md
  - scripts/fetch_india_headlines.py
  - src/index.html
  - src/app.js
  - assets/data/india-headlines.js
workflowType: architecture
project_name: newAgg
user_name: Havishakillo
date: 2026-04-22
status: final
---

# Architecture Decision Document - newAgg Stage 1

## Architecture Summary

Stage 1 uses a static-site-plus-generator architecture:

- A Python command fetches RSS feeds, normalizes headline data, records source status, deduplicates items, and writes artifacts.
- A browser-only static UI reads the generated JS artifact and renders the board.
- JSON edition files provide an audit trail for daily runs.

There is no backend server, database, account system, or AI processing in this stage. This keeps the system aligned with the product risk: reliable headline collection.

## Tool Selection

### Selected

| Layer | Tool | Reason |
|---|---|---|
| Collector | Python 3 standard library | Already in repo, zero dependency install, enough for RSS/XML/HTTP/date parsing. |
| Display | Static HTML/CSS/JS | Current MVP works without build tooling or dev server. |
| Data exchange | JSON plus browser-loadable JS wrapper | JSON gives auditability; JS preserves current UI loading model. |
| Storage | Files under `assets/data` | Simple, inspectable, fits Stage 1. |
| Validation | `node --check`, `py_compile` | Fast syntax validation with no framework setup. |

### Deferred

| Tool | Why Deferred |
|---|---|
| FastAPI/Flask | No current need for HTTP APIs or users. |
| SQLite/Postgres | Files are enough until we need query history or multi-user access. |
| Feedparser dependency | Useful later, but standard library is enough for Stage 1 RSS/Atom support. |
| Scheduler | Manual command first; schedule only after the command is reliable. |
| AI/LLM | Headline-only data is too thin for grounded summarization. |
| Graph database | Clustering/story continuity are Stage 3+ concerns. |

## Component Design

### Collector CLI

Path: `scripts/fetch_india_headlines.py`

Responsibilities:

- hold source configuration
- fetch enabled feeds
- parse RSS and Atom entries
- filter by edition date
- normalize and deduplicate records
- produce source-level status
- write edition JSON
- write browser JS data
- enforce minimum headline count

### Artifacts

Paths:

- `assets/data/india-headlines.js`
- `assets/data/editions/YYYY-MM-DD.json`

The JS file is the app-facing artifact. The JSON file is the durable edition artifact.

### Static UI

Paths:

- `src/index.html`
- `src/app.js`
- `src/styles.css`

Responsibilities:

- load `window.__INDIA_HEADLINES__`
- show summary metrics
- filter by source/category/search
- open original source links

Stage 2 can add source status UI using the Stage 1 payload.

## Data Flow

```text
Configured RSS feeds
  -> fetch_india_headlines.py
  -> parse entries
  -> date filter in Asia/Kolkata
  -> normalize + dedupe
  -> build payload with fetchStatus/sourceStatus
  -> assets/data/editions/YYYY-MM-DD.json
  -> assets/data/india-headlines.js
  -> src/index.html renders board
```

## Payload Contract

Required top-level fields:

- `generatedAt`
- `editionDate`
- `region`
- `note`
- `fetchStatus`
- `sourceStatus`
- `sources`
- `headlines`

Required headline fields:

- `id`
- `sourceId`
- `source`
- `title`
- `category`
- `priority`
- `url`
- `publishedAt`

Required source status fields:

- `sourceId`
- `source`
- `status`
- `feedUrl`
- `fetched`
- `accepted`
- `skipped`
- `duplicates`
- `error`

## Source Strategy

Use official RSS feeds where possible. Include at least five Indian sources in configuration, even if some fail on a given run. Source failures are product data, not invisible script noise.

Initial source set:

- The Indian Express
- The Times of India
- NDTV
- Hindustan Times
- Business Standard

Optional later additions:

- The Hindu
- Deccan Herald
- India Today
- Mint

## Failure Policy

The collector should continue through individual source failures, then decide final success from output quality.

Default failure conditions:

- zero accepted headlines
- accepted headline count below `--min-headlines`
- no source succeeded
- artifact write failure

`--allow-partial` overrides the minimum-count failure for development and known low-volume days.

## Deduplication Strategy

Stage 1 uses conservative dedupe:

- canonical URL stripping fragments and common tracking query parameters
- normalized title lowercased with punctuation and whitespace collapsed

This avoids obvious duplicates without prematurely clustering related stories.

## Security And Compliance

- No credentials.
- No scraping behind authentication.
- Source links are preserved.
- Headlines are short factual references, not copied articles.
- No MiroFish source code or assets are reused.

## Implementation Plan

1. Extend source config to at least five feeds.
2. Add `--date`, `--min-headlines`, `--allow-partial`, `--edition-dir`.
3. Add source status tracking.
4. Add JSON edition output.
5. Add dedupe.
6. Preserve JS output compatibility.
7. Validate with syntax checks and a partial run if live feeds are unavailable.

## Architecture Decision Records

### ADR-001: Keep Stage 1 Static

Decision: no backend service for Stage 1.

Rationale: the product risk is source reliability, not API scalability.

### ADR-002: Use File Artifacts

Decision: write JSON edition files plus current JS data file.

Rationale: gives auditability while preserving the current UI.

### ADR-003: Avoid AI Until Article Text Exists

Decision: no AI summaries or briefings in Stage 1.

Rationale: headline-only AI output would not be sufficiently grounded.

### ADR-004: Use Selected MiroFish Patterns Only

Decision: borrow state/artifact/progress thinking, not platform code or architecture.

Rationale: MiroFish is too large for this MVP and is AGPL-licensed.
