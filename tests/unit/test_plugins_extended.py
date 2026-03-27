import importlib
import pkgutil
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import src.plugins


def get_plugin_names() -> list[str]:
    return [modname for _, modname, _ in pkgutil.iter_modules(src.plugins.__path__)]


@patch("requests.get")
@pytest.mark.parametrize("plugin_name", get_plugin_names())
def test_plugin_search_execution(mock_requests_get: MagicMock, plugin_name: str) -> None:
    """
    Test that each plugin's search function correctly initializes the harvester.
    """
    mod = importlib.import_module(f"src.plugins.{plugin_name}")

    # Mock response for plugins that call requests directly (like ask.py)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"contact@example.com"
    mock_response.encoding = "utf-8"
    mock_requests_get.return_value = mock_response

    # Mock EmailHarvester instance
    mock_app = MagicMock()
    mock_app.get_emails.return_value = ["test@example.com"]

    # Inject mock into plugin's global or local scope if it's there
    if hasattr(mod, "app_emailharvester"):
        mod.app_emailharvester = mock_app  # type: ignore[attr-defined]

    # Some plugins might use a Plugin class that registers the function
    # Let's mock registration and direct call

    with patch("src.plugins." + plugin_name + ".app_emailharvester", mock_app):
        try:
            # We need to handle the case where the plugin uses its own local app_emailharvester
            # which is set during Plugin initialization.
            _plugin_instance = mod.Plugin(mock_app, {"useragent": "test-ua", "proxy": None})

            # Now call the search function
            # Most plugins have a search(domain, limit) function
            emails = mod.search("example.com", 1)

            assert isinstance(emails, list)
            if plugin_name != "ask":
                mock_app.init_search.assert_called()
                mock_app.process.assert_called()
        except Exception as e:
            pytest.fail(f"Plugin {plugin_name} failed: {e}")


@pytest.mark.parametrize("plugin_name", get_plugin_names())
def test_plugin_registration(plugin_name: str) -> None:
    """
    Verify that each plugin correctly registers itself with the harvester.
    """
    mod = importlib.import_module(f"src.plugins.{plugin_name}")
    mock_app: Any = MagicMock()

    _plugin_instance = mod.Plugin(mock_app, {"useragent": "test-ua", "proxy": None})
    mock_app.register_plugin.assert_called()
    # Check that it registered with its own name
    args, _ = mock_app.register_plugin.call_args
    assert args[0] == plugin_name
