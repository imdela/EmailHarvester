from unittest.mock import MagicMock

import pytest

from src.core import EmailHarvester, RateLimitError, SearchBlockedError, SearchStatus


def test_block_detection_captcha(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-11: Verifies that CAPTCHAs are detected and raise expected custom errors.
    """
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.content = b"<html>Please solve this CAPTCHA</html>"

    base_harvester.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")

    with pytest.raises(SearchBlockedError) as excinfo:
        base_harvester.do_search()

    assert "Bot challenge detected" in str(excinfo.value)
    assert base_harvester.status == SearchStatus.PARTIAL_CAPTCHA


def test_block_detection_rate_limit(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-11: Verifies that HTTP 429 raises expected custom error.
    """
    mock_requests_get.return_value.status_code = 429

    base_harvester.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")

    with pytest.raises(RateLimitError):
        base_harvester.do_search()

    assert base_harvester.status == SearchStatus.FAILED_RATE_LIMIT
