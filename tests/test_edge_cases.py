import unittest
from unittest.mock import MagicMock, patch
from src.core import EmailHarvester, SearchStatus

class TestSearchEdgeCases(unittest.TestCase):
    def setUp(self):
        self.app = EmailHarvester("UA", None)

    def test_init_with_limit_smaller_than_counter(self):
        """
        US-01/07: Verifies that if the limit is lower than the counter, the loop skips immediately.
        """
        self.app.init_search("http://test.com/", "test.com", 50, 100, 10, "TestEngine")
        self.app.process()
        self.assertEqual(self.app.counter, 100) # Loop should not run

    @patch("requests.get")
    def test_empty_response_content(self, mock_get):
        """
        US-11: Verifies that empty network content does not crash the parser.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b""
        mock_get.return_value.encoding = "UTF-8"
        
        self.app.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
        self.app.do_search()
        self.assertEqual(len(self.app.get_emails()), 0)

    def test_persistence_without_filename(self):
        """
        US-13: Verifies that the save_email_callback handles cases where no filename is provided without crashing.
        """
        # This is already handled in cli.py logically, but let's verify if the engine calls it safely
        self.app.save_callback = None
        self.app.parser.extract("test@test.com", "test.com")
        # Should not raise exception
        if self.app.save_callback:
            self.app.save_callback(["test@test.com"])

    @patch("requests.get")
    def test_bad_decoding_recovery(self, mock_get):
        """
        US-02: Verifies that even if decoding fails initially, we use the fallback or raise error.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"\xff\xfeT\x00e\x00s\x00t" # UTF-16
        mock_get.return_value.encoding = None 
        
        self.app.init_search("http://test.com/", "test.com", 1, 0, 1, "TestEngine")
        self.app.do_search() # Should handle the decoding errors="replace" correctly

    def test_proxy_url_validation(self):
        """
        US-03: Verifies that checkProxyUrl rejects malformed proxy strings.
        """
        import argparse
        from src.core import checkProxyUrl
        with self.assertRaises(argparse.ArgumentTypeError):
            checkProxyUrl("127.0.0.1:8080")
        with self.assertRaises(argparse.ArgumentTypeError):
            checkProxyUrl("ftp://127.0.0.1:8080")
        res = checkProxyUrl("http://proxy.com:8080")
        self.assertEqual(res.scheme, "http")

    def test_domain_validation(self):
        """
        US-03: Verifies that checkDomain rejects obviously invalid domains.
        """
        import argparse
        from src.core import checkDomain
        with self.assertRaises(argparse.ArgumentTypeError):
            checkDomain("invalid_domain")
        self.assertEqual(checkDomain("google.com"), "google.com")

if __name__ == "__main__":
    unittest.main()
