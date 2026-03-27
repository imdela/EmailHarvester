# Phase 1: Modernization Fixes Checklist

This checklist tracks the remediation steps required to close the gaps identified in the `2026-03-27_Implementation_Audit.md` and achieve true compliance with the Python Development Guide.

## Outstanding Technical Debt

- [x] **Fix TI-03 (Exception Handling in CLI & Plugins)**:
  - Update `src/cli.py` to intercept `RateLimitError`, `ForbiddenError`, and `SearchBlockedError`, formatting them into user-friendly Rich dashboard messages rather than a generic `Exception`.
  - Replace the bare `RuntimeError` explicitly raised inside `src/plugins/ask.py` using our new custom hierarchy.

- [x] **Fix TI-04 (Pydantic Fail-Fast Tests)**:
  - Create a test case (e.g., in `tests/test_settings.py`) explicitly proving that an invalid environment configuration (like `EH_TIMEOUT=-5`) triggers a `ValidationError` preventing unsafe engine startup.

- [x] **Fix TI-05 (Stealth Jitter Unit Tests)**:
  - Add a dedicated test in `tests/test_stealth.py` that verifies the engine correctly tracks its `burst_count` and triggers the long `time.sleep` (15-30s) strictly on the 5th request iteration.

- [ ] **Fix TI-07 (Plugin Layer Docstrings)**:
  - Enforce PEP 257 Google-Style compliance by adding complete `Args:` and `Returns:` docstrings to the `search()` function of ALL remaining plugin files (ask, baidu, bing, dogpile, github, google, instagram, reddit, twitter, yahoo, youtube).

- [ ] **Fix TI-08 (True Pytest Refactoring)**:
  - Refactor the existing test suites (`test_stealth.py`, `test_resilience.py`) to actually utilize the specific `base_harvester` fixture defined in `conftest.py`, eliminating the manual instantiation of `EmailHarvester` instances in every test class.
