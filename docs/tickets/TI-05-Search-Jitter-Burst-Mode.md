# TI-05: Stealth Jitter Implementation (Burst & Rest)

## Description

Implement the adaptive "Burst & Rest" timing logic required by **US-12**, to better mimic human browsing behavior and avoid detection.

## Acceptance Criteria

- [ ] Add a `burst_count` and `burst_limit` (default: 5) to `EmailHarvester`.
- [ ] Update the `process()` loop in `src/core.py`.
- [ ] After every 5 requests, trigger a "Rest period" of `random.uniform(15.0, 30.0)` seconds.
- [ ] Maintain the existing `random.uniform(0.7, 1.8)` seconds between individual requests within a burst.
- [ ] Ensure that multiple engine threads (up to 20) do not synchronize their rests unnecessarily.
- [ ] Log "Resting for X seconds" specifically when a burst is completed.
