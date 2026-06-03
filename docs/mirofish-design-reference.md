---
type: project-knowledge
topic: MiroFish design reference for newAgg
created: 2026-04-22
status: active-reference
source_repo: https://github.com/666ghj/MiroFish
use_policy: reference-only
---

# MiroFish Design Reference for newAgg

## Decision

Use MiroFish as a design reference for a news intelligence and analysis product. Do not copy source code, do not vendor the repository, and do not adopt its speculative or social-environment features.

The useful parts are workflow shape, task orchestration, document-to-graph processing, progress tracking, and report generation.

## Why This Reference Matters

newAgg currently has no application stack. MiroFish gives us a concrete example of how a document-driven AI system can move from raw materials to structured knowledge and then to an interactive report.

For our project, the equivalent flow should be:

1. Ingest source material: URLs, RSS entries, articles, PDFs, Markdown, or pasted text.
2. Extract normalized text and metadata.
3. Identify entities, events, dates, locations, organizations, claims, and source references.
4. Build a lightweight knowledge graph or relational graph projection.
5. Generate briefings with citations, uncertainty notes, source conflicts, and timeline context.
6. Support follow-up questions against the source set and extracted graph.

## Reference Architecture Observed

MiroFish uses a two-service app:

- Frontend: Vue 3, Vite, Axios, D3, Vue Router, Vue i18n.
- Backend: Python Flask, Flask-CORS, OpenAI-compatible LLM calls, Zep Cloud, file parsing, and background task state.
- Dev orchestration: root `package.json` runs backend and frontend with `concurrently`.
- Deployment reference: Docker Compose publishes frontend and backend ports and mounts backend uploads.

Important source files inspected:

- `README.md`: public workflow and setup.
- `package.json`: root orchestration scripts.
- `frontend/package.json`: frontend stack.
- `backend/pyproject.toml`: backend dependencies.
- `backend/app/config.py`: environment and upload configuration.
- `backend/app/api/graph.py`: project, ontology, graph build, task, and graph data APIs.
- Backend long-running task APIs: task status and progress patterns.
- Backend file-backed state services: state model and progress-aware preparation flow.
- `backend/app/services/report_agent.py`: report outline, section generation, progress files, Markdown assembly, and JSONL logs.
- `LICENSE`: AGPL-3.0.

## Reusable Patterns

### Project State Model

MiroFish keeps a persistent project concept with uploaded files, extracted text, generated ontology, graph ID, status, task IDs, and errors.

newAgg should use a similar state model:

- `project_id`
- `name`
- `source_items`
- `extracted_text_refs`
- `analysis_goal`
- `entity_schema`
- `graph_ref`
- `status`
- `task_ids`
- `created_at`
- `updated_at`
- `error`

### Background Task Progress

MiroFish exposes long-running operations as tasks with status, message, progress, and result. This is valuable for ingestion, extraction, graph building, and briefing generation.

newAgg should standardize task states:

- `queued`
- `processing`
- `completed`
- `failed`
- `cancelled`

Every long-running endpoint should return a task ID immediately and expose a polling endpoint.

### Document-to-Graph Pipeline

MiroFish first generates an ontology, then chunks documents, then builds a graph. For newAgg, the same pattern should become source-grounded news analysis:

- Text extraction and cleanup.
- Entity extraction.
- Event extraction.
- Claim extraction.
- Source attribution.
- Relationship extraction.
- Timeline construction.
- Conflict and corroboration detection.

Start with a local store before adding an external graph service.

### Report Generation

MiroFish generates an outline, writes sections, logs agent activity, tracks progress, and assembles Markdown.

newAgg should reuse the concept, but target news briefings:

- Executive summary.
- Key developments.
- Timeline.
- Stakeholders.
- Source comparison.
- Open questions.
- Confidence and uncertainty notes.
- Source list.

### Interactive Follow-Up

MiroFish supports interaction with generated report and environment state. newAgg should adapt that to source-grounded Q&A:

- Ask questions against a project.
- Retrieve cited source spans.
- Compare claims across sources.
- Explain why a story is ranked as important.
- Show what changed since the last briefing.

## Excluded Scope

Do not implement speculative or synthetic social-environment workflows from the reference project.

Acceptable alternatives:

- Source-grounded analysis.
- Evidence-grounded summaries.
- Timeline reconstruction.
- Source conflict mapping.
- Stakeholder and entity mapping.
- Risk and uncertainty labeling based on current evidence.

## License And Adoption Rules

MiroFish is AGPL-3.0. Treat it as reference material only.

Rules for newAgg:

- Do not copy MiroFish source files.
- Do not paste modified MiroFish code into this repository.
- Do not use its UI assets, images, or branding.
- Reimplement any chosen pattern independently.
- Keep source citations in planning documents when referencing MiroFish.
- Review licensing before using any AGPL dependency directly.

## Recommended MVP Direction

Build a smaller, source-grounded system:

1. `Source Intake`: save URL/text/PDF inputs with metadata.
2. `Extraction`: parse text and chunk it with source span references.
3. `Analysis Schema`: extract entities, events, claims, dates, and source links.
4. `Local Graph`: store nodes and edges in SQLite/Postgres tables first.
5. `Briefing Generator`: produce Markdown/HTML reports with citations.
6. `Ask Project`: answer follow-up questions only from stored source evidence.
7. `Task Progress`: expose status for intake, extraction, graph build, and briefing.

## Candidate Stack

Keep the first stack conservative:

- Backend: Python FastAPI or Flask.
- Storage: SQLite for prototype, Postgres when multi-user or heavier querying is needed.
- Jobs: in-process background tasks first, then RQ/Celery if needed.
- Frontend: Vite with React or Vue, chosen once product direction is clearer.
- Documents: Markdown reports under `docs/` or generated artifacts under `_bmad-output/implementation-artifacts`.
- LLM: OpenAI-compatible client wrapper with explicit citation and source-bound response rules.

## Next BMAD Steps

1. Product brief: define who newAgg serves and what briefing workflow matters first.
2. PRD: specify source intake, briefing, graph extraction, and Q&A behavior.
3. Architecture: choose backend/frontend/store and define task/status contracts.
4. Epics and stories: split MVP into source intake, extraction, graph, report, and Q&A.

## Sources

- MiroFish repository: https://github.com/666ghj/MiroFish
- README: https://github.com/666ghj/MiroFish/blob/main/README.md
- Root package scripts: https://github.com/666ghj/MiroFish/blob/main/package.json
- Frontend package: https://github.com/666ghj/MiroFish/blob/main/frontend/package.json
- Backend dependencies: https://github.com/666ghj/MiroFish/blob/main/backend/pyproject.toml
- Backend config: https://github.com/666ghj/MiroFish/blob/main/backend/app/config.py
- Graph API: https://github.com/666ghj/MiroFish/blob/main/backend/app/api/graph.py
- Report agent: https://github.com/666ghj/MiroFish/blob/main/backend/app/services/report_agent.py
- License: https://github.com/666ghj/MiroFish/blob/main/LICENSE
