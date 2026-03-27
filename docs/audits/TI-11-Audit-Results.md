# Resilience Manager Audit & TI-11 Analysis - 2026-03-27

## 🔍 Context

This audit evaluates the implementation status of **TI-11 (Resilience Manager)** and **US-11 (Resilient Accumulation)**. It identifies critical architectural bottlenecks that explain the observed application "hangs" and "crashes" during high-concurrency TOR operations.

## 🚨 Critical Findings

### 1. Global Lock Contention (The "23% Hang")
The primary cause of the application freezing is a **deadlock-prone locking strategy** in `src/resilience.py`.
*   **Blocking Inside Lock**: The `ResilienceManager._lock` is held while calling `time.sleep()` in `pre_flight_check()` for burst pauses (`resilience.py:167–173`) and implicitly through `rotate_identity()` (`resilience.py:148`).
*   **Impact**: Since there are up to 20 concurrent threads, if one thread triggers a 20s burst pause or a 15s TOR rotation while holding the lock, **all other threads are blocked** at the entry of `pre_flight_check`.
*   **Sequential vs. Parallel**: Identity rotations are forced to happen sequentially instead of allowing other healthy circuits to continue their work.
*   **Note**: The inter-page jitter sleep (`resilience.py:163`) is correctly placed *before* the lock acquisition and does not contribute to contention.

### 2. Tight Loop Risk (TOR Disabled)
*   **Bug in `pre_flight_check`**: If `tor_enabled` is `False`, the `while True` loop in `pre_flight_check` can become a tight loop if an IP is marked as `USING`.
*   **Scenario**: `rotate_identity()` returns `False` immediately, and the loop continues to `get_current_ip()` and the lock check, hammering the CPU and network without delay.
*   **Location**: `resilience.py:193–196` — there is no `time.sleep()` guard before `continue` in the `USING` branch when rotation is unavailable.

### 3. User Story 11 Compliance (CLI Dashboard)
*   **Missing Instrumentation**: User Story 11 requirement #4 specifies that the CLI should show `[PARTIAL] BLOCKED @ Batch X`.
*   **Gap**: `core.py:541` reports only `f"[red]{self.activeEngine} ({str(self.status)})"` on failure — the `self.counter` batch index is available in scope but is not included in the progress callback description.

### 4. Test Coverage Deficit (Requirement Violation)
TI-11 Acceptance Criteria requires **100% test coverage** for the pooled resilience logic. Currently:
*   **Untested Core Methods**: `get_current_ip`, `rotate_identity`, and `pre_flight_check` (the most complex logic) are entirely untested in unit tests.
*   **Zero Concurrency Tests**: There are no tests verifying that the `USING` state correctly isolates threads or that the shared `burst_count` behaves correctly under multi-threaded stress.
*   **Dead Test Code**: `tests/unit/test_resilience_manager.py` defines a `get_status()` helper inside `test_ip_status_lifecycle` that is never called — a lint violation (`ruff` will flag this as unused variable F841).

### 5. Secondary Blocking in `report_block()` [NEW]
*   **Unguarded `rotate_identity()` Call**: `report_block()` ends at `resilience.py:244` with an unconditional call to `self.rotate_identity()`.
*   **Impact**: Any thread reporting a block (e.g., on a 429 or CAPTCHA) will be blocked for `rotation_stabilization_s` (default 15s) inside `report_block`, in addition to the lock contention already present in `pre_flight_check`. This compounds latency for all callers.
*   **Audit Gap**: This secondary blocking path was absent from the original audit.

## 📋 TI-11 Completion Status

| Requirement | Status | Gap |
| :--- | :--- | :--- |
| Rename ResilienceEngine -> ResilienceManager | ✅ **DONE** | Complete. |
| Implement `USING` state | ⚠️ **PARTIAL** | Logic is present but flawed (blocking inside lock + tight loop). |
| Centralize `burst_count` | ✅ **DONE** | State is correctly shared via `_shared_burst_count` class variable. |
| Diagnostic logging to `ip_health.csv` | ✅ **DONE** | `save_cache()` writes CSV correctly. |
| 100% Test Coverage | ❌ **FAIL** | Core logic and concurrency are untested; dead code present. |

## 🛠 Remediation Plan (To Finish TI-11)

1.  **[HIGH] Refactor Burst Lock**: Move `time.sleep(pause)` in `pre_flight_check()` (`resilience.py:167–173`) **outside** the `ResilienceManager._lock` scope.
2.  **[HIGH] Fix Tight Loop**: Add a `time.sleep(1.0)` guard before `continue` in `pre_flight_check()` when identity rotation is requested but disabled (the `USING` branch).
3.  **[HIGH] Implement Mocked Unit Tests**: Create unit tests for `ResilienceManager` that mock `requests` and `stem.control.Controller` to cover `get_current_ip`, `rotate_identity`, and `pre_flight_check` locally.
4.  **[MEDIUM] Add Threading Integration Test**: Create a functional test that spawns multiple threads to verify the `USING` state prevents IP collisions under concurrency.
5.  **[MEDIUM] Enhance CLI Description**: Modify the `progress_callback` in `core.py:541` to include `self.counter` (the batch index) on failure.
6.  **[LOW] Guard `report_block` Rotation**: Make the terminal `rotate_identity()` call in `report_block()` conditional or non-blocking to avoid a double 15s penalty for the reporting thread.
7.  **[LOW] Remove Dead Test Code**: Delete the unused `get_status()` helper from `test_ip_status_lifecycle` to pass `ruff` linting.

---
**Auditor**: Antigravity AI
**Date**: 2026-03-27 (Revised — v2)
**Changes vs v1**: Added Finding 5 (secondary block in `report_block`); clarified Finding 1 (jitter sleep is correctly placed); added Finding 4 dead-code note; updated remediation plan with priority levels and precise line references.
