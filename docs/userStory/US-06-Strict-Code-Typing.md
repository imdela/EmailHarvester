# US-06: Strict Code Typing and PEP8 Reformatting

## Description
**As a** core maintainer of the project,
**I want** to enforce strict Python type hinting (`mypy`) and PEP8 style formatting (`ruff`),
**So that** the codebase achieves 100% static analysis compliance according to our `PYTHON_DEVELOPMENT_GUIDE.md`, eliminating ambiguity around input/output data flows and standardizing class naming.

## Acceptance Criteria
- **Given** the current legacy Python code,
- **When** `ruff check .` and `ruff format .` are executed,
- **Then** the codebase must pass all logical and stylistic linters consistently.
- **When** `mypy src/` is executed in `--strict` mode,
- **Then** no type-checking violations should be triggered.
- **And** legacy classes utilizing lowercase names (like `myparser`) must be explicitly refactored to conform to PascalCase conventions (e.g., `MyParser`).

## Technical Notes
- Apply type annotations (`-> str`, `list[dict]`, etc.) to every single method definition inside `EmailHarvester.py` and its plugins.
- Refactor identity operators where violated and rewrite non-compliant variable references.
- Setup `pyproject.toml` configurations for `ruff` and `mypy` locally to ensure tooling runs automatically with the correct boundaries.
