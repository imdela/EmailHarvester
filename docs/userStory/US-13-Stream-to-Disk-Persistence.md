# US-13: Stream-to-Disk Persistence (Atomic Persistence)

**As a** security researcher  
**I want to** have harvested emails written to the results file in real-time  
**So that** I don't lose my harvest if the process crashes or is terminated early, and can monitor discovery progress live via `tail -f`.

---

## Acceptance Criteria

1.  **Atomic Writing (Stream-to-Disk)**: Emails must be appended to the results file (`-s filename`) **immediately after each successful batch parse**, instead of waiting for the program to terminate.
2.  **Thread-Safe Append**: Implement a global `Lock` to allow 20+ concurrent workers to append found emails to the same results file without corruption or EOF errors.
3.  **Real-Time Flush**: Ensure each write explicitly flushes the buffer to ensure the file is always current and survives sudden process termination.
4.  **Global Unique Preservation**: Maintain a global set of found emails to prevent duplicate entries in the results file during a single run.

---

## Technical Considerations

*   **File Locking**: Use Python's `threading.Lock` to synchronize IO across the orchestrator's thread pool.
*   **Buffering**: Call `f.flush()` and `os.fsync()` for maximum data integrity during the stream.
