# Antigravity Design Guidelines - Aspirant-Friendly Headline Experience

## Product Direction

Design the page as a **Current Affairs Study Desk**: a fast, source-linked headline experience that makes people curious enough to open the original story and smart enough to know why it matters.

The product should work for:

- UPSC aspirants
- state public service aspirants
- SSC/banking/railway exam aspirants
- general readers who want important India news without noise

The page should not feel like a coaching-note dump. It should feel like a clean news desk with study intelligence layered on top.

## Core User Promise

> See the latest India headlines, understand why they matter, and decide what to study next.

Secondary promise:

> Every item links back to the original public source.

## Design North Star

When a user opens the page, they should feel:

> "I can quickly see what happened, what is worth knowing, and what is worth studying."

Avoid making the user do all the mental work of sorting raw headlines.

## Primary Experience

The current page should evolve from a generic headline grid into a guided headline experience.

Recommended page order:

1. Topbar
2. Daily insight summary
3. Today's must-know headlines
4. Topic filters
5. All collected headlines
6. Source health

This order matters. Users first need value, then controls, then operational details.

## Page Sections

### 1. Topbar

Purpose:

- Establish trust and freshness.
- Make the product feel like a current affairs desk, not a raw feed.

Recommended content:

- Brand: `newAgg`
- Page title: `Current Affairs Study Desk`
- Subtitle: `Source-linked India headlines for news-aware aspirants`
- Edition timestamp
- Compact status badge: `Ready`, `Partial`, or `Needs review`

Avoid:

- large marketing hero
- generic "India Headlines" only
- claiming full article understanding

### 2. Daily Insight Summary

Purpose:

- Give users the edition health and usefulness at a glance.

Recommended metrics:

- `Study-worthy`: count of headlines with useful tags
- `Sources`: successful source count
- `Topics`: number of topic areas covered
- `Needs review`: failed source count or low-confidence count

Example:

```text
14 study-worthy · 5 sources · 8 topics · 1 source needs review
```

Use this instead of only showing `24 headlines`, because raw volume is not the main value.

### 3. Today's Must-Know Headlines

Purpose:

- Make the page interesting immediately.
- Help users decide what to open first.

This should be the main section.

Each card should show:

- headline title
- source and time
- study priority
- topic tags
- exam usefulness
- short `Why it matters` line
- original source link

Example:

```text
High-yield
Karnataka High Court notice to State...

GS2 · Polity · Governance · Mains
Why it matters: useful for legal accountability and state governance themes.

The Hindu · Open source
```

Important:

- The `Why it matters` line must be conservative.
- It should be based on deterministic tags/keywords, not AI assumptions.
- Keep it one sentence.

Recommended card priority labels:

- `High-yield`
- `Useful`
- `General update`

Avoid:

- `Lead`, unless there is a real editorial or rule-based reason
- dramatic labels like `Breaking` unless source metadata supports it
- unsupported summary text

### 4. Topic Filters

Purpose:

- Let users browse by study interest.

Recommended filters:

- All
- Polity
- Governance
- Economy
- Environment
- International Relations
- Internal Security
- Society
- Social Justice
- Science and Technology
- Geography
- Culture
- Reports and Indices
- Schemes

Also support exam-use filters:

- Prelims
- Mains
- Essay
- Interview

And optional GS filters:

- GS1
- GS2
- GS3
- GS4

Design:

- Use chips or segmented controls.
- Show counts where possible.
- Keep filters sticky or near the top on mobile only if it does not crowd the page.

### 5. All Collected Headlines

Purpose:

- Preserve broad news browsing.
- Keep the product useful for users who do not want exam filtering.

Cards here can be simpler:

- headline
- source
- published time
- topic tags if available
- source link

This section can reuse the current headline grid but should feel secondary to the must-know section.

### 6. Source Health

Purpose:

- Preserve transparency.
- Show whether missing coverage is a collection issue.

Move detailed source health below the main headline experience or put it behind a disclosure:

```text
Source health: 5 ok, 1 failed · View details
```

Detailed source card fields:

- source name
- status
- source type
- section
- accepted count
- skipped count
- duplicate count
- error or policy note

Source health is important, but it should not be the first emotional moment of the page.

## Visual Style

Use a restrained editorial-study style.

The app should feel:

- trustworthy
- calm
- focused
- readable
- slightly academic, but not dull

Recommended visual treatment:

- dark header for identity
- white cards on light background
- 8px border radius maximum
- subtle borders, not heavy shadows
- small colored tag accents
- no large decorative gradients
- no stock imagery
- no marketing hero

Color suggestions:

- Navy/ink: primary text and header
- Teal: verified/source-grounded states
- Amber: warnings/source issues
- Blue: polity/governance
- Green: environment
- Indigo: IR/security
- Slate: general/neutral

