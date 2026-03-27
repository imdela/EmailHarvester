# US-01: Python 3 Codebase Modernization and Syntax Compliance

## Description

**As a** developer or end-user of the EmailHarvester tool,
**I want** the codebase to be fully compliant with modern Python 3 standards,
**So that** the application runs reliably without syntax warnings, deprecation errors, or compatibility issues on current Python environments.

## Acceptance Criteria

- **Given** the application runs on a modern Python 3 interpreter (e.g., Python 3.8+),
- **When** the script is executed,
- **Then** no SyntaxWarning should be triggered regarding the `is` keyword being used for integer comparison (e.g., `sys.argv == 1` instead of `sys.argv is 1`).
- **And** the `urlparse` import logic should exclusively rely on `urllib.parse` without legacy Python 2 fallback blocks (`try...except ImportError`).
- **And** all regular expression patterns (e.g., `[a-zA-Z0-9.\-_+#~!$&\',;=:]+`) must use raw strings (`r"..."`) or properly escaped characters to avoid invalid escape sequence deprecation warnings.

## Technical Notes

- Update comparison operators in `EmailHarvester.py`.
- Modernize the `urlparse` module import at the top of the file.
- Convert regex string literals in `myparser.emails()` to raw strings.
