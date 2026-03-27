# TI-11: Resilience Manager & IP Blacklisting (Rule 7, 10, 11)

## Description

Implement an advanced `ResilienceManager` to handle search engine blocks by tracking "dirty" TOR IPs and automating identity rotation. This system will classify IPs as 'CLEAN', 'REJECTED' (1h quarantine), or 'BLACKLISTED' (permanent for session), ensuring that search attempts are only made using verified healthy circuits.

## Acceptance Criteria

- [ ] Create `src/resilience.py` containing the `IPManager` and `ThreatLevel` logic.
- [ ] Implement `src/config/ip_health.csv` persistence for IP status tracking.
- [ ] Add a "Pre-flight IP Check" in each search thread before executing requests.
- [ ] Automate TOR identity rotation (`NEWNYM`) when a blocked IP is detected.
- [ ] Implement a "Staggered Start" in the CLI orchestrator to delay thread launching.
- [ ] Add randomized jitter and progressive backoff for search requests.
- [ ] Achieve 100% test coverage for the resilience logic.

---
**Status:** Open
