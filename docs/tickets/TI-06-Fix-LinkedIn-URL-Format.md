# TI-06: Standardize Search URL Placeholders

## Description

Fix the technical inconsistency identified in `src/plugins/linkedin.py` where double-braces `{{word}}` and `{{counter}}` were used, preventing correct variable replacement by the `.format()` call in `core.py`.

## Acceptance Criteria

- [ ] Refactor `src/plugins/linkedin.py` to use single-brace placeholders: `{word}` and `{counter}`.
- [ ] Audit all other plugins in `src/plugins` for similar double-brace placeholder issues.
- [ ] Correct any discrepancies to ensure universal compatibility with `EmailHarvester.do_search()`.
- [ ] Verify LinkedIn search functionality with a manual test.
