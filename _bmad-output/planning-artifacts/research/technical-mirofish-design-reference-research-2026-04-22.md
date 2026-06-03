---
stepsCompleted: [1, 2]
inputDocuments:
  - https://github.com/666ghj/MiroFish
workflowType: research
lastStep: 2
research_type: technical
research_topic: MiroFish as architecture reference for newAgg
research_goals: Use MiroFish patterns to guide a source-grounded news intelligence project while excluding speculative and synthetic social-environment features
user_name: Havishakillo
date: 2026-04-22
web_research_enabled: true
source_verification: true
status: draft
---

# Research Report: Technical

**Date:** 2026-04-22  
**Author:** Havishakillo  
**Research Type:** Technical  

---

## Research Overview

This BMAD technical research note evaluates MiroFish as an external design reference for newAgg. The goal is to retain useful architecture patterns while rejecting speculative and synthetic social-environment features.

Research was verified against the public GitHub repository and selected source files. The repository is used as reference material only because it is licensed under AGPL-3.0.

## Technical Research Scope Confirmation

**Research Topic:** MiroFish as architecture reference for newAgg  
**Research Goals:** Use MiroFish patterns to guide a source-grounded news intelligence project while excluding speculative and synthetic social-environment features.

**Technical Research Scope:**

- Architecture Analysis - design patterns, backend/frontend boundaries, project state, task orchestration.
- Implementation Approaches - document ingestion, graph extraction, progress tracking, report generation.
- Technology Stack - languages, frameworks, tools, platforms visible in MiroFish.
- Integration Patterns - API boundaries, task polling, report artifact storage, source-bound follow-up.
- Performance Considerations - long-running task separation, incremental progress, local-first prototype path.

**Research Methodology:**

- Current public GitHub repository inspection.
- Source verification against README, package files, backend config, API modules, service modules, Docker Compose, and license.
- Confidence labels based on directly inspected files.
- Exclusion filter applied to keep newAgg focused on source-grounded news analysis.

**Scope Confirmed:** 2026-04-22

## Technology Stack Analysis

### Observed Stack In MiroFish

**Confidence: High.** Verified from `package.json`, `frontend/package.json`, `backend/pyproject.toml`, `.env.example`, `docker-compose.yml`, and backend source files.

- Frontend: Vue 3, Vite, Axios, D3, Vue Router, Vue i18n.
- Backend: Python Flask, Flask-CORS, pydantic, python-dotenv.
- LLM integration: OpenAI-compatible SDK configuration.
- Knowledge/memory graph: Zep Cloud.
- Additional source-project dependencies that are outside the newAgg MVP scope.
- File parsing: PyMuPDF, charset-normalizer, chardet.
- Dev orchestration: root npm scripts with `concurrently`.
- Deployment reference: Docker Compose exposes ports `3000` and `5001` and mounts backend upload data.

### Stack Elements Useful To newAgg

Use these ideas, not copied code:

- Root-level scripts for repeatable setup, backend start, frontend start, and full dev mode.
- Backend API split by domain: graph/project endpoints, long-running task endpoints, report endpoints.
- Environment-driven LLM configuration with an OpenAI-compatible client abstraction.
- Explicit upload and artifact directories.
- Frontend graph visualization library pattern for source/entity maps.
- Markdown report assembly and progress files.

### Stack Elements To Avoid For MVP

- Synthetic social-environment dependencies.
- Social platform environment runners.
- Synthetic actor orchestration.
- Heavy external graph dependency as a day-one requirement.
- Docker-first setup before a simple local app exists.

### Recommended newAgg Stack Direction

**Prototype path:**

- Backend: Python FastAPI or Flask.
- Store: SQLite first, with tables for projects, sources, chunks, entities, events, claims, edges, tasks, and reports.
- Jobs: in-process background tasks for prototype.
- Frontend: Vite app after the backend contract stabilizes.
- Reports: Markdown artifacts and structured JSON metadata.
- LLM: OpenAI-compatible adapter with strict source citation behavior.

