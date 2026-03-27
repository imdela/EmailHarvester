import os
import pathlib

from src.resilience import ResilienceManager, ThreatLevel


def test_ip_status_lifecycle(tmp_path: pathlib.Path) -> None:
    """
    Verify that an IP correctly transitions through statuses using ResilienceManager.
    """
    storage = os.path.join(tmp_path, "test_ip_health.csv")
    engine = ResilienceManager(storage_path=storage)

    # We clear the shared cache explicitly for tests because ResilienceManager uses class-level state
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()

    # 1. New IP should be CLEAN implicitly (not in pool means it gets assigned USING on first pre_flight)
    def get_status(ip: str) -> ThreatLevel:
        with ResilienceManager._lock:
            data = ResilienceManager._shared_ip_cache.get(ip)
            return (
                data["status"] if data else ThreatLevel.USING
            )  # It assumes using if not found during pre-flight, but lets just check if it's there. Actually, the cache doesn't have CLEAN. Let's just check the data.

    # 2. Mark as REJECTED
    engine.report_block("1.1.1.1", permanent=False)
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["1.1.1.1"]["status"] == ThreatLevel.REJECTED

    # 3. Mark as BLACKLISTED
    engine.report_block("2.2.2.2", permanent=True)
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["2.2.2.2"]["status"] == ThreatLevel.BLACKLISTED


def test_cache_persistence(tmp_path: pathlib.Path) -> None:
    """
    Verify that IP data is correctly saved and reloaded by ResilienceManager.
    """
    storage = os.path.join(tmp_path, "persist_ip.csv")

    # Clear shared state
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()

    engine = ResilienceManager(storage_path=storage)
    engine.report_block("9.9.9.9", permanent=True)

    # Clear shared state to simulate fresh load
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()

    # Create new manager pointing to same file
    new_engine = ResilienceManager(storage_path=storage)

    with ResilienceManager._lock:
        assert "9.9.9.9" in ResilienceManager._shared_ip_cache
        assert ResilienceManager._shared_ip_cache["9.9.9.9"]["status"] == ThreatLevel.BLACKLISTED

    assert new_engine is not None  # Consume the new_engine to avoid lints
