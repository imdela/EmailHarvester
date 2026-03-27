from unittest.mock import MagicMock

from src.plugins import duckduckgo


def test_duckduckgo_search_initialization() -> None:
    """
    Verify that duckduckgo plugin correctly initializes the harvester with YAML config.
    """
    mock_app = MagicMock()
    # Provide mock config for duckduckgo
    mock_app.get_plugin_config.return_value = [
        {
            "name": "DuckDuckGo (Lite)",
            "url": "https://lite.duckduckgo.com/lite/?q=%40{word}&s={counter}",
            "counter_init": 0,
            "counter_step": 30,
        }
    ]
    mock_app.get_emails.return_value = ["test@payoneer.com"]

    emails = duckduckgo.search("payoneer.com", 30, mock_app)

    assert "test@payoneer.com" in emails
    mock_app.init_search.assert_called_with(
        "https://lite.duckduckgo.com/lite/?q=%40{word}&s={counter}", "payoneer.com", 30, 0, 30, "DuckDuckGo (Lite)"
    )
    mock_app.process.assert_called_once()