**Scale-up path:**

- Postgres for multi-user and query durability.
- Background worker queue once ingestion/report tasks exceed in-process reliability.
- Graph database or Zep-like service only after local graph needs exceed relational tables.

## Architecture Patterns Analysis

### Source Intake And Project State

MiroFish creates a project around uploaded files and tracks derived artifacts. newAgg should do the same for news research workspaces.

Suggested project state:

- `project_id`
- `name`
- `analysis_goal`
- `source_items`
- `extracted_text_refs`
- `schema_version`
- `graph_ref`
- `briefing_refs`
- `status`
- `task_ids`
- `error`
- timestamps

### Async Task Contract

MiroFish treats graph building and preparation as background work with task status APIs. newAgg should standardize this early.

Suggested task response:

```json
{
  "task_id": "task_xxx",
  "status": "queued",
  "message": "Source extraction queued",
  "progress": 0,
  "result": null,
  "error": null
}
```

Suggested states:

- `queued`
- `processing`
- `completed`
- `failed`
- `cancelled`

### Document-To-Graph Analysis

MiroFish moves from documents to ontology to graph. newAgg should adapt this as a source-grounded news graph:

- Source extraction.
- Chunking with source span references.
- Entity extraction.
- Event extraction.
- Claim extraction.
- Source attribution.
- Relationship extraction.
- Timeline generation.
- Conflict/corroboration mapping.

### Report Generation

MiroFish report generation uses outline planning, per-section artifacts, progress tracking, JSONL logs, and final Markdown assembly.

newAgg briefing reports should use:

- `outline.json`
- `section_01.md`, `section_02.md`, etc.
- `progress.json`
- `source_map.json`
- `full_report.md`

Report sections:

- Executive summary.
- Key developments.
- Timeline.
- Entities and stakeholders.
- Source comparison.
- Conflicts or unresolved claims.
- Open questions.
- Source list.

### Interactive Follow-Up

MiroFish has interactive report/environment concepts. newAgg should only support source-grounded follow-up:

- Ask questions against known sources.
- Retrieve cited source chunks.
- Compare claims across sources.
- Explain ranking and importance.
- Show changes between briefings.

Responses must cite stored evidence and identify when the source set is insufficient.

## Exclusion Decisions

Do not implement speculative or synthetic social-environment workflows from the reference project.

Acceptable product language:

- "Analyze current evidence."
- "Compare source claims."
- "Track how a story developed."
- "Summarize what is known and unknown."
- "Map entities, events, and relationships."

## License Risk

MiroFish is AGPL-3.0. newAgg should keep the repository as reference-only material.

Rules:

- No source file copying.
- No adapted code snippets.
- No asset reuse.
- No branding reuse.
- License review before using AGPL dependencies directly.

## MVP Recommendation

Build a small source-grounded news intelligence MVP:

1. Project creation and source intake.
2. Text extraction and chunk storage.
3. Entity, event, claim, and date extraction.
4. Local graph projection in SQLite.
5. Briefing generation with citations.
6. Source-grounded Q&A.
7. Task status and progress endpoints.

## Source Links

- MiroFish repository: https://github.com/666ghj/MiroFish
- README: https://github.com/666ghj/MiroFish/blob/main/README.md
- Root package scripts: https://github.com/666ghj/MiroFish/blob/main/package.json
- Frontend package: https://github.com/666ghj/MiroFish/blob/main/frontend/package.json
- Backend dependencies: https://github.com/666ghj/MiroFish/blob/main/backend/pyproject.toml
- Backend config: https://github.com/666ghj/MiroFish/blob/main/backend/app/config.py
- Graph API: https://github.com/666ghj/MiroFish/blob/main/backend/app/api/graph.py
- Report agent: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/report_agent.py
- Docker Compose: https://github.com/666ghj/MiroFish/blob/main/docker-compose.yml
- License: https://github.com/666ghj/MiroFish/blob/main/LICENSE
