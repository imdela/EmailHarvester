# TI-09: Search Engine Rules Externalization (Rule 7)

## Description

Refactor the EmailHarvester engine to move hardcoded search parameters (URLs, pagination offsets, and display names) from individual plugin files into a centralized configuration file (`src/engines_config.yaml`). This alignment with Rule 7 ("Environment Variables via Schemas") ensures that search logic can be updated without modifying Python code, enhancing the tool's resilience to external search engine layout changes.

## Acceptance Criteria

- [ ] Add `PyYAML` and `types-PyYAML` to `requirements.txt`.
- [ ] Create `src/engines_config.yaml` containing the search rules for all 12 supported plugins.
- [ ] Update `src/core.py/EmailHarvester` to load and parse this YAML during initialization.
- [ ] Refactor all 12 plugins in `src/plugins/` to retrieve their configuration dynamically from the `harvester` instance instead of using hardcoded constants.
- [ ] Update unit tests to verify that the engine correctly handles missing or malformed configuration files.
- [ ] Ensure Mypy, Ruff, and Pytest remain 100% green.

---
**Status:** Open
