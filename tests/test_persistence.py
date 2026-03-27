import unittest
import os
from unittest.mock import MagicMock, patch
from src.core import EmailHarvester

class TestPersistenceStreaming(unittest.TestCase):
    def setUp(self):
        self.app = EmailHarvester("UA", None)

    @patch("requests.get")
    def test_save_callback_triggered_on_discovery(self, mock_get):
        """
        US-13: Verifies that save_callback is triggered as soon as emails are discovered in a batch.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html>Contact: alice@test.com</html>"
        mock_get.return_value.encoding = "UTF-8"

        mock_save = MagicMock()
        self.app.save_callback = mock_save
        
        self.app.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
        self.app.do_search()
        
        # Callback should be called with found emails
        mock_save.assert_called_once()
        self.assertIn("alice@test.com", mock_save.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
