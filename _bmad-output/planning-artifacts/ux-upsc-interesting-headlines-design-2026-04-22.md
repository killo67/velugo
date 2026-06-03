---
type: bmad-ux-design-recommendation
project: newAgg
feature: Interesting UPSC-aware headline news page
created: 2026-04-22
status: recommended
skill_used:
  - bmad-agent-ux-designer
  - bmad-create-ux-design guidance
input_artifacts:
  - _bmad-output/planning-artifacts/final-design-india-headline-mvp-2026-04-22.md
  - _bmad-output/planning-artifacts/product/upsc-ui-validation-2026-04-22.md
  - _bmad-output/planning-artifacts/final-prd-india-headline-mvp-2026-04-22.md
implementation_targets:
  - src/index.html
  - src/app.js
  - src/styles.css
  - scripts/fetch_india_headlines.py
---

# UX Design Recommendation - Interesting UPSC-Aware Headlines

## Design North Star

The page should feel like a calm study desk for the news cycle.

When an aspirant opens it, they should not feel buried under headlines. They should feel:

> "I know what is happening, what is worth studying, and where to verify it."

The design should still work as a general India headline board, but the first-class experience should help public-service exam aspirants find news with study value.

## Product Promise

Current promise:

> India Headlines

Recommended promise:

> Current Affairs Study Desk

Support line:

> Source-linked India headlines organized by relevance, syllabus area, and study value.

This keeps the product useful for any headline reader while making the main use case clearer.

## Design Principles

- **Interesting means useful, not loud.** Avoid clickbait styling. Make a headline interesting by showing why it matters.
- **Source first, study second.** The original source remains the trust anchor; study tags are aids, not facts.
- **Aspirants need triage.** The page should reduce decision fatigue by separating high-yield items from general updates.
- **No unsupported synthesis.** Until article text exists, use conservative rule-based labels and simple template explanations.
- **Readable under pressure.** Many users will check this during commute, between classes, or while revising.

## Recommended Page Structure

### 1. Topbar

Purpose:

- establish the product identity
- show freshness
- make it feel trustworthy

Content:

- `newAgg`
- `Current Affairs Study Desk`
- edition date and generated time
- compact status badge: `Ready`, `Partial`, or `Needs review`

Design:

- keep dark topbar
- reduce visual weight of "MVP"
- make timestamp readable but secondary

### 2. Study Snapshot

Purpose:

- answer "Is today's edition worth using?"

Metrics:

- study-worthy headlines
- source coverage
- topics covered
- failed sources

Example:

```text
12 study-worthy | 6 sources | 7 syllabus areas | 1 source failed
```

This replaces the generic "lead stories" idea with something more meaningful.

### 3. Today's Study Queue

Purpose:

- become the main reason to open the page

Position:

- immediately after the summary
- before source health

Content per card:

- headline
- source and time
- `Study priority`: High / Medium / Low
- `Exam use`: Prelims / Mains / Essay / Interview
- `Syllabus`: GS2, GS3, etc.
- `Topic tags`: Polity, Governance, Economy, Environment, IR, Security, Society
- `Why study`: one short conservative reason
- original source link

Example card:

```text
Karnataka High Court notice to State...
The Hindu · 8:20 PM

GS2 · Polity · Governance
Mains

Why study: touches public institutions, legal accountability, and state governance.
Open source
```

Important:

- `Why study` should be rule-based from tags.
- Do not claim article details the system has not read.

### 4. Topic Rail

Purpose:

- make exploration feel guided

Use chips/tabs:

- All
- Polity
- Governance
- Economy
- Environment
- IR
- Security
- Society
- Science & Tech
- Reports
- Schemes

Interaction:

- selecting a chip filters the study queue and headline board
- chips should show counts when possible

Example:

```text
Polity 4 | Economy 3 | Environment 2 | IR 1
```

### 5. General Headline Board

Purpose:

- preserve broad headline scanning

This section keeps the original grid but changes the label:

> All Collected Headlines

Each card should include:

- headline
- source/time
- topic tags if available
- source link
- low-key priority indicator

Avoid:

- making every headline look equally urgent
- using `Lead` unless editorially justified

### 6. Source Health Drawer Or Lower Section

Purpose:

- preserve transparency without taking over the first screen

Recommended behavior:

- show a compact status row near the top
- place detailed source cards below headlines or behind a "View source health" disclosure

Compact row:

```text
Sources: 5 ok, 1 failed · View details
```

Detailed source health can stay very close to the current implementation.

## Information Architecture

Recommended order:

