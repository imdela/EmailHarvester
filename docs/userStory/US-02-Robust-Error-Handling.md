# US-02: Robust Error Handling and Exception Management

## Description

**As a** user operating EmailHarvester,
**I want** the application to gracefully handle network and file I/O exceptions,
**So that** it provides clear, actionable feedback instead of crashing abruptly or swallowing critical errors silently.

## Acceptance Criteria

- **Given** the application attempts to save output to a text or XML file,
- **When** an exception occurs (e.g., permission denied),
- **Then** the exception message should be logged safely to the console without causing a type-casting crash (e.g., converting exception objects explicitly to strings before concatenation).
- **And** silent `except:` blocks (bare excepts) must specify the exception class (e.g., `except Exception as e`) and log the context.
- **Given** the `ask.py` plugin executes a search,
- **When** the HTTP response does not explicitly define an encoding (`r.encoding is None`),
- **Then** the plugin must gracefully default to `UTF-8` before decoding the response content to prevent a `TypeError`.

## Technical Notes

- Refactor file I/O `try/except` blocks in `EmailHarvester.py` (lines 304-318).
- Ensure `str(e)` is used when printing exceptions natively.
- Apply the encoding fallback logic (`if r.encoding is None: r.encoding = 'UTF-8'`) directly to `plugins/ask.py`.
