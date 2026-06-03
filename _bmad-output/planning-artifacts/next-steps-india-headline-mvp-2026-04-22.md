---
type: bmad-next-steps
project: newAgg
created: 2026-04-22
status: ready-for-planning
input_artifacts:
  - _bmad-output/planning-artifacts/prd-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/architecture-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/research/llm-wiki-fit-analysis-2026-04-22.md
decision_summary:
  - continue with headline MVP
  - do not add LLM wiki in Stage 1
  - source of truth remains original newspaper source
---

# Next Steps - India Headline MVP

## Direction

Progress the MVP as a source-grounded India newspaper headline board.

The next work should improve source quality, reader scanability, and validation before adding any AI, wiki, database, or backend layer.

## Recommended Sequence

### 1. Tighten Source Policy

Goal: make "free online India newspapers" explicit and testable.

Actions:

- Add source metadata fields in `scripts/fetch_india_headlines.py`:
  - `source_type`
  - `section`
  - `country_scope`
  - `is_free_to_read`
  - `policy_notes`
- Prefer official India/national RSS feeds from newspapers.
- Replace or classify sources that are not strict newspaper sources.
- Avoid generic "latest" feeds when an India/national feed exists.

Acceptance:

- Every source has explicit eligibility metadata.
- Every source is either accepted as a free India newspaper source or clearly marked as out of strict newspaper scope.
- Output artifacts include enough source metadata for BMAD QA to validate scope.

### 2. Improve Source Set

Goal: collect from stronger India newspaper sources.

Candidate strict newspaper sources to evaluate:

- The Hindu
- The Indian Express
- Hindustan Times
- The Times of India
- Deccan Herald
- The Tribune
- The Telegraph India
- Mint, if business/economy headlines are in scope
- Business Standard, only if a working public India/news feed is available

Current source concerns:

- NDTV is a news publisher, but not a newspaper. Keep only if the product expands from newspapers to news publishers.
- Business Standard currently uses a generic latest feed and returned `403` in the seeded artifact. Replace, repair, or disable.

Acceptance:

- At least 5 enabled sources match the chosen source policy.
- Failed feeds appear in `sourceStatus`.
- The collector can still produce a useful edition when one source fails.

### 3. Add Reader-Facing Source Health

Goal: make the board transparent instead of silently hiding feed problems.

Actions:

- Show source status in the static UI:
  - ok/error
  - accepted count
  - skipped count
  - duplicate count
  - feed error if any
- Add a small freshness indicator using `generatedAt` and `editionDate`.

Acceptance:

- A reader/maintainer can see which newspapers contributed to the current board.
- A failed source does not look like missing editorial coverage.

### 4. Add Source-Grounded Interestingness

Goal: make headlines more useful without model assumptions.

Allowed signals:

- latest first
- source diversity
- repeated coverage across multiple newspapers
- configured section/category
- lead ranking based on deterministic metadata

Avoid:

- LLM deciding what is important from headline text alone
- unsupported summaries
- claims that require article text when only headline text exists

Acceptance:

- Ranking/filtering reasons can be explained from stored metadata.
- No generated statement is treated as newspaper fact.

### 5. Prepare Stage 2 PRD Update

Goal: give BMAD PM a concrete edit target.

Recommended PRD additions:

- strict source eligibility requirement
- source metadata data contract
- source health UI requirement
- source-grounded ranking/filtering requirement
- explicit non-goal: no LLM wiki or AI summaries in Stage 1/2

Acceptance:

- PRD and architecture agree on source policy.
- Dev stories can be written without ambiguity.

## First Implementation Story

Title: Add strict newspaper source metadata and expose source health

User story:

As a maintainer, I want each configured source to declare whether it is a free online India newspaper source, so that the headline board can be validated against the project scope.

Scope:

- update `FeedSource` metadata
- include source metadata in generated `sources`
- keep `sourceStatus` unchanged or extend it only where useful
- update source list to disable or annotate questionable sources
- update static UI to expose source health

Validation:

- `node --check src/app.js`
- `node --check assets/data/india-headlines.js`
- `PYTHONPYCACHEPREFIX=/tmp/newagg-pycache python3 -m py_compile scripts/fetch_india_headlines.py`
- `python3 scripts/fetch_india_headlines.py --date 2026-04-22 --allow-partial`

## BMAD Agent Handoff

PM:

- Update the PRD with source eligibility and source health requirements.

Architect:

- Keep the static artifact architecture.
- Add metadata fields without adding a backend.

Dev:

- Implement source metadata and UI source health.
- Do not add AI or LLM wiki.

QA:

- Validate source eligibility, artifact integrity, date filtering, and error visibility.

UX:

- Make source health and freshness visible without turning the MVP into a dashboard-heavy tool.

## Decision Checkpoint

Before building story clustering or AI features, answer:

- Are we strictly newspaper-only, or free India news publishers?
- Are business/economy sources in scope?
- Do we want article text collection later, or headlines only?
- Should "interesting" mean latest, multi-source coverage, editorially selected categories, or a mix?