1. Topbar
2. Study snapshot
3. Today's Study Queue
4. Topic rail and filters
5. All collected headlines
6. Source health details

This order matches the user's mental model:

1. Is this fresh?
2. What should I study?
3. What area does it belong to?
4. What else was collected?
5. Can I trust the sources?

## Visual Design Direction

Keep the restrained editorial utility style, but make the study layer warmer and more inviting.

Recommended palette:

- deep ink/navy for header and text
- teal for verified/source-grounded status
- amber for needs-attention/source-failure state
- blue for polity/governance tags
- green for environment
- violet or indigo for IR/security
- slate for neutral/general headlines

Use color as a small label accent, not as full-card decoration.

Cards:

- max 8px border radius
- no nested cards
- avoid heavy shadows
- use left-border or top-border accent for study priority
- keep headline text prominent

Typography:

- headline title: strong, readable, not oversized
- metadata: compact and secondary
- `Why study`: readable, plain language, no academic clutter

## Key Components

### Study Priority Badge

Labels:

- `High yield`
- `Useful`
- `General update`

Avoid:

- `Lead`, because it sounds editorial and currently means recency.

### Exam Use Badge

Labels:

- `Prelims`
- `Mains`
- `Essay`
- `Interview`

A headline can have multiple exam uses.

### Syllabus Chips

Labels:

- `GS1`
- `GS2`
- `GS3`
- `GS4`

Use only when rule-based mapping is reasonably confident.

### Why Study Line

Purpose:

- creates the "interesting" moment

Rules:

- one sentence only
- no more than 120 characters if possible
- must be derived from tags/keywords/source type, not article body assumptions

Examples:

- "Useful for governance and accountability themes."
- "Connects economy, agriculture, and external trade context."
- "Relevant to environment and decarbonisation policy."
- "Touches election institutions and political conduct."

### Source Trust Row

Purpose:

- keep source transparency available without dominating the page

Content:

- number of sources ok
- number failed
- generated time
- link/disclosure to details

## Interaction Design

### Primary Flow

1. User opens page.
2. Sees freshness and study snapshot.
3. Scans top study queue.
4. Filters by topic or GS paper.
5. Opens original source for items worth reading.
6. Checks source health only if something feels missing.

### Secondary Flow

1. User wants general news.
2. Skips study queue.
3. Uses All Collected Headlines.
4. Filters by source or search.

### Empty States

If no study-worthy items:

> No high-yield study items found yet. You can still scan all collected headlines below.

If sources failed:

> Some sources did not refresh. Study queue may be incomplete.

If a filter has no matches:

> No headlines match this topic yet.

## Data Needed

Add fields to each headline:

- `studyPriority`
- `upscTags`
- `gsPapers`
- `examUse`
- `whyStudy`
- `issueId` later

Add top-level fields later:

- `studyStatus`
- `topicCounts`
- `studyQueue`

Suggested MVP derivation:

- compute tags using deterministic keyword rules
- sort study queue by matched UPSC relevance, then recency
- keep all original headlines unchanged and source-linked

## Example First Screen

```text
newAgg
Current Affairs Study Desk
Edition 22 Apr 2026 · Updated 8:22 PM

12 study-worthy | 6 sources | 7 topics | 1 source failed

Today's Study Queue

[High yield] Karnataka High Court notice to State...
GS2 · Polity · Governance · Mains
Why study: touches legal accountability and state governance.
The Hindu · Open source

[High yield] 60 migrant workers from Odisha freed...
GS2 · Society · Social Justice · Mains
Why study: useful for labour rights and vulnerable groups.
The Hindu · Open source

Topics: All | Polity | Governance | Economy | Environment | IR | Society

All Collected Headlines
...

Source Health
5 ok · 1 failed
```

## Design Acceptance Criteria

- The first screen makes study value visible, not just headline volume.
- A user can identify at least 5 study-worthy items without reading every headline.
- Every study label is source-grounded and rule-explainable.
- Original source links remain prominent.
- Source health remains visible but not dominant.
- The page still works for general headline scanning.
- Mobile view keeps the study queue readable.
- No AI summaries or unsupported article claims appear.

## Recommended Next Implementation Story

Title:

> Add UPSC study queue and topic filters

Scope:

- add deterministic tagging rules in the collector
- emit study fields in headline payload
- change summary metrics to study snapshot
- render a top `Today's Study Queue`
- move detailed source health below the main headline experience
- add topic chips and GS paper filters

Out of scope:

- article body scraping
- LLM summary
- LLM wiki
- personalized saved notes

