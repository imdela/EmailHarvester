# TI-11 Fix Implementation Checklist

**Ticket**: TI-11 — Resilience Manager & Global IP Pooling
**Audit Reference**: [TI-11-Audit-Results.md](../audits/TI-11-Audit-Results.md)
**Standard Reference**: [PYTHON_DEVELOPMENT_GUIDE.md](../standards/PYTHON_DEVELOPMENT_GUIDE.md)
**Date**: 2026-03-27

> Complete items in priority order. Do not move to a lower-priority item until all higher-priority items pass `pytest --cov=src` and `ruff check .`.

---

## 🔴 HIGH PRIORITY

### FIX-1 — Refactor Burst Pause Outside Lock Scope
**File**: `src/resilience.py` | **Lines**: 167–173
**Finding**: `time.sleep(pause)` is called while holding `ResilienceManager._lock`, blocking all threads for up to 30s.

**Steps**:
- [ ] Extract the `pause` value and `burst_count` reset *inside* the lock
- [ ] Call `time.sleep(pause)` *after* the `with` block is exited
- [ ] Verify no other shared state is read between the lock release and the sleep

**Expected Result**: Thread A waits for its burst pause independently; all other threads can proceed with their own `pre_flight_check` concurrently during that pause.

**Acceptance**: `pytest tests/unit/test_resilience_manager.py` passes; no deadlock in integration test.

---

### FIX-2 — Fix Tight Loop When TOR is Disabled
**File**: `src/resilience.py` | **Lines**: 193–196
**Finding**: When `tor_enabled=False` and current IP is `USING`, `rotate_identity()` returns `False` without any sleep, causing a CPU/network tight loop.

**Steps**:
- [ ] In the `USING` status branch, after `self.rotate_identity()` returns `False`, add `time.sleep(1.0)` before `continue`
- [ ] Ensure the sleep duration is sourced from config if possible (e.g., a new `tor_disabled_retry_delay_s` key in `stealth.yaml`), with a hardcoded fallback of `1.0`

**Expected Result**: When TOR is disabled and the IP is busy, the thread yields for at least 1 second per retry cycle.

**Acceptance**: Unit test `test_pre_flight_check_tight_loop_guard_success` passes; CPU usage does not spike in functional test.

---

### FIX-3 — Implement Mocked Unit Tests for Core ResilienceManager Methods
**File**: `tests/unit/test_resilience_manager.py`
**Finding**: `get_current_ip`, `rotate_identity`, and `pre_flight_check` have zero unit test coverage.

**Steps**:
- [ ] Add `test_get_current_ip_success` — mock `requests.get` to return a 200 with a fake IP; assert the IP is returned
- [ ] Add `test_get_current_ip_fails_all_urls` — mock all URLs to raise `requests.exceptions.ConnectionError`; assert `"unknown"` is returned
- [ ] Add `test_rotate_identity_success` — mock `stem.control.Controller` and `time.sleep`; assert `True` is returned and `NEWNYM` was signaled
- [ ] Add `test_rotate_identity_fails_when_tor_disabled` — assert `rotate_identity()` returns `False` immediately with no external calls
- [ ] Add `test_rotate_identity_fails_on_exception` — mock `Controller.from_port` to raise `Exception`; assert `False` is returned
- [ ] Add `test_pre_flight_check_clean_ip_success` — mock `get_current_ip` to return clean IP; assert IP is added as `USING` and returned
- [ ] Add `test_pre_flight_check_blacklisted_ip_rotates` — mock IP in cache as `BLACKLISTED`; mock `rotate_identity` to then return a clean IP; assert the clean IP is returned
- [ ] Add `test_pre_flight_check_tight_loop_guard_success` — mock `tor_enabled=False`, IP as `USING`, then `CLEAN` on second call; assert `time.sleep` was called
- [ ] Add `test_pre_flight_check_burst_mode_triggered` — drive `_shared_burst_count` to threshold; mock `time.sleep`; assert burst sleep is called *outside* lock scope (verify lock not held during sleep)
- [ ] Remove dead `get_status()` helper from `test_ip_status_lifecycle`

**Convention**: All test names follow `test_[action]_[success|fails]`. All mocks use `unittest.mock.patch`.

