# US-07: Architectural Refactoring of the CLI Project

## Description
**As a** project architect,
**I want** to dismantle the monolithic `EmailHarvester.py` file into a separated modular file structure (`src/cli.py`, `src/core.py`),
**So that** the project strictly conforms to the Thin Controller CLI standard defined in our `PYTHON_DEVELOPMENT_GUIDE.md` and isolates command-line execution from unit-testable service logic.

## Acceptance Criteria
- **Given** the current flat monolithic file architecture (`EmailHarvester.py`),
- **When** executing the new refactor,
- **Then** all `argparse` definitions and terminal I/O logic must be extracted directly to `src/cli.py` (the "Thin Controller").
- **And** all core extraction loops, class definitions (`EmailHarvester`, `MyParser`), and proxy implementations must be extracted to `src/core.py`.
- **And** the `plugins/` directory should be effectively imported utilizing modern namespace resolution techniques rather than the legacy `__import__` OS-directory loops.
- **And** the `tests/` suite must pass cleanly against the newly isolated `core.py` directly.

## Technical Notes
- Do not let `EmailHarvester.py` manage its own data processing loop inside `if __name__ == "__main__":`.
- Rename `EmailHarvester.py` to `src/cli.py` and extract logic accurately.
- Avoid polluting `sys.path.*` logic if absolute/relative imports safely accomplish the same logic natively.
