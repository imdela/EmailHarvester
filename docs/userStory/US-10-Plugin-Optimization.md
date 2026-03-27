# US-10: Plugin Optimization and Pruning

**As a** security researcher  
**I want to** remove dead search engine plugins and repair "hijacked" social media searches  
**So that** I don't waste time/network resources on non-functional engines and get more accurate results from social platforms.

---

## Acceptance Criteria

1.  **Prune Obsolete Engines**: Permanently delete `googleplus.py` (defunct platform) and `exalead.py` (deprecated public scraping endpoint) from `src/plugins/`.
2.  **Repair "Baidu Hijacking"**: Standardize the search URL for `linkedin.py`, `twitter.py`, `github.py`, `instagram.py`, `reddit.py`, and `youtube.py` to use a high-quality global engine (Google or Bing) with the `site:` operator.
3.  **Correct Internal Naming**: Audit all `init_search` calls to ensure the internal variable names match the engine being invoked (e.g., if scraping Google, pass `url` not `yahooUrl`).
4.  **Validate Plugin Registration**: Ensure each repaired plugin registers itself with its correct identifier (e.g., `linkedin`) so that `-e linkedin` works natively.
5.  **Verify Search Functionality**: Perform dry-runs for the repaired social plugins to ensure they return data from their respective platforms correctly via the new providers.

---

## Technical Considerations

*   **Social Search Pattern**: A recommended pattern for LinkedIn would be: `https://www.bing.com/search?q=site%3Alinkedin.com/in/+%40{word}&count=50&first={counter}`.
*   **Code Integrity**: Maintain all `mypy` strict type enforcements and `ruff` formatting throughout the repair process.
*   **Result Verification**: Test the `-p` (list plugins) command to ensure the pruned list is clean and professional.
