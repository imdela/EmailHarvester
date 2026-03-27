# TI-12: Snake Case Standardization (Rule 124-135)

## Description

Refactor the entire codebase to replace legacy `camelCase` nomenclature with Pythonic `snake_case`. This includes variable names, function names, and method names across `core.py`, `cli.py`, and all plugins. This ensures 100% compliance with the modernized `PYTHON_DEVELOPMENT_GUIDE.md` and PEP 8 standards.

## Acceptance Criteria

- [ ] Refactor `EmailHarvester` class properties:
    - `userAgent` -> `user_agent`
    - `tor_enabled` (already snake)
    - `activeEngine` -> `active_engine`
    - `burst_count` (already snake)
    - `totalresults` -> `total_results`
- [ ] Refactor `EmailHarvester` methods:
    - `init_search` (already snake)
    - `do_search` (already snake)
    - `get_emails` (already snake)
    - `_visit_deep_link` (already snake)
    - `genericClean` -> `generic_clean` in `MyParser`
- [ ] Update `cli.py` to match the new property names.
- [ ] Ensure all functional tests pass after the rename.
- [ ] Zero linting errors related to N802/N803/N816 (Ruff).

---
**Status:** BACKLOG
