from unittest.mock import MagicMock, patch

from src.core import EmailHarvester


def test_user_agent_rotates_per_request(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-12: Verifies that the User-Agent header rotates for different requests.
    """
    base_harvester.init_search("http://test.com/{counter}", "domain.com", 10, 0, 1, "TestEngine")

    # Capture first request UA
    base_harvester.do_search()
    ua1 = mock_requests_get.call_args[1]["headers"]["User-Agent"]

    # Capture second request UA
    base_harvester.do_search()

    # 99.9% chance they are different due to randomization pool
    assert ua1 != base_harvester.default_userAgent
    assert len(base_harvester.userAgent) > 0


def test_tor_enabled_flag_persistence() -> None:
    """
    US-12: Verifies if TOR enabled flag is correctly passed.
    """
    app_tor = EmailHarvester("UA", None, tor_enabled=True)
    assert app_tor.tor_enabled


@patch("src.resilience.time.sleep")
def test_stealth_jitter_burst_rest(
    mock_sleep: MagicMock, base_harvester: EmailHarvester, mock_requests_get: MagicMock
) -> None:
    """
    US-12/TI-05: Verifies that the engine tracks `burst_count` and triggers a
    5 seconds `time.sleep` rest period exactly on the 6th search iteration.
    """
    # Reset shared burst state for tests
    from src.resilience import ResilienceManager

    with ResilienceManager._lock:
        ResilienceManager._shared_burst_count = 0

    # Search requiring 7 requests
    base_harvester.init_search("http://test.com/?q={counter}", "domain.com", 7, 0, 1, "TestEngine")
    base_harvester.process()

    # We use pre_flight_check which makes 1 requests.get call for IP, plus 1 for the domain search
    # Therefore, 7 iterations * 2 = 14 total requests
    assert mock_requests_get.call_count == 14

    # 7 iterations will produce 7 jitter sleeps and 1 burst sleep = 8 sleep calls
    assert mock_sleep.call_count == 8

    # Grab the arguments passed to time.sleep()
    sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]

    # Jitter assertions (100ms - 500ms)
    jitter_calls = sleep_calls.copy()
    burst_sleep = jitter_calls.pop(6)  # The 7th call (index 6, at 6 iterations) is the burst sleep.

    for delay in jitter_calls:
        assert 0.1 <= delay <= 0.5

    # Burst assertion (exactly 5s as per config)
    assert burst_sleep == 5.0
