# US-09: Multi-Threaded Engine Orchestration

**As a** security researcher  
**I want to** execute multiple search engine scrapes simultaneously  
**So that** I can minimize the overall execution time (makes searching 'all' engines significantly faster) without increasing the risk of a single-engine IP ban.

---

## Acceptance Criteria

1.  **Parallel Engine Execution**: The orchestrator in `src/cli.py` or `src/core.py` must launch each selected engine in a dedicated thread using `concurrent.futures.ThreadPoolExecutor`.
2.  **Sequential Internal Processing**: Each engine thread **must** process its internal pagination batches sequentially (not in parallel) to respect individual search engine rate limits from a single IP.
3.  **Anti-Fingerprint Jitter**: Replace the static `time.sleep(1)` inside the core loop with a randomized delay (e.g., `random.uniform(0.7, 1.8)` seconds) per engine thread to mimic human browsing patterns.
4.  **Graceful Thread Termination**: If one engine thread fails (e.g., network timeout), it should catch the `RuntimeError`, report it locally, and allow the other threads to complete their work.
5.  **Thread-Safe Result Aggregation**: All extracted emails from separate threads must be safely aggregated into a final unique results list before being printed/saved.
6.  **Concurrent Progress Visualization**: Implement a CLI progress bar (e.g., using `rich` or `tqdm`) that allows multiple engines to update their status simultaneously in the terminal without UI flicker or log corruption.

---

## Technical Considerations

*   **Concurrency Model**: Use `concurrent.futures.ThreadPoolExecutor` for its high-level API for handling futures.
*   **Result Retrieval**: Since `ThreadPoolExecutor.map()` or `.submit()` returns futures, use `as_completed()` to aggregate results as they become available.
*   **Library Additions**: Evaluate lightweight UI progress libraries (e.g., `rich`) to handle multi-line terminal updates.
*   **Rate-Limit Guardrails**: Ensure the "sequential within thread" constraint is strictly maintained to preserve IP health.
