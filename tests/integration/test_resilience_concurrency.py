"""
Concurrency integration tests for ResilienceManager.
Spawns real threads to verify that shared state (USING, burst_count)
behaves correctly under concurrent access without deadlocks or race conditions.
"""

import pathlib
import threading
import time
from datetime import datetime
from typing import Generator
from unittest.mock import patch

import pytest

from src.resilience import ResilienceManager, ThreatLevel


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_shared_state() -> Generator[None, None, None]:
    """Resets all class-level shared state before and after each test."""
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()
        ResilienceManager._shared_burst_count = 0
    yield
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()
        ResilienceManager._shared_burst_count = 0


@pytest.fixture
def manager(tmp_path: pathlib.Path) -> ResilienceManager:
    """Returns a ResilienceManager with TOR disabled and a temporary storage path."""
    return ResilienceManager(storage_path=str(tmp_path / "ip_health.csv"))


# ─────────────────────────────────────────────
# USING State Isolation Tests
# ─────────────────────────────────────────────


def test_using_state_isolates_threads_success(manager: ResilienceManager) -> None:
    """Verify that a thread waits for the USING IP to be released before claiming it.

    Thread A holds the IP as USING. Thread B calls pre_flight_check() and must
    block (retry) until Thread A calls release_ip(). Thread B should eventually
    acquire a different clean IP, not collide with Thread A's circuit.
    """
    results: list[str] = []
    errors: list[Exception] = []

    # Seed the shared IP that Thread A is "using"
    claimed_ip = "10.10.10.1"
    clean_ip = "10.10.10.2"

    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache[claimed_ip] = {
            "status": ThreatLevel.USING,
            "timestamp": datetime.now(),
        }

    # Thread B will first see claimed_ip (USING), then after release see clean_ip.
    ip_sequence = [claimed_ip, clean_ip]
    call_count = {"n": 0}

    def mock_get_current_ip() -> str:
        idx = call_count["n"]
        call_count["n"] += 1
        return ip_sequence[min(idx, len(ip_sequence) - 1)]

    def thread_b_work() -> None:
        try:
            with (
                patch.object(manager, "get_current_ip", side_effect=mock_get_current_ip),
                patch.object(manager, "rotate_identity", return_value=False),
                patch("src.resilience.time.sleep"),
            ):
                ip = manager.pre_flight_check()
            results.append(ip)
        except Exception as e:
            errors.append(e)

    # Release Thread A's IP after a short delay to unblock Thread B
    def release_after_delay() -> None:
        time.sleep(0.05)
        manager.release_ip(claimed_ip)

    t_release = threading.Thread(target=release_after_delay, daemon=True)
    t_b = threading.Thread(target=thread_b_work, daemon=True)

    t_release.start()
    t_b.start()
    t_b.join(timeout=5.0)

    assert not errors, f"Thread B raised: {errors}"
    assert len(results) == 1
    assert results[0] == clean_ip, f"Expected clean IP {clean_ip!r}, got {results[0]!r}"

    # Ensure the final IP is in USING state (Thread B claimed it)
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache.get(clean_ip, {}).get("status") == ThreatLevel.USING


def test_shared_burst_count_increments_across_threads_success(tmp_path: pathlib.Path) -> None:
    """Verify that _shared_burst_count is correctly incremented across multiple threads.

    N threads each call pre_flight_check() once. The cumulative burst count
    should match N (or have been reset if the threshold was crossed).
    """
    n_threads = 4
    managers = [ResilienceManager(storage_path=str(tmp_path / "ip_health.csv")) for _ in range(n_threads)]

    # Unique IP per thread means no USING contention
    thread_ips = [f"192.168.1.{i}" for i in range(n_threads)]

    def worker(mgr: ResilienceManager, fake_ip: str) -> None:
        with patch.object(mgr, "get_current_ip", return_value=fake_ip), patch("src.resilience.time.sleep"):
            mgr.pre_flight_check()

    threads = [
        threading.Thread(target=worker, args=(managers[i], thread_ips[i]), daemon=True) for i in range(n_threads)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)

    # All threads completed pre_flight_check; at least n_threads increments occurred.
    # If threshold wasn't exceeded, count == n_threads; if it was, count was reset to 0.
    threshold = managers[0]._config.get("burst", {}).get("threshold_requests", 6)
    with ResilienceManager._lock:
        count = ResilienceManager._shared_burst_count
    assert count == n_threads % threshold, (
        f"Expected burst_count={n_threads % threshold} after {n_threads} threads, got {count}"
    )


def test_no_deadlock_on_concurrent_report_block_success(manager: ResilienceManager) -> None:
    """Verify that concurrent report_block() calls from multiple threads do not deadlock.

    This is a smoke test: if the test completes within the timeout, there is no deadlock.
    """
    n_threads = 8
    barrier = threading.Barrier(n_threads)
    errors: list[Exception] = []

    def worker(ip: str) -> None:
        try:
            barrier.wait(timeout=2.0)  # All threads start simultaneously
            with patch.object(manager, "save_cache"), patch.object(manager, "rotate_identity", return_value=False):
                manager.report_block(ip, reason="stress-test", permanent=False, rotate=False)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(f"172.16.0.{i}",), daemon=True) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)

    assert not errors, f"Threads raised errors: {errors}"
    with ResilienceManager._lock:
        assert len(ResilienceManager._shared_ip_cache) == n_threads
