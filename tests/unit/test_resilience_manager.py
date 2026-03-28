"""
Unit tests for ResilienceManager.
Covers IP lifecycle, cache persistence, get_current_ip, rotate_identity,
and pre_flight_check with full mock isolation (no network, no TOR daemon).
"""

import pathlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.resilience import ResilienceManager, ThreatLevel


# Note: ResilienceManager shared state is reset by the global autouse fixture in conftest.py.
@pytest.fixture
def manager(tmp_path: pathlib.Path) -> ResilienceManager:
    """Returns a default ResilienceManager with TOR disabled and temp storage."""
    return ResilienceManager(storage_path=str(tmp_path / "ip_health.csv"))


@pytest.fixture
def tor_manager(tmp_path: pathlib.Path) -> ResilienceManager:
    """Returns a ResilienceManager with TOR enabled for rotation tests."""
    return ResilienceManager(
        storage_path=str(tmp_path / "ip_health.csv"),
        tor_enabled=True,
    )


# ─────────────────────────────────────────────
# IP Status Lifecycle & Cache Persistence
# ─────────────────────────────────────────────


def test_ip_status_lifecycle_success(manager: ResilienceManager) -> None:
    """Verify that an IP correctly transitions through REJECTED and BLACKLISTED statuses."""
    manager.report_block("1.1.1.1", permanent=False, rotate=False)
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["1.1.1.1"]["status"] == ThreatLevel.REJECTED

    manager.report_block("2.2.2.2", permanent=True, rotate=False)
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["2.2.2.2"]["status"] == ThreatLevel.BLACKLISTED


def test_cache_persistence_success(tmp_path: pathlib.Path) -> None:
    """Verify that IP health data is correctly saved to CSV and reloaded by a new instance."""
    storage = str(tmp_path / "persist_ip.csv")
    engine = ResilienceManager(storage_path=storage)
    engine.report_block("9.9.9.9", permanent=True, rotate=False)

    # Simulate a fresh process loading the same file
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache.clear()

    new_engine = ResilienceManager(storage_path=storage)

    with ResilienceManager._lock:
        assert "9.9.9.9" in ResilienceManager._shared_ip_cache
        assert ResilienceManager._shared_ip_cache["9.9.9.9"]["status"] == ThreatLevel.BLACKLISTED

    assert new_engine is not None


# ─────────────────────────────────────────────
# get_current_ip Tests
# ─────────────────────────────────────────────


