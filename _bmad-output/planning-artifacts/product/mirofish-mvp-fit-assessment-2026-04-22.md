---
type: bmad-product-manager-assessment
product: newAgg
artifact: MiroFish MVP fit assessment
created: 2026-04-22
owner: Havishakillo
skill_used: bmad-agent-pm
reference_doc: ../../../../docs/mirofish-design-reference.md
current_mvp:
  - src/index.html
  - src/app.js
  - assets/data/india-headlines.js
  - scripts/fetch_india_headlines.py
decision: use-selected-patterns-only
---

# MiroFish Fit For newAgg MVP

## PM Verdict

Use about **20-25% of MiroFish as product inspiration for the MVP**, not as code and not as a full architecture.

Why so little? Because our current MVP job is narrow: **get today's online India newspaper headlines, populate a board, and let a user scan/filter them quickly**. MiroFish is a much larger document-to-graph/reporting system. If we import its whole mental model now, we will slow down the headline validation loop.

Use MiroFish now for:

- source/project state thinking
- refresh/task status patterns
- report/briefing artifact shape
- future evidence graph direction

Do not use it now for:

- external graph services
- heavy backend/frontend split
- synthetic social-environment workflows
- large multi-agent orchestration
- AGPL source code

## Current MVP Job

The MVP currently proves this user workflow:

1. User opens the static headline board.
2. User sees today's India headlines.
3. User filters by source or category.
4. User searches headline text.
5. User clicks through to the original source.
6. Maintainer can refresh data through `scripts/fetch_india_headlines.py`.

This is not yet a full news intelligence product. It is a collection and display prototype.

## Product Fit Matrix

| MiroFish Pattern | Fit For Current MVP | Use Now? | PM Rationale |
|---|---:|---|---|
| Project/source state model | High | Yes | We need a clean concept of edition date, sources, generated time, source IDs, and headline IDs. |
| Background task status | Medium | Soon | Static MVP does not need it, but scheduled refresh and feed failures will. |
| File-backed artifacts | High | Yes | Our `india-headlines.js` is already a file-backed artifact; keep this simple. |
| Report/briefing sections | Medium | Soon | Once headline display works, add a daily brief summary artifact. |
| Source-to-entity extraction | Low now, high later | Later | Useful after we validate headline ingestion across sources. |
| Graph building | Low now | Later | Do not add a graph until we need dedupe, clustering, or story continuity. |
| Interactive Q&A | Low now | Later | Premature until sources and article text are captured reliably. |
| Heavy Flask/Vue app shell | Low | No | Current MVP is static; a server is not yet justified. |
| External memory/graph service | Low | No | Adds cost and operations before product need is proven. |
| AGPL source reuse | Not acceptable | No | Reference only. Reimplement patterns independently. |

## What We Should Take Immediately

### 1. Stronger Data Contract

MiroFish is disciplined about state. Our data file should become a stable contract before the UI grows.

Add or preserve these fields:

- `generatedAt`
- `editionDate`
- `region`
- `sources[]`
- `headlines[]`
- `headline.id`
- `headline.sourceId`
- `headline.title`
- `headline.url`
- `headline.publishedAt`
- `headline.category`
- `headline.priority`

Next useful additions:

- `fetchStatus`
- `sourceStatus[]`
- `duplicateOf`
- `sourceRank`
- `verifiedAt`
- `summary`

### 2. Source Refresh Reliability

MiroFish tracks long-running work. Our first version does not need a backend task system, but it does need refresh accountability.

Add next:

- per-feed success/failure output
- refresh summary JSON
- count of fetched, accepted, skipped, and errored items
- deterministic non-empty exit rules
- optional `--date YYYY-MM-DD`

This validates the product better than adding AI features.

### 3. Edition Artifact

Treat each daily run as an edition.

Recommended file shape:

```text
assets/data/editions/
  2026-04-22.json
  2026-04-23.json
assets/data/india-headlines.js
```

The `.js` file can remain the browser target. JSON edition files become the audit trail.

### 4. Briefing Artifact Later

Borrow MiroFish's report artifact idea, but keep it source-grounded and small.

Later daily brief sections:

- top headlines
- source coverage count
- category mix
- repeated story clusters
- source links

No speculative or synthetic social-environment sections.

## What We Should Not Take Yet

### Full Backend

Do not add Flask/FastAPI only because MiroFish has one. The MVP can validate usefulness without a server.

Backend becomes justified when we need:

- scheduled refresh
- persistent editions
- multiple users
- stored article text
- clustering across days
- authentication

### Graph System

Do not add Zep or any graph database in the current MVP. The next real product risk is not graph modeling; it is whether the source collection is reliable and useful.

Graph becomes justified when we need:

- dedupe same story across newspapers
- follow a story across days
- map entities and events
- show source disagreement

### AI Report Generation

Do not add AI report generation until we have reliable article text and source spans. A headline-only AI summary would look smart while being thin.

## MVP Roadmap Using Only Relevant MiroFish Patterns

### Stage 0: Current Static MVP

Status: built.

- Static board.
- Seeded data.
- RSS refresh script.
- Source/category/search filters.

### Stage 1: Reliable Headline Collector

Goal: prove we can refresh daily headlines without manual editing.

Requirements:

- Add more source feeds.
- Write JSON edition artifacts.
- Track source refresh status.
- Validate no empty output unless explicitly allowed.
- Add duplicate detection by normalized title and URL.

Success metric:

- One command produces at least 20 valid, linked headlines from at least 5 Indian sources on a normal news day.

### Stage 2: Editorial Scan Board

Goal: make the page useful for a person scanning today's India news.

Requirements:

- Add source status panel.
- Add sort by latest, source, category, priority.
- Add "lead only" toggle.
- Add "copied source link" affordance.
- Add empty/error states from refresh status.

Success metric:

- User can identify the top stories and open source links in under 2 minutes.

### Stage 3: Story Clustering

Goal: group duplicate or related headlines across sources.

Requirements:

- Normalize titles.
- Cluster by title similarity and repeated named terms.
- Show "covered by N sources."
- Keep source links visible.

Success metric:

- Repeated major stories appear as one cluster with multiple source links, not as scattered cards.

### Stage 4: Daily Brief Artifact

Goal: generate a source-grounded daily briefing from clustered headlines.

Requirements:

- Markdown daily brief.
- No unsupported claims.
- Every story cluster links back to sources.
- Category and source coverage summary.

Success metric:

- User can read a one-page brief and trace every item to original sources.

## Product Risks

### Risk 1: Source Coverage Is Too Thin

RSS feeds are inconsistent. Some newspapers may omit sections, publish delayed items, or block automated access.

Mitigation:

- Keep source status.
- Support manual seed fallback.
- Add feeds incrementally.
- Prefer official RSS or public section pages.

### Risk 2: Headline-Only Data Is Shallow

Headlines alone are not enough for serious analysis.

Mitigation:

- Treat headline board as MVP.
- Add article text extraction only after collection works.
- Mark headline-only artifacts clearly.

### Risk 3: Overbuilding From MiroFish

MiroFish's architecture can tempt us into graph, report, and interaction features too early.

Mitigation:

- Gate every borrowed pattern behind a product question.
- Do not add systems that do not improve daily headline collection or scanning.

## Final Product Decision

For the MVP, borrow **process patterns**, not platform architecture:

- Yes: state model, source status, edition artifacts, report artifact shape.
- Soon: task progress, daily briefing, clustering.
- Later: entity extraction, graph, source-grounded Q&A.
- No: copied code, AGPL assets, synthetic social-environment workflows, heavy services before validation.

The smallest valuable next step is **Stage 1: Reliable Headline Collector**.
