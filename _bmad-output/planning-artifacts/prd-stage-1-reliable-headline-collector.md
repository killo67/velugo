---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - docs/mirofish-design-reference.md
  - _bmad-output/planning-artifacts/product/mirofish-mvp-fit-assessment-2026-04-22.md
  - scripts/fetch_india_headlines.py
  - src/index.html
  - src/app.js
  - assets/data/india-headlines.js
workflowType: prd
project: newAgg
feature: Stage 1 Reliable Headline Collector
author: Havishakillo
date: 2026-04-22
status: final
---

# Product Requirements Document - newAgg Stage 1

## Executive Summary

newAgg Stage 1 upgrades the current static India headlines board into a reliable daily collection workflow. The product goal is simple: one command should collect today's online India headlines from multiple Indian news sources, record source-level fetch status, deduplicate obvious repeats, and publish a browser-ready data file plus an auditable JSON edition artifact.

This stage deliberately avoids backend services, databases, AI summaries, graph systems, and speculative features. The fastest validation path is to prove that the source collection itself works every day.

## Problem

The current MVP can display a useful headline board, but the collection process is still fragile:

- Seed data can drift stale.
- RSS failures are invisible to the UI and maintainer.
- There is no edition archive for what was collected on a given day.
- Duplicate or near-identical headlines can clutter the board.
- The refresh script only covers a small set of sources.

If headline collection is unreliable, later features such as clustering, briefings, and source-grounded analysis will be built on sand.

## Users And Jobs

Primary user: a maintainer/editorial researcher who wants to quickly populate a daily India headline board.

Core job:

- "Give me a fresh, source-linked India headline board for today's newspaper/news cycle, and tell me which sources succeeded or failed."

Secondary user: a reader or researcher scanning the board.

Core job:

- "Let me quickly scan current India headlines and open the original source."

## Scope

### In Scope

- Fetch headlines from at least 5 configured Indian news sources.
- Keep only items matching the selected edition date in Asia/Kolkata.
- Generate an auditable JSON edition file under `assets/data/editions/YYYY-MM-DD.json`.
- Generate browser-ready `assets/data/india-headlines.js`.
- Track per-source status: fetched count, accepted count, skipped count, duplicate count, error.
- Deduplicate exact/obvious repeats using normalized title and canonical URL.
- Support `--date YYYY-MM-DD`.
- Support configurable minimum output count.
- Fail non-zero when output is empty or below required count unless explicitly allowed.
- Keep the current static UI compatible with the generated data.

### Out Of Scope

- Backend API.
- Database.
- Login/user accounts.
- Article body scraping.
- AI-generated summaries.
- Entity extraction or graphing.
- Source ranking beyond simple source metadata.
- Speculative or synthetic social-environment features.

## Success Criteria

- `python3 scripts/fetch_india_headlines.py` writes both JS and JSON artifacts.
- The default run targets today's date in Asia/Kolkata.
- The collector supports at least 5 source definitions.
- The artifact includes `fetchStatus` and `sourceStatus`.
- The script exits non-zero if it cannot collect the configured minimum number of headlines, unless `--allow-partial` is passed.
- The static page loads generated data without code changes.
- Validation commands pass:
  - `node --check assets/data/india-headlines.js`
  - `node --check src/app.js`
  - `PYTHONPYCACHEPREFIX=/tmp/newagg-pycache python3 -m py_compile scripts/fetch_india_headlines.py`

## Functional Requirements

### FR1 - Source Configuration

The collector shall define source metadata in code for Stage 1:

- `id`
- `name`
- `feed_url`
- `site_url`
- default category
- enabled flag

### FR2 - Fetch RSS Feeds

The collector shall request each enabled feed with a user agent and timeout. A failed source shall not abort the entire run unless all sources fail or output falls below the minimum count.

### FR3 - Parse RSS And Atom

The collector shall support common RSS item fields:

- `title`
- `link`
- `pubDate`
- `guid`

The collector should also tolerate Atom-style entries where feasible.

### FR4 - Date Filtering

The collector shall keep items whose published date matches the requested edition date in Asia/Kolkata.

If an item has no parseable date, it shall be skipped and counted in source status.

### FR5 - Deduplication

The collector shall deduplicate by:

- canonical URL without tracking query strings, and
- normalized headline title.

Duplicate items shall be counted but not included in the final headline list.

### FR6 - Artifact Generation

The collector shall write:

- `assets/data/editions/YYYY-MM-DD.json`
- `assets/data/india-headlines.js`

Both artifacts shall include the same payload shape.

### FR7 - Fetch Status

The payload shall include:

- `generatedAt`
- `editionDate`
- `region`
- `fetchStatus`
- `sourceStatus`
- `sources`
- `headlines`

### FR8 - CLI Controls

The collector shall support:

- `--date YYYY-MM-DD`
- `--limit N`
- `--min-headlines N`
- `--allow-partial`
- `--output PATH`
- `--edition-dir PATH`

### FR9 - Static UI Compatibility

The current static UI shall continue reading `window.__INDIA_HEADLINES__` from `assets/data/india-headlines.js`.

## Non-Functional Requirements

- Dependency-free for Stage 1.
- No secrets or API keys.
- Deterministic artifact paths.
- Human-readable JSON edition artifacts.
- Clear stderr warnings for source failures.
- No copied MiroFish code or assets.

## Data Contract

```json
{
  "generatedAt": "2026-04-22T18:20:00+05:30",
  "editionDate": "2026-04-22",
  "region": "India",
  "fetchStatus": {
    "status": "complete",
    "sourcesConfigured": 5,
    "sourcesSucceeded": 4,
    "sourcesFailed": 1,
    "fetched": 40,
    "accepted": 24,
    "skipped": 12,
    "duplicates": 4,
    "errors": 1
  },
  "sourceStatus": [
    {
      "sourceId": "indian-express",
      "source": "The Indian Express",
      "status": "ok",
      "fetched": 10,
      "accepted": 8,
      "skipped": 2,
      "duplicates": 0,
      "error": null
    }
  ],
  "sources": [],
  "headlines": []
}
```

## Tool Decision

Selected tools for Stage 1:

- Python standard library for RSS fetching/parsing.
- Static HTML/CSS/JavaScript for display.
- JSON edition files for auditability.
- Browser-loadable JS data file for compatibility.

Rejected for Stage 1:

- Backend framework.
- Database.
- Feed parsing dependency.
- AI summarization.
- External graph service.

## Acceptance Tests

1. Running the collector with today's date writes a JS file and an edition JSON file.
2. Generated payload contains at least 5 configured sources.
3. `fetchStatus` and `sourceStatus` exist.
4. Duplicate titles do not appear twice in final headlines.
5. The static page still opens with generated data.
6. The script exits non-zero when minimum headline count is unmet and `--allow-partial` is not set.

## Next Stage

Stage 2 should improve the scan board:

- source status panel
- sort controls
- lead-only toggle
- better empty/error states
- copy/open source affordances
