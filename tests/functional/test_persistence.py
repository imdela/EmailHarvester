from unittest.mock import MagicMock

from src.core import EmailHarvester


def test_save_callback_triggered_on_discovery(base_harvester: EmailHarvester, mock_requests_get: MagicMock) -> None:
    """
    US-13: Verifies that save_callback is triggered as soon as emails are discovered in a batch.
    """
    mock_requests_get.return_value.content = b"<html>Contact: alice@test.com</html>"

    mock_save = MagicMock()
    base_harvester.save_callback = mock_save

    base_harvester.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
    base_harvester.do_search()

    # Callback should be called with found emails
    mock_save.assert_called_once()
    assert "alice@test.com" in mock_save.call_args[0][0]
