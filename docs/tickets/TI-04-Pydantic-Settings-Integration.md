# TI-04: Robust Configuration Schema (Rule 7)

## Description

Implement `pydantic-settings` to manage and validate the EmailHarvester engine configuration. Ensure "Fail-Fast" behavior on startup if required variables are invalid or missing, as required by Rule 7 of the `PYTHON_DEVELOPMENT_GUIDE.md`.

## Acceptance Criteria

- [ ] Add `pydantic-settings` and `pydantic` to `requirements.txt`.
- [ ] Create a `Settings` class (inherited from `BaseSettings`) in `src/core.py`.
- [ ] Centralize variables such as `SEARCH_LIMIT`, `USER_AGENT_PLATFORM`, `TOR_PORT`, `TOR_CONTROL_PORT`, and timeouts in this schema.
- [ ] Refactor `EmailHarvester.__init__` to utilize this `Settings` object for its internal configuration.
- [ ] Ensure that default values are provided to maintain CLI backward compatibility.
- [ ] Verify that an invalid configuration (e.g., negative timeout) raises a clear `ValidationError` on startup.
