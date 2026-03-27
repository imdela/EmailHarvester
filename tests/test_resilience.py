import unittest
from unittest.mock import MagicMock, patch
from src.core import EmailHarvester, SearchStatus, SearchBlockedError, RateLimitError

class TestSearchResilience(unittest.TestCase):
    def setUp(self):
        self.app = EmailHarvester("UA", None)

    @patch("requests.get")
    def test_block_detection_raises_custom_errors(self, mock_get):
        """
        US-11: Verifies that CAPTCHAs and 429 errors are detected and raise expected custom errors in the loop.
        """
        # Scenario 1: CAPTCHA in HTML
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html>Please solve this CAPTCHA</html>"
        mock_get.return_value.encoding = "UTF-8"
        
        self.app.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
        with self.assertRaises(SearchBlockedError) as cm:
            self.app.do_search()
        self.assertIn("Bot challenge detected", str(cm.exception))
        self.assertEqual(self.app.status, SearchStatus.PARTIAL_CAPTCHA)

        # Scenario 2: HTTP 429
        mock_get.return_value.status_code = 429
        with self.assertRaises(RateLimitError) as cm2:
            self.app.do_search()
        self.assertEqual(self.app.status, SearchStatus.FAILED_RATE_LIMIT)

if __name__ == "__main__":
    unittest.main()
