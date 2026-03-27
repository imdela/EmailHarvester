# US-05: Documentation Revamp and Legal / Ethical Compliance Integration

## Description

**As an** end-user cloning this repository,
**I want** comprehensive, clear, and up-to-date documentation that exactly reflects the application's CLI options, setup process, and strict ethical usage guidelines,
**So that** I understand how to securely install the tool via venv, what command parameters are available, and the legal constraints surrounding its use.

## Acceptance Criteria

- **Given** a user navigates to the project repository,
- **When** they read the `README.md`,
- **Then** they should see an updated description explicitly mentioning the current CLI arguments and plugins.
- **And** there must be explicit installation instructions using Python virtual environments (`python3 -m venv ...`, source activation, and pip install).
- **And** both HTTPS and SSH cloning methods must be documented side-by-side.
- **And** a clear note must indicate that the repository is a fork modernized in 2026.
- **And** an explicit "Legal & Ethical Use" section must be present, forbidding illegal actions (phishing, spam) and restricting usage to educational, security audit, or B2B prospecting purposes while respecting GDPR/CAN-SPAM.
- **And** original copyright credits to `@maldevel` must remain prominently featured.
- **And** the `LICENSE` file must structurally remain an untouched GNU GPLv3 license.

## Technical Notes

- Rewrite the `README.md` completely under professional markdown formatting conventions.
- Extract the `--help` output directly into the README to reflect exactly what the tool supports securely.
- Ensure zero modifications are made to the actual `LICENSE` file text.
