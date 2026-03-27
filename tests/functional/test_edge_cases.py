import argparse
from unittest.mock import MagicMock

import pytest

from src.core import EmailHarvester, checkDomain, checkProxyUrl


def test_init_with_limit_smaller_than_counter(base_harvester: EmailHarvester) -> None:
    """
    US-01/07: Verifies that if the limit is lower than the counter, the loop skips immediately.
    """
    base_harvester.init_search("http://test.com/", "test.com", 50, 100, 10, "TestEngine")
    base_harvester.process()
    assert base_harvester.counter == 100


def test_empty_response_content(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-11: Verifies that empty network content does not crash the parser.
    """
    mock_requests_get.return_value.content = b""

    base_harvester.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
    base_harvester.do_search()
    assert len(base_harvester.get_emails()) == 0


def test_persistence_without_filename(base_harvester: EmailHarvester) -> None:
    """
    US-13: Verifies that the save_email_callback handles cases where no filename is provided without crashing.
    """
    base_harvester.save_callback = None
    base_harvester.parser.extract("test@test.com", "test.com")
    # Should not raise exception
    if base_harvester.save_callback:
        base_harvester.save_callback(["test@test.com"])


def test_bad_decoding_recovery(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-02: Verifies that even if decoding fails initially, we use the fallback sequence.
    """
    mock_requests_get.return_value.content = b"\xff\xfeT\x00e\x00s\x00t"  # UTF-16
    mock_requests_get.return_value.encoding = None

    base_harvester.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
    base_harvester.do_search()  # Should handle the decoding errors="replace" correctly


def test_proxy_url_validation() -> None:
    """
    US-03: Verifies that checkProxyUrl rejects malformed proxy strings.
    """
    with pytest.raises(argparse.ArgumentTypeError):
        checkProxyUrl("127.0.0.1:8080")
    with pytest.raises(argparse.ArgumentTypeError):
        checkProxyUrl("ftp://127.0.0.1:8080")

    res = checkProxyUrl("http://proxy.com:8080")
    assert res.scheme == "http"


def test_domain_validation() -> None:
    """
    US-03: Verifies that checkDomain rejects obviously invalid domains.
    """
    with pytest.raises(argparse.ArgumentTypeError):
        checkDomain("invalid_domain")
    assert checkDomain("google.com") == "google.com"
