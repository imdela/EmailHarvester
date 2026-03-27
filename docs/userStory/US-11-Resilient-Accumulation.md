# US-11: Resilient Data Accumulation and Block Detection

**As a** security researcher  
**I want to** maximize the email yield across massive, multi-engine searches  
**So that** a failure or block in one batch doesn't destroy the data already harvested in previous batches or other engines, while being informed of the exact cause of any engine-level interruptions.

---

## Acceptance Criteria

1.  **Status-Aware Search Engine**: Update the core search logic in `src/core.py` to audit HTTP response codes (`403 Forbidden`, `429 Too Many Requests`) and `r.raise_for_status()` for all batches.
2.  **Heuristic Block Detection**: Implement a "Fingerprint Scanner" that identifies CAPTCHA or "Unusual Traffic" challenge pages in the HTML response, even if the status code is `200 OK`.
3.  **Partial Yield Preservation**: If an engine hits a block at Batch X, it must **not** raise a fatal exception. Instead, the loop must terminate for that engine and **return the list of emails found in Batches 1 to X-1**.
4.  **Informational Progress State**: The CLI dashboard must update the status line of a blocked engine to show `[PARTIAL] BLOCKED @ Batch X` or `[PARTIAL] CAPTCHA` instead of a misleading `100% SUCCESS` or `[-] ERROR`.
5.  **Smart Back-off (Wait & Retry)**: On a `429 Rate Limit` detection, the thread should perform a single "Cool Down" wait (e.g., 5-10 seconds) and retry that specific batch before definitively terminating the engine search.
6.  **Summary Diagnostics**: The final output must include a clear diagnostic report:
    *   `[+] Google: 145 emails (SUCCESS)`
    *   `[?] Bing: 82 emails (PARTIAL: Blocked at Batch 45)`
    *   `[X] Yahoo: 0 emails (FAILED: Access Forbidden 403)`

---

## Technical Considerations

*   **Exceptions vs. States**: Shift from raising `RuntimeError` internally to a "Status-Result" pattern where search results are bundled with an `EngineStatus` enum.
*   **Thread Isolation**: Maintain strict memory isolation (Thread-Local instances) so that a wait-and-retry on one engine doesn't block other threads from progressing.
*   **HTML Fingerprinting**: Compile a list of common "Block Strings" to scan for in the `decoding` step of search results.
