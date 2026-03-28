# Modernization Final Push Checklist (Finalization TI-11)

**Reference**: [modernization_status_report.md](../audits/modernization_status_report.md)
**Standard**: [PYTHON_DEVELOPMENT_GUIDE.md](../standards/PYTHON_DEVELOPMENT_GUIDE.md)
**Date**: 2026-03-28

> [!IMPORTANT]
> These items must be implemented to ensure 100% human-like behavior and finalize the 2026 modernization of EmailHarvester.

---

## 🔵 1. Filename Automation (UX)
**Goal**: Ensure results are saved even if the user forgets the `-s` flag.
- [ ] **File**: `src/cli.py` | **Location**: `main()` (args parsing)
- [ ] If `args.filename` is `None`, default `filename` to `args.domain`.
- [ ] Ensure legal filename characters are handled (already checked by `checkDomain`).
- [ ] **Expected**: `python3 EmailHarvester.py -d test.com` should automatically create `test.com.txt`.

---

## 🕵️ 2. Dynamic Stealth & Human Simulation
**Goal**: Eliminate all hardcoded timing patterns to avoid search engine detection.

### A. Global Jitter & Staggered Start
- [ ] **File**: `src/cli.py` | **Location**: `ThreadPoolExecutor` loop.
- [ ] Replace `time.sleep(random.uniform(0.2, 0.5))` with values from `stealth.yaml` (`timing.min_jitter_ms` and `max_jitter_ms`).
- [ ] Implementation should convert ms to seconds (`/ 1000.0`).

### B. Batch Execution Jitter
- [ ] **File**: `src/core.py` | **Location**: `EmailHarvester.process()` loop.
- [ ] Add a `time.sleep(random.uniform(min, max))` *between* batch requests (increments of `self.counter`).
- [ ] Values must be sourced from a new `stealth.yaml` key: `timing.batch_pause_range`.

### C. TOR Identity Rotation & Stabilization
- [ ] **File**: `src/resilience.py` | **Location**: `rotate_identity()`.
- [ ] Check `controller.get_newnym_wait()` to avoid TOR's 10s rate limit (551 error).
- [ ] If wait > 0, sleep for the duration provided by TOR.
- [ ] Replace fixed 15s wait with a randomized stabilization wait (ex: 3s to 6s) defined in `stealth.yaml` (`timing.circuit_stabilization_range`).
- [ ] **File**: `src/core.py` | **Location**: `process()`.
- [ ] Replace `time.sleep(5.0)` with randomized circuit wait sourced from `stealth.yaml`.

---

## 🛡️ 3. Connectivity & IP tracking (Resilience)
**Goal**: Avoid silent failures when the external IP cannot be verified.
- [ ] **File**: `src/resilience.py` | **Location**: `pre_flight_check()`.
- [ ] If `current_ip` is `"unknown"`, do not just return it. 
- [ ] Implement a retry mechanism: Attempt to rotate TOR identity immediately if IP detection fails twice.
- [ ] If still `"unknown"` after rotation, raise a `ConnectivityError` to stop the thread properly.

---

## 🧹 4. Redundancy & Maintenance
- [ ] **File**: `src/cli.py` | **Location**: End of `main()`.
- [ ] Remove the redundant loop that re-writes the TXT file (since `save_email_callback` already streams it).
- [ ] Keep the XML generation block as the final "clean" artifact.
- [ ] **File**: `src/config/stealth.yaml`.
- [ ] Add explicit comments for every key to explain its impact on the "Speed vs Stealth" balance.

---

## ✅ Validation Criteria
- [ ] `pytest tests/unit/` -> All tests green.
- [ ] `ruff check .` -> Zero violations.
- [ ] `mypy src/ --strict` -> Zero type errors.
- [ ] Manual verification: Run `EmailHarvester.py -d payoneer.com --tor` and check if `payoneer.com.txt` is created with variable delays.
