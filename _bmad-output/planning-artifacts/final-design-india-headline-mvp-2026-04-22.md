---
type: final-product-design
project: newAgg
feature: India Headline MVP
date: 2026-04-22
status: final
paired_prd:
  - _bmad-output/planning-artifacts/final-prd-india-headline-mvp-2026-04-22.md
implementation_artifacts:
  - src/index.html
  - src/app.js
  - src/styles.css
---

# Final Design - newAgg India Headline MVP

## Design Intent

newAgg should feel like a fast, trustworthy headline board rather than a content site or AI briefing. The design should help users answer three questions quickly:

- What India headlines were collected?
- Which sources contributed?
- Can I verify the original source?

The page should favor clarity, source transparency, and scan speed.

## Experience Principles

- Source-first: every headline links to its original public source.
- Transparent: source failures and low accepted counts are visible.
- Lightweight: no app chrome, accounts, onboarding, or marketing page.
- Grounded: no AI-written summaries or unsupported interpretations.
- Reader-friendly: filters and search make scanning efficient.

## Information Architecture

The first screen should contain:

1. Header
   - product label
   - page title
   - edition timestamp

2. Summary band
   - headline count
   - configured source count
   - lead count

3. Source health
   - per-source status
   - source type
   - section
   - India scope
   - free-online status
   - accepted/fetched/skipped/duplicate counts
   - error or policy note

4. Filters
   - source select
   - category select
   - headline search

5. Headline grid
   - category pill
   - priority pill
   - headline link
   - source and publication time

## Visual Direction

Use a restrained editorial utility style:

- dark topbar for strong page identity
- white surfaces on a light page background
- teal accent for successful/source-grounded state
- amber warning accent for failed or attention-needed state
- 8px radius maximum for cards and controls
- dense but readable spacing
- no decorative illustration, no gradient hero, no marketing section

The MVP should look more like a source monitor plus headline board than a magazine homepage.

## Layout

Desktop:

- max-width content column around 1180px
- three-column summary band
- three-column source health grid
- three-column headline grid
- filter toolbar with source/category/search columns

Mobile:

- stacked header
- one-column summary band
- one-column source health cards
- one-column toolbar
- one-column headline list

## Components

### Topbar

Purpose: identify the product and edition freshness.

Content:

- `newAgg MVP`
- `India Headlines`
- edition date and generated timestamp

### Summary Band

Purpose: quick edition health.

Metrics:

- headlines
- sources
- lead stories

### Source Health Card

Purpose: make collection quality visible.

Fields:

- source name
- status pill: `OK` or `Error`
- source metadata line
- accepted/fetched/skipped/dupes counters
- policy note or error message

Design behavior:

- success state uses teal left border
- error state uses amber left border
- long errors wrap rather than overflow

### Filter Toolbar

Purpose: narrow the headline board without hiding source trust details.

Controls:

- source select
- category select
- search input

### Headline Card

Purpose: scan and open original source.

Fields:

- category pill
- priority pill
- linked headline title
- source and published time

Behavior:

- click headline opens original source in a new tab
- hover/focus underlines headline link

## Content Rules

- Do not imply the app has read full article bodies.
- Do not summarize articles.
- Do not label stories as important using model judgment.
- Use "source", "feed", "edition", and "public source" language.
- Make source policy notes visible when a source is not a strict newspaper.

## Accessibility

- Use semantic sections with aria labels.
- Keep source health content as text, not icons alone.
- Preserve visible focus states through browser defaults and link underline.
- Avoid text overlap by allowing wrapping and responsive one-column layouts.

## Design Acceptance Criteria

- Source health is visible before filters and headlines.
- A failed source is visually distinguishable.
- Non-newspaper source classification is visible in the source health card.
- The page remains usable on mobile widths.
- Headline links clearly open the original source.
- No AI/wikilike synthesis appears in the UI.

## Future Design Extensions

Possible later additions:

- sort control for latest/source/category
- lead-only toggle
- multi-source coverage badge after story clustering exists
- source-only view
- stale edition warning

Avoid until article text exists:

- generated daily brief
- generated story explanation
- entity pages
- LLM wiki pages

