"""
Global pytest configuration and shared fixtures for EmailHarvester tests.
Conforms strictly to PEP 257 and type hinting guidelines.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from src.core import EmailHarvester


@pytest.fixture
def base_harvester() -> EmailHarvester:
    """
    Provides a pre-configured, clean EmailHarvester instance
    to be used across multiple test modules for consistent test state isolation.
    """
    return EmailHarvester(userAgent="Default-UA", proxy=None, tor_enabled=False)


@pytest.fixture
def mock_requests_get() -> Generator[MagicMock, None, None]:
    """
    Provides a reusable stateful mock for requests.get to simulate search engine responses,
    preventing actual outgoing queries and protecting proxy limits.
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html>test@domain.com</html>"
        mock_get.return_value.encoding = "UTF-8"
        yield mock_get
