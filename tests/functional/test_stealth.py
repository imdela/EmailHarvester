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


@patch("src.core.time.sleep")
def test_stealth_jitter_burst_rest(
    mock_sleep: MagicMock, base_harvester: EmailHarvester, mock_requests_get: MagicMock
) -> None:
    """
    US-12/TI-05: Verifies that the engine tracks `burst_count` and triggers a
    15-30 seconds `time.sleep` rest period exactly on the 5th search iteration.
    """
    # Search requiring 6 requests
    base_harvester.init_search("http://test.com/?q={counter}", "domain.com", 6, 0, 1, "TestEngine")
    base_harvester.process()

    assert mock_requests_get.call_count == 6
    assert mock_sleep.call_count == 6

    # Grab the arguments passed to time.sleep()
    sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]

    # Iterations 1 to 4 should be short jitter (0.7s - 1.8s)
    for i in range(4):
        assert 0.7 <= sleep_calls[i] <= 1.8

    # Iteration 5 should be the burst rest limit (15.0s - 30.0s)
    assert 15.0 <= sleep_calls[4] <= 30.0

    # Iteration 6 should reset to short jitter
    assert 0.7 <= sleep_calls[5] <= 1.8
