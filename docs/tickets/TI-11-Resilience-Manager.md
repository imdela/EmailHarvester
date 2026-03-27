# TI-11: Resilience Manager & Global IP Pooling (Rule 7, 10, 11)

## Description

Implement an advanced `ResilienceManager` to handle search engine blocks by tracking "dirty" TOR IPs and automating identity rotation using a shared state pool. This system ensures that search attempts are only made using verified healthy circuits, preventing thread conflicts.

## Functional Logic (Human Behavior Simulation)

1.  **Centralized "Lean" IP Pool**:
    *   **States**: `USING` (thread isolation), `REJECTED` (quarantine), `BLACKLISTED` (persistent).
    *   **Locking Mechanism**: A thread marks an IP as `USING`. No other thread can select it until it is released or rejected.
    *   **Clean IP Handling**: If an IP is not in the pool, it is considered `CLEAN`. It gets added to the pool as `USING`, performing the search, and then **removed** from the pool upon completion (unless a block occurs).

2.  **Adaptive Delay Strategy (Externalized)**:
    *   **Inter-page Jitter**: Short jitter (100ms - 500ms) to break machine regularity.
    *   **Progressive Jitter**: Start at 3s. Upon partial block (`REJECTED`), increase to 5s, 7s, 10s... up to a **30s cap**.
    *   **Global Burst Mode**: Force a **15-30s human-like pause** every 5-10 cumulative requests to the same host (e.g., Google) across all threads.

3.  **Tor Circuit Stabilization**:
    *   Signal `NEWNYM` with a **15-second** wait time to ensure circuit rebuild completion.

4.  **Recovery Logic (Configurable)**:
    *   Check `REJECTED` IPs after a defined quarantine (e.g., 60 minutes).
    *   Promote to `BLACKLISTED` if blocks persist across multiple attempts or sessions.

## Acceptance Criteria

- [ ] Rename `ResilienceEngine` -> `ResilienceManager` and `IPStatus` -> `ThreatLevel`.
- [ ] Implement the `USING` state to prevent concurrent requests on the same IP.
- [ ] Centralize `burst_count` in `ResilienceManager` (Shared State across engines).
- [ ] Add diagnostic logging to `ip_health.csv` (block reason, attempts).
- [ ] Achieve 100% test coverage for the pooled resilience logic.

---
**Status:** IN_PROGRESS