Use color only as a label accent, not as full-card decoration.

## Typography

Headlines should be the visual hero.

Recommended hierarchy:

- Page title: strong, compact
- Section headings: clear and restrained
- Headline title: prominent, readable
- Metadata: smaller and muted
- `Why it matters`: readable, plain, not tiny

Avoid:

- giant headline text that makes scanning slow
- dense coaching-note paragraphs
- negative letter spacing
- viewport-scaled font sizes

## Interaction Guidelines

### Opening A Story

Primary action:

- click headline or `Open source`

Behavior:

- opens original source in new tab
- preserve source trust

### Filtering

Topic chips should filter both:

- Today's must-know section
- all collected headlines

Search should match:

- headline title
- source
- topic tags
- exam use
- GS paper

### Empty States

No high-yield stories:

```text
No high-yield study items found yet. You can still scan all collected headlines below.
```

Source failures:

```text
Some sources did not refresh. Today's study queue may be incomplete.
```

No filter matches:

```text
No headlines match this topic yet.
```

## Data Fields To Support The Design

Each headline should eventually include:

```json
{
  "studyPriority": "High-yield",
  "upscTags": ["Polity", "Governance"],
  "gsPapers": ["GS2"],
  "examUse": ["Mains"],
  "whyStudy": "Useful for legal accountability and state governance themes.",
  "issueId": "state-governance-accountability"
}
```

Top-level data can include:

```json
{
  "studyStatus": "ready",
  "topicCounts": {},
  "studyQueue": []
}
```

For now, these should be derived through deterministic keyword rules.

Do not use LLM-generated claims until article text or excerpts are collected with citations.

## Rule-Based Relevance Guidance

Use headline keywords and source metadata to assign conservative tags.

Examples:

Polity/Governance:

- court
- Supreme Court
- High Court
- Election Commission
- Parliament
- Bill
- law
- policy
- governor
- federal
- constitutional

Economy:

- RBI
- inflation
- GDP
- trade
- exports
- budget
- tax
- jobs
- agriculture economy

Environment:

- climate
- pollution
- forest
- wildlife
- heatwave
- decarbonisation
- renewable
- river

Society/Social Justice:

- labour
- migrant
- caste
- women
- education
- health
- poverty
- vulnerable groups

International Relations:

- diplomacy
- border
- West Asia
- China
- Pakistan
- treaty
- global
- peace talks

Internal Security:

- terrorism
- insurgency
- border security
- cybercrime
- smuggling
- police reform

Science and Technology:

- space
- AI
- digital
- biotechnology
- research
- satellite
- semiconductor

Keep uncertain items as `General update`.

## What Not To Do

Do not:

- write AI summaries from headline-only data
- imply the app read article bodies
- invent relevance beyond visible data
- over-prioritize recency
- make source health dominate the first screen
- make every headline look equally important
- hide original source links
- turn the page into a coaching-notes wall

## Mobile Design

Mobile is important because aspirants may check headlines while commuting or between study sessions.

Mobile layout:

1. Topbar
2. Study snapshot
3. Topic chips horizontal scroll
4. Must-know cards
5. All headlines
6. Source health disclosure

Cards should be single column.

Avoid:

- three-column layouts on small screens
- long metadata rows that overflow
- tiny tags that are hard to tap

## Success Criteria

The design is successful if:

- a user can identify important stories in under 30 seconds
- a user can understand why a story may matter
- every item still links to the source
- source failures are visible but not distracting
- general readers can still browse all headlines
- aspirants can filter by topic or exam use
- no unsupported claims appear

## Suggested First Implementation Slice

Build this first:

1. Add rule-based tags and study fields in the collector.
2. Add a `Today's Must-Know` section above the headline grid.
3. Add topic chips.
4. Move detailed source health lower.
5. Replace `Lead/High/Medium` with `High-yield/Useful/General update`.

Keep everything static and dependency-free.

## One-Screen Target

The first screen should roughly feel like this:

```text
newAgg
Current Affairs Study Desk
Edition 22 Apr 2026 · Updated 8:22 PM · Ready

14 study-worthy · 5 sources · 8 topics · 1 source needs review

Today's Must-Know

[High-yield] Karnataka High Court notice to State...
GS2 · Polity · Governance · Mains
Why it matters: useful for legal accountability and state governance themes.
The Hindu · Open source

[Useful] Chittoor's mango economy in crisis...
GS3 · Economy · Agriculture · Mains
Why it matters: connects agriculture, trade, and regional economy.
The Hindu · Open source

Topics: All | Polity | Governance | Economy | Environment | IR | Society

All Collected Headlines
...
```

That is the experience to aim for.
