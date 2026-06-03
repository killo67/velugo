---
type: bmad-research-decision
topic: LLM wiki usefulness for newAgg
created: 2026-04-22
project: newAgg
status: final
input_context:
  - MVP aggregates India news headlines that are interesting for readers
  - scope is India news from free online newspapers
  - source of truth is the newspaper, not model memory or model inference
related_artifacts:
  - _bmad-output/planning-artifacts/prd-stage-1-reliable-headline-collector.md
  - _bmad-output/planning-artifacts/architecture-stage-1-reliable-headline-collector.md
  - assets/data/editions/2026-04-22.json
  - scripts/fetch_india_headlines.py
decision: do-not-use-llm-wiki-for-headline-mvp
---

# LLM Wiki Fit Analysis For newAgg

## Decision

Do **not** use an LLM wiki for the current headline MVP.

An LLM wiki is useful later as a source-grounded story memory layer, but it is premature for a dependency-free India headline board. The current MVP needs stronger newspaper source discipline, auditable feed collection, source status, deduplication, and reader-facing scanning controls before it needs generated wiki pages.

## What LLM Wiki Means Here

Based on Karpathy's LLM Wiki gist and related public LLM Wiki descriptions checked on 2026-04-22, the pattern means an LLM incrementally maintains a structured wiki from immutable raw sources. Common pieces are:

- raw sources that remain the source of truth
- generated Markdown/wiki pages
- wiki links across entities, topics, sources, and claims
- source traceability
- contradiction and gap detection
- persistent knowledge that grows across ingest runs

This is different from asking an LLM to summarize headlines once. It is closer to an auditable research vault.

## Fit Against MVP Needs

### Need: Interesting India Headlines

Fit: **Low for Stage 1**

The product can make the board more interesting without an LLM wiki by using source-grounded signals:

- recency from `publishedAt`
- source diversity across newspapers
- repeated coverage across multiple newspapers
- India-only section/feed selection
- category diversity if supplied by the source or configured source section
- explicit source labels when available in the feed
- visible source status so the reader knows what was and was not collected

The product should **not** ask an LLM to decide what is interesting from headline text alone unless the result is clearly labeled as an editorial ranking aid and every reason points back to source metadata or cited article text.

### Need: Newspaper As Source Of Truth

Fit: **Low until article text or excerpts exist**

The current collector stores headlines, URLs, source names, feed URLs, and timestamps. That is enough to build a reliable scan board, but not enough to support claim-level wiki pages. A wiki page would be tempted to infer context from model memory, which conflicts with the rule that the newspaper is the source of truth.

### Need: Free Online Newspapers Only

Fit: **No special value**

LLM wiki does not solve source eligibility. BMAD should handle that as a source policy and implementation requirement:

- only use public, free, official newspaper RSS feeds or public newspaper section pages
- prefer India/national section feeds, not generic latest feeds
- avoid sources that require login, subscription, private APIs, scraping workarounds, or unclear redistribution rights
- preserve the original newspaper URL for every headline

Current source list note: NDTV is a news publisher but not a newspaper. Business Standard's current configured feed is a generic latest feed and returned `403` in the seeded artifact. If the product requirement is strictly "newspapers," BMAD should either replace these sources or classify them separately.

## Stage Recommendation

### Stage 1: Reliable Headline Collector

Decision: **Do not use LLM wiki.**

Implement:

- official free online newspaper source registry
- India-only feed validation
- source status panel
- conservative dedupe
- edition JSON archive
- reader scan controls

Reject:

- LLM-generated summaries
- LLM-generated wiki pages
- vector database
- graph database
- hosted knowledge platform

### Stage 2: Reader Scan Board

Decision: **Still defer LLM wiki.**

Useful work:

- source health and freshness indicators
- "covered by multiple newspapers" grouping
- sort by latest/source/category
- show source diversity
- highlight stale or failed sources

These features need metadata, not an LLM wiki.

### Stage 3: Story Clustering

Decision: **Consider wiki-shaped artifacts, but no LLM wiki requirement.**

When several newspapers cover the same story, the product can create source-linked story clusters:

```text
assets/data/stories/YYYY-MM-DD.json
```

Each story cluster should list only observed facts from collected metadata:

- headline titles
- source names
- source URLs
- published times
- cluster reason, such as same canonical URL, same normalized title, or high title similarity

No unsupported story explanation should be generated.

### Stage 4: Article Text Or Source Excerpts

Decision: **LLM wiki becomes useful here.**

Only adopt the pattern once newAgg stores article text, excerpts, or quote spans with stable citations. Then wiki pages can help readers follow ongoing stories across days.

Possible structure:

```text
raw/
  articles/YYYY-MM-DD/
wiki/
  sources/
  stories/
  entities/
  daily-briefs/
  log.md
```

Minimum claim metadata:

- newspaper name
- article URL
- article/headline ID
- publication time
- collection time
- source span or quote boundary
- generated page timestamp

## Guardrails If LLM Wiki Is Later Adopted

- Newspaper articles remain the source of truth.
- Raw source artifacts are immutable.
- Every generated claim must cite a source URL.
- Once article text exists, every generated claim must cite a source span.
- If collected sources do not support a claim, the wiki must say "not found in collected sources."
- Generated pages must be labeled as analysis, not source material.
- The LLM must not fill gaps using memory.
- Contradictions must be shown as source disagreement, not resolved by model judgment.
- User-facing summaries must link back to original newspaper pages.

## BMAD Skill Guidance

### PM

Treat LLM wiki as a future "story memory" capability, not an MVP feature. Tighten the Stage 1 PRD around:

- strict source eligibility: free online Indian newspapers
- India-only section/feed requirement
- source freshness and source failure visibility
- reader value from scanability, not AI synthesis

### Architect

Keep Stage 1 static and file-based. Do not introduce a database, vector store, graph store, hosted wiki, or LLM pipeline. Add only metadata that future stages can reuse:

- `sourceType`
- `section`
- `countryScope`
- `isFreeToRead`
- `sourcePolicyNotes`

### UX Designer

Use source-grounded reader affordances:

- latest first
- newspaper/source filters
- source health panel
- multi-source coverage badges
- category or region filters only when backed by source/config metadata

Avoid user-facing text that implies the app has read article bodies if it has only collected headlines.

### Dev

Prioritize collector correctness:

- replace or reclassify non-newspaper sources if strict newspaper scope is confirmed
- avoid generic feeds when India/national feeds exist
- preserve source URLs and feed URLs
- record collection errors in artifacts
- keep generated artifacts auditable and human-readable

### QA

Validate against source truth:

- every headline title must come from the feed/source, not model generation
- every URL must point to the original newspaper article
- date filtering must use Asia/Kolkata
- non-India or generic-feed leakage should be caught
- source failures must be visible rather than silently ignored

## Final Recommendation

LLM wiki is **not useful for this MVP** because the MVP currently collects headline metadata, not article-level evidence. It becomes useful later if the product evolves into a source-grounded India news intelligence tool with article text, source spans, story continuity, and contradiction tracking.

For now, BMAD should decide toward:

- India-only free online newspaper sources
- auditable source-linked headline collection
- source health and scanability
- no generated claims beyond the newspaper-provided data

## Sources Consulted

- LLM Wiki app overview: https://llmwiki.app/
- Karpathy LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- nashsu LLM Wiki repository: https://github.com/nashsu/llm_wiki
- LLM Wiki pattern document: https://github.com/nashsu/llm_wiki/blob/main/llm-wiki.md
