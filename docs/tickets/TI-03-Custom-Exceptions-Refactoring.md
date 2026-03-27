# TI-03: Custom Exception Segregation (Rule 10)

## Description

Refactor the search engine error handling to replace generic `RuntimeError` strings with a structured hierarchy of custom exceptions, as required by Rule 10 of the `PYTHON_DEVELOPMENT_GUIDE.md`.

## Acceptance Criteria

- [ ] Define a base class `EmailHarvesterError(Exception)` in `src/core.py`.
- [ ] Create specialized sub-classes:
  - `RateLimitError` (for 429 status code)
  - `ForbiddenError` (for 403 status code)
  - `SearchBlockedError` (for Captcha detection)
  - `PluginConfigurationError` (for invalid URLs or missing data)
- [ ] Refactor `EmailHarvester.do_search()` and `EmailHarvester.process()` to raise these specific exceptions.
- [ ] Update `src/cli.py` to catch these typed exceptions and convert them to user-friendly status messages in the Rich dashboard.
- [ ] Ensure `mypy` strict analysis remains green after refactoring.
