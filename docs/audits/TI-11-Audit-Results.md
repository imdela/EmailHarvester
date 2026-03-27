# Resilience Manager Audit & TI-11 Analysis - 2026-03-27

## 🔍 Context

This audit evaluates the implementation status of **TI-11 (Resilience Manager)** and **US-11 (Resilient Accumulation)**. It identifies critical architectural bottlenecks that explain the observed application "hangs" and "crashes" during high-concurrency TOR operations.

## 🚨 Critical Findings

### 1. Global Lock Contention (The "23% Hang")
The primary cause of the application freezing is a **deadlock-prone locking strategy** in `src/resilience.py`.
*   **Blocking Inside Lock**: The `ResilienceManager._lock` is held while calling `time.sleep()` in `pre_flight_check()` (for both jitter and burst pauses) and `rotate_identity()`.
*   **Impact**: Since there are up to 20 concurrent threads, if one thread triggers a 20s burst pause or a 15s TOR rotation while holding the lock, **all other threads are blocked** at the entry of `pre_flight_check`.
*   **Sequential vs. Parallel**: Identity rotations are forced to happen sequentially instead of allowing other healthy circuits to continue their work.

### 2. Tight Loop Risk (TOR Disabled)
*   **Bug in `pre_flight_check`**: If `tor_enabled` is `False`, the `while True` loop in `pre_flight_check` can become a tight loop if an IP is marked as `USING`.
*   **Scenario**: `rotate_identity()` returns `False` immediately, and the loop continues to `get_current_ip()` and the lock check, hammering the CPU and network without delay.

### 3. User Story 11 Compliance (CLI Dashboard)
*   **Missing Instrumentation**: User Story 11 requirement #4 specifies that the CLI should show `[PARTIAL] BLOCKED @ Batch X`. 
*   **Gap**: Currently, `src/cli.py` and `src/core.py` only report the status (e.g., `PARTIAL_CAPTCHA`), but don't include the specific counter/batch index where the block occurred.

### 4. Test Coverage Deficit (Requirement Violation)
TI-11 Acceptance Criteria requires **100% test coverage** for the pooled resilience logic. Currently:
*   **Untested Core Methods**: `get_current_ip`, `rotate_identity`, and `pre_flight_check` (the most complex logic) are entirely untested in unit tests.
*   **Zero Concurrency Tests**: There are no tests verifying that the `USING` state correctly isolates threads or that the shared `burst_count` behaves correctly under multi-threaded stress.

## 📋 TI-11 Completion Status

| Requirement | Status | Gap |
| :--- | :--- | :--- |
| Rename ResilienceEngine -> ResilienceManager | ✅ **DONE** | Complete. |
| Implement `USING` state | ⚠️ **PARTIAL** | Logic is present but flawed (blocking). |
| Centralize `burst_count` | ✅ **DONE** | State is correctly shared. |
| Diagnostic logging to `ip_health.csv` | ✅ **DONE** | Functional. |
| 100% Test Coverage | ❌ **FAIL** | Core logic and concurrency are untested. |

## 🛠 Remediation Plan (To Finish TI-11)

1.  **Refactor Locking**: Move all `time.sleep()` calls (jitter, burst, and rotation) **outside** the `ResilienceManager._lock` scope.
2.  **Fix Tight Loop**: Add a break or safety delay in `pre_flight_check` when identity rotation is requested but disabled.
3.  **Enhance CLI Description**: Modify the `progress_callback` in `core.py` to include the batch number on failure.
4.  **Implement Mocked Unit Tests**: Create unit tests for `ResilienceManager` that mock `requests` and `stem.control.Controller` to simulate blocks and rotations locally.
5.  **Add Threading Integration Test**: Create a functional test that spawns multiple threads to verify the `USING` state prevents IP collisions.

---
**Auditor**: Antigravity AI
**Date**: 2026-03-27
