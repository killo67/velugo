---
type: bmad-product-validation
project: newAgg
feature: UPSC-focused India headline board
created: 2026-04-22
status: validation-complete
review_inputs:
  - http://localhost:8080
  - assets/data/india-headlines.js
  - src/index.html
  - src/app.js
  - scripts/fetch_india_headlines.py
persona:
  - UPSC/public-service-exam aspirant
  - wants latest India news worth studying
  - needs source-grounded relevance, not unsupported AI claims
method:
  - BMAD PM lens
  - parallel agent review
  - local container smoke check
---

# UPSC UI Validation - newAgg

## PM Decision

The current UI is **useful as a transparent headline collection and source-health board**, but it is **not yet useful enough for a UPSC aspirant's daily study workflow**.

Why: a UPSC aspirant is not just asking "what happened latest?" They are asking:

- What should I study today?
- Which headline maps to polity, governance, economy, environment, IR, security, or society?
- Is this useful for Prelims, Mains, Essay, or Interview?
- Why should I care enough to open the source?
- Is this a one-off headline or part of an ongoing issue?

The current product answers source trust and freshness reasonably well. It does not yet answer study relevance.

## What Works

- Static production container is serving the app at `http://localhost:8080`.
- Source health is visible.
- Feed failures are transparent.
- Headlines preserve original source links.
- Source policy metadata is present.
- The app avoids AI summaries and unsupported claims.

This is a good foundation. The collection layer is becoming trustworthy.

## Major Gaps For UPSC Use

### P0 - Priority Labels Are Misleading

Current `Lead`, `High`, and `Medium` labels are assigned by recency/order, not exam relevance.

For UPSC, latest does not always mean high-yield. A board result or hyperlocal political item can outrank a governance, constitutional, economy, environment, or international-relations issue.

Decision:

- Replace current priority labels with UPSC relevance labels.
- Do not call something `Lead` unless the reason is transparent and source-grounded.

### P0 - Headline Cards Do Not Explain Study Value

Current cards show:

- category
- priority
- title
- source
- time

Missing study fields:

- `whyStudy`
- `upscTags`
- `gsPaper`
- `examUse`
- `prelimsHook`
- `mainsAngle`
- `entities`
- `issueId`

Decision:

- Add a study-card layer before adding more UI polish.

### P1 - Generic Categories Are Too Weak

Most current items use category `India`, which does not help a candidate triage.

UPSC-native filters should include:

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

Decision:

- Replace or supplement generic categories with exam-oriented tags.

### P1 - Source Health Uses Prime Space

Source health is important for trust, but the aspirant's first job is study selection.

Decision:

- Keep source health visible, but collapse it or move it below a "Today's Study Queue" section.
- Top of page should help answer: "What should I study today?"

### P1 - No Issue Clustering

UPSC value comes from issues, not isolated headlines. Current dedupe removes exact repeats but does not group related stories.

Examples from current data that could become issue threads:

- Election Commission and political conduct
- bonded labour and migrant workers
- decarbonisation efforts
- West Asia diplomacy
- state governance and public institutions

Decision:

- Add lightweight issue clustering after basic UPSC tagging exists.

### P1 - Source Mix Is Not UPSC-Complete

Newspaper headlines are useful, but UPSC preparation also depends on primary/reference sources.

Potential future sources:

- PIB
- PRS
- RBI
- Supreme Court/constitutional court updates
- Election Commission of India
- Ministries and departments
- Down To Earth for environment
- ORF/IDSA-style explainers for IR/security, if clearly classified as analysis/reference

Decision:

- Keep newspapers as the foundation.
- Add official/reference public sources in a separate source type later.

## Usefulness Score

For current general headline scanning:

- **7/10**

For UPSC daily study:

- **3/10**

Reason: source trust is present, but exam relevance, syllabus mapping, and study workflow are missing.

## Recommended Product Pivot

Change the product promise from:

> India Headlines

to:

> UPSC Current Affairs Study Queue

The raw headline board can remain, but the primary experience should become a ranked, source-grounded study queue.

## Proposed Next MVP Slice

Title: Add UPSC relevance tagging and study queue

Goal:

Help an aspirant identify which collected headlines are worth studying today.

Scope:

- Add deterministic keyword-based UPSC tagging in the collector.
- Add fields:
  - `upscTags`
  - `gsPaper`
  - `examUse`
  - `studyPriority`
  - `whyStudy`
- Replace visible `Lead/High/Medium` with study-oriented priority.
- Add filters for GS paper and UPSC tag.
- Add a top "Today's Study Queue" section before source health.

Validation:

- Every study tag must be explainable from the headline/source metadata.
- No generated factual claim beyond source headline/link.
- Study reasons must be template-based and conservative.
- Users can filter by GS paper/tag.

## Guardrail

Do not use LLM inference for UPSC relevance until article text or source excerpts exist.

For now, use conservative rule-based tagging so the system stays auditable.

## Final Recommendation

Proceed with the current containerized static stack, but shift the product design toward UPSC study relevance.

The next feature should not be more sources or prettier cards. It should be:

- syllabus tagging
- study relevance
- exam-use filters
- "why study this" based on deterministic rules