**Acceptance**: `pytest tests/unit/test_resilience_manager.py -v` — all pass; `pytest --cov=src/resilience.py` shows **≥ 90% coverage** on `resilience.py` from unit tests alone.

---

## 🟡 MEDIUM PRIORITY

### FIX-4 — Add Concurrency Integration Test
**File**: `tests/functional/test_resilience.py` (or new `tests/integration/test_resilience_concurrency.py`)
**Finding**: No test verifies that `USING` state correctly prevents two threads from using the same IP simultaneously.

**Steps**:
- [ ] Create test `test_using_state_isolates_threads_success`
- [ ] Instantiate one shared `ResilienceManager`
- [ ] Mock `get_current_ip` to always return `"1.2.3.4"` and `rotate_identity` to return `True`
- [ ] Pre-populate the shared cache with `"1.2.3.4": {status: USING}` before the second thread starts
- [ ] Spawn Thread A: calls `pre_flight_check()` — should block on `USING` and then rotate
- [ ] Spawn Thread B: releases the IP after 0.5s using `release_ip("1.2.3.4")` so Thread A can resume
- [ ] Assert Thread A eventually receives a healthy IP without collision
- [ ] Create test `test_shared_burst_count_increments_across_threads_success`
- [ ] Spawn N threads that each call `pre_flight_check()` with a mocked `get_current_ip`
- [ ] Assert `_shared_burst_count` reset was triggered at the configured threshold

**Acceptance**: `pytest tests/functional/test_resilience.py -v` — all pass; no race conditions or deadlocks.

---

### FIX-5 — Enhance Failure Progress Callback with Batch Index
**File**: `src/core.py` | **Line**: 541
**Finding**: Failure message only shows `(PARTIAL_CAPTCHA)` — does not include the batch index (`self.counter`).

**Steps**:
- [ ] Update line 541 from:
  ```python
  self.progress_callback(self.task_id, description=f"[red]{self.activeEngine} ({str(self.status)})")
  ```
  to:
  ```python
  self.progress_callback(self.task_id, description=f"[red]{self.activeEngine} ({str(self.status)}) @ Batch {self.counter}")
  ```
- [ ] Verify the same pattern is applied to the `FAILED_RATE_LIMIT` retry path (line ~524–527) if applicable

**Acceptance**: `pytest tests/unit/test_core_features.py` passes; manual run shows correct batch label in the dashboard.

---

## ⚪ LOW PRIORITY

### FIX-6 — Guard Terminal `rotate_identity()` in `report_block()`
**File**: `src/resilience.py` | **Line**: 244
**Finding**: `report_block()` unconditionally calls `self.rotate_identity()` at the end, adding a 15s block for any thread reporting a CAPTCHA or rate-limit hit.

**Steps**:
- [ ] Add a `rotate: bool = True` parameter to `report_block()` signature
- [ ] Wrap the terminal `self.rotate_identity()` call in `if rotate:`
- [ ] Update all callers in `core.py` (`do_search` lines 451, 455, 466) to pass `rotate=False` since `pre_flight_check` and the retry logic in `process()` already handle rotation
- [ ] Update unit tests accordingly

**Acceptance**: A thread reporting a block returns immediately without waiting 15s; `pytest` passes.

---

### FIX-7 — Remove Dead Test Helper
**File**: `tests/unit/test_resilience_manager.py` | **Lines**: 19–24
**Finding**: `get_status()` inner function is defined but never called — `ruff` flags this as `F841`.

**Steps**:
- [ ] Delete lines 19–24 (the `get_status` function definition) from `test_ip_status_lifecycle`
- [ ] Verify `ruff check tests/unit/test_resilience_manager.py` returns no warnings

**Acceptance**: `ruff check .` — clean; `pytest tests/unit/test_resilience_manager.py` passes.

---

## ✅ Done Criteria for TI-11 Closure

All of the following must be green before the ticket can be closed:

- [ ] `pytest --cov=src` → **100% coverage** on `src/resilience.py`
- [ ] `ruff check .` → **0 violations**
- [ ] `mypy src/` → **0 type errors**
- [ ] All 7 fix items above are checked off
- [ ] `TI-11-Resilience-Manager.md` acceptance criteria table fully checked
- [ ] A single atomic commit following the convention: `fix(ti-11): remediate resilience manager locking and coverage gaps`
