from typing import Any
from unittest.mock import MagicMock

from src.plugins import linkedin


def test_url_formatting_placeholders() -> None:
    """
    Verify that search URLs use single {word}/{counter} braces.
    """
    mock_app = MagicMock()
    # Hijack init_search to capture URLs
    captured_urls = []

    def mock_init(url: str, *args: Any, **kwargs: Any) -> None:
        captured_urls.append(url)

    mock_app.init_search = mock_init
    linkedin.app_emailharvester = mock_app

    # Trigger plugin search
    linkedin.search("example.com", 10)

    # Inspect captured URLs
    for url in captured_urls:
        # Should contain single braces for string.format()
        assert "{word}" in url, f"URL {url} missing {{word}}"
        assert "{counter}" in url, f"URL {url} missing {{counter}}"
        # Should NOT contain double braces (common mistake)
        assert "{{word}}" not in url
        assert "{{counter}}" not in url