def test_get_current_ip_success(manager: ResilienceManager) -> None:
    """Verify that get_current_ip returns the stripped IP from the first successful URL."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "  1.2.3.4  "

    with patch("src.resilience.requests.get", return_value=mock_response) as mock_get:
        ip = manager.get_current_ip()

    assert ip == "1.2.3.4"
    mock_get.assert_called_once()


def test_get_current_ip_fails_all_urls_success(manager: ResilienceManager) -> None:
    """Verify that get_current_ip returns 'unknown' when every URL raises an exception."""
    with patch("src.resilience.requests.get", side_effect=Exception("Connection refused")):
        ip = manager.get_current_ip()

    assert ip == "unknown"


def test_get_current_ip_fallback_on_non_200_success(manager: ResilienceManager) -> None:
    """Verify that get_current_ip falls back to the next URL when a 503 is returned."""
    fail_response = MagicMock()
    fail_response.status_code = 503

    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.text = "5.6.7.8"

    with patch("src.resilience.requests.get", side_effect=[fail_response, ok_response]):
        ip = manager.get_current_ip()

    assert ip == "5.6.7.8"


# ─────────────────────────────────────────────
# rotate_identity Tests
# ─────────────────────────────────────────────


def test_rotate_identity_fails_when_tor_disabled(manager: ResilienceManager) -> None:
    """Verify that rotate_identity returns False immediately when TOR is disabled."""
    with patch("src.resilience.Controller") as mock_controller:
        result = manager.rotate_identity()

    assert result is False
    mock_controller.assert_not_called()


def test_rotate_identity_success(tor_manager: ResilienceManager) -> None:
    """Verify that rotate_identity signals NEWNYM and returns True on success."""
    mock_ctrl = MagicMock()
    mock_ctrl.get_newnym_wait.return_value = 0  # Fix: Return numeric 0 to avoid comparing MagicMock to int

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_ctrl)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("src.resilience.Controller.from_port", return_value=mock_ctx), patch("src.resilience.time.sleep"):
        result = tor_manager.rotate_identity()

    assert result is True
    mock_ctrl.signal.assert_called_once()


def test_rotate_identity_fails_on_exception(tor_manager: ResilienceManager) -> None:
    """Verify that rotate_identity returns False when the TOR controller raises an error."""
    with patch("src.resilience.Controller.from_port", side_effect=Exception("TOR not running")):
        result = tor_manager.rotate_identity()

    assert result is False


# ─────────────────────────────────────────────
# pre_flight_check Tests
# ─────────────────────────────────────────────


def test_pre_flight_check_clean_ip_success(manager: ResilienceManager) -> None:
    """Verify that a clean real IP is immediately claimed as USING and returned."""
    with patch.object(manager, "get_current_ip", return_value="10.0.0.1"), patch("src.resilience.time.sleep"):
        ip = manager.pre_flight_check()

    assert ip == "10.0.0.1"
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["10.0.0.1"]["status"] == ThreatLevel.USING


def test_pre_flight_check_unknown_ip_raises_connectivity_error_success(manager: ResilienceManager) -> None:
    """Verify that 'unknown' IP detection raises ConnectivityError after retries (FIX-CONNECTIVITY)."""
    from src.resilience import ConnectivityError

    with (
        patch.object(manager, "get_current_ip", return_value="unknown"),
        patch.object(manager, "rotate_identity", return_value=True),
        patch("src.resilience.time.sleep"),
    ):
        with pytest.raises(ConnectivityError):
            manager.pre_flight_check()

    with ResilienceManager._lock:
        assert "unknown" not in ResilienceManager._shared_ip_cache, "'unknown' must never enter the USING pool"


def test_pre_flight_check_blacklisted_ip_rotates_success(manager: ResilienceManager) -> None:
    """Verify that a BLACKLISTED IP triggers rotation and then claims the next clean IP."""
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache["10.0.0.99"] = {
            "status": ThreatLevel.BLACKLISTED,
            "timestamp": datetime.now(),
        }

    with (
        patch.object(manager, "get_current_ip", side_effect=["10.0.0.99", "10.0.0.1"]),
        patch.object(manager, "rotate_identity", return_value=True),
        patch("src.resilience.time.sleep"),
    ):
        ip = manager.pre_flight_check()

    assert ip == "10.0.0.1"

    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["10.0.0.1"]["status"] == ThreatLevel.USING


def test_pre_flight_check_tight_loop_guard_success(manager: ResilienceManager) -> None:
    """Verify that a 1s guard sleep is applied when TOR is disabled and IP is USING (FIX-2)."""
    # Seed cache: first IP is IN USE; second is clean
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache["10.0.0.2"] = {
            "status": ThreatLevel.USING,
            "timestamp": datetime.now(),
        }

    with (
        patch.object(manager, "get_current_ip", side_effect=["10.0.0.2", "10.0.0.3"]),
        patch("src.resilience.time.sleep") as mock_sleep,
    ):
        ip = manager.pre_flight_check()

    assert ip == "10.0.0.3"
    # FIX-2: the 1.0s guard sleep must have been triggered
    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert 1.0 in sleep_args, f"Expected 1.0s guard sleep; got sleep calls with args: {sleep_args}"


def test_pre_flight_check_quarantine_active_rotates_success(manager: ResilienceManager) -> None:
    """Verify that a REJECTED IP still in quarantine triggers rotation."""
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache["10.0.0.10"] = {
            "status": ThreatLevel.REJECTED,
            "timestamp": datetime.now(),  # quarantine not expired
        }

    with (
        patch.object(manager, "get_current_ip", side_effect=["10.0.0.10", "10.0.0.11"]),
        patch.object(manager, "rotate_identity", return_value=False),
        patch("src.resilience.time.sleep"),
    ):
        ip = manager.pre_flight_check()

    assert ip == "10.0.0.11"


def test_pre_flight_check_quarantine_expired_reclaims_success(manager: ResilienceManager) -> None:
    """Verify that a REJECTED IP past its quarantine window is reclaimed as USING."""
    with ResilienceManager._lock:
        ResilienceManager._shared_ip_cache["10.0.0.20"] = {
            "status": ThreatLevel.REJECTED,
            "timestamp": datetime.now() - timedelta(minutes=120),  # expired
        }

    with patch.object(manager, "get_current_ip", return_value="10.0.0.20"), patch("src.resilience.time.sleep"):
        ip = manager.pre_flight_check()

    assert ip == "10.0.0.20"
    with ResilienceManager._lock:
        assert ResilienceManager._shared_ip_cache["10.0.0.20"]["status"] == ThreatLevel.USING


def test_pre_flight_check_burst_mode_triggered_success(manager: ResilienceManager) -> None:
    """Verify that the burst-mode pause is triggered when the threshold is reached (FIX-1)."""
    threshold: int = manager._config.get("burst", {}).get("threshold_requests", 6)
    pause: int = manager._config.get("burst", {}).get("pause_duration_s", 20)

    # Drive to threshold - 1 so the next call tips it over
    with ResilienceManager._lock:
        ResilienceManager._shared_burst_count = threshold - 1

    with (
        patch.object(manager, "get_current_ip", return_value="10.0.0.30"),
        patch("src.resilience.time.sleep") as mock_sleep,
    ):
        manager.pre_flight_check()

    sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
    assert float(pause) in sleep_args, f"Expected burst pause of {pause}s in sleep calls; got: {sleep_args}"


def test_report_block_rotate_false_skips_rotation_success(manager: ResilienceManager) -> None:
    """Verify that report_block does not rotate when rotate=False is passed (FIX-6)."""
    with patch.object(manager, "rotate_identity") as mock_rotate, patch.object(manager, "save_cache"):
        manager.report_block("1.1.1.1", reason="test", permanent=False, rotate=False)

    mock_rotate.assert_not_called()


def test_report_block_rotate_true_triggers_rotation_success(manager: ResilienceManager) -> None:
    """Verify that report_block triggers rotation when rotate=True (the default)."""
    with patch.object(manager, "rotate_identity") as mock_rotate, patch.object(manager, "save_cache"):
        manager.report_block("2.2.2.2", reason="test", permanent=False, rotate=True)

    mock_rotate.assert_called_once()
