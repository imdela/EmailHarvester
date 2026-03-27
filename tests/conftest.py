"""
Global pytest configuration and shared fixtures for EmailHarvester tests.
Conforms strictly to PEP 257 and type hinting guidelines.
"""

from unittest.mock import MagicMock

import pytest

from src.core import EmailHarvester


@pytest.fixture
def base_harvester() -> MagicMock:
    """
    Provides a pre-configured, mocked EmailHarvester instance
    to be used across multiple test modules for consistent test state isolation.

    Returns:
        MagicMock: A mocked instance of EmailHarvester.
    """
    app = MagicMock(spec=EmailHarvester)
    app.get_emails.return_value = []
    # Setting up default states for typical tests
    app.search_limit = 100
    app.domain = "example.com"
    return app
