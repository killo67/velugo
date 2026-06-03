# Repository Guidelines

## Project Structure & Module Organization
This repository is currently lightweight and now includes the BMAD planning framework. Place application code under `src/`, tests under `tests/`, static assets under `assets/`, and utility scripts under `scripts/`. Keep configuration files at the repository root. BMAD-generated workflow assets live under `_bmad/`, generated planning and implementation artifacts live under `_bmad-output/`, and persistent project knowledge documents live under `docs/`.

Example structure:
```text
src/
tests/
assets/
scripts/
_bmad/
_bmad-output/
docs/
```

## Build, Test, and Development Commands
The current MVP is a dependency-free static page. No application build system is configured yet. BMAD is installed for planning and workflow support. When adding a fuller app stack, expose the common workflows through repeatable top-level commands and document them here.

Current MVP commands:
- Open `src/index.html` in a browser: view the static India headlines board
- `docker build -t newagg .`: build the production-style static container
- `docker run --rm -p 8080:80 newagg`: serve the static app at `http://localhost:8080`
- `python3 scripts/fetch_india_headlines.py`: refresh `assets/data/india-headlines.js` and `assets/data/editions/YYYY-MM-DD.json` from configured public RSS feeds
- `python3 scripts/fetch_india_headlines.py --date YYYY-MM-DD --allow-partial`: refresh a specific edition date and allow low-volume output during development
- `node --check src/app.js`: syntax-check the browser app script
- `node --check assets/data/india-headlines.js`: syntax-check the seeded data file
- `PYTHONPYCACHEPREFIX=/tmp/newagg-pycache python3 -m py_compile scripts/fetch_india_headlines.py`: syntax-check the refresh script without writing bytecode outside the workspace

Future command pattern:
- `npx bmad-method install --directory . --modules bmm --tools none --yes`: install or refresh the BMAD framework used by this repository
- `npm install` or `uv sync`: install dependencies
- `npm run dev` or `make dev`: run the local development entrypoint
- `npm test` or `pytest`: run the test suite
- `npm run lint` or `ruff check .`: run static checks

Prefer a single standard toolchain rather than mixing parallel setups.

## Coding Style & Naming Conventions
Use 2 spaces for Markdown, JSON, YAML, and frontend files; use 4 spaces for Python if Python is introduced. Prefer descriptive, lowercase directory names such as `src/api` or `assets/icons`. Use `camelCase` for JavaScript/TypeScript variables and functions, `PascalCase` for classes/components, and `snake_case` for Python modules and test files.

Adopt a formatter and linter early. Recommended defaults are `Prettier` and `ESLint` for JS/TS, or `ruff` plus `black` for Python.

## Testing Guidelines
Store tests in `tests/` or next to source files if the selected framework expects co-located tests. Name tests after the unit under test, for example `tests/test_parser.py` or `src/button.test.ts`. Add tests for new behavior and bug fixes before opening a PR. If coverage tooling is added, keep coverage stable or improving.

## Commit & Pull Request Guidelines
There is no Git history in this directory yet, so use clear imperative commit messages such as `Add initial API client` or `Set up test runner`. Keep commits focused on one change.

For pull requests, include:
- a short summary of what changed
- any setup or migration steps
- linked issue or task reference, if applicable
- screenshots or sample output for UI-facing changes

## Agent-Specific Notes
Do not introduce new tooling without updating this file. BMAD is currently installed with the `bmm` module and no IDE-specific integration. When the first real app stack is chosen, replace the placeholder command examples above with the exact commands used by this repository.
