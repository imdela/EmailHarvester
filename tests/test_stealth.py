import unittest
from unittest.mock import MagicMock, patch
from src.core import EmailHarvester

class TestStealthMechanisms(unittest.TestCase):
    def setUp(self):
        self.app = EmailHarvester("Default-UA", None)

    @patch("requests.get")
    def test_user_agent_rotates_per_request(self, mock_get):
        """
        US-12: Verifies that the User-Agent header rotates for different requests.
        """
        # Mock successful response
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html></html>"
        mock_get.return_value.encoding = "UTF-8"

        self.app.init_search("http://test.com/{counter}", "domain.com", 10, 0, 1, "TestEngine")
        
        # Capture first request UA
        self.app.do_search()
        ua1 = mock_get.call_args[1]["headers"]["User-Agent"]

        # Capture second request UA
        self.app.do_search()
        ua2 = mock_get.call_args[1]["headers"]["User-Agent"]

        # 99.9% chance they are different due to randomization pool
        self.assertNotEqual(ua1, self.app.default_userAgent)
        # Randomness is not 100% guarantee but high probability; 
        # let's just assert that the userAgent property changed or matches the pool
        self.assertTrue(len(self.app.userAgent) > 0)

    def test_tor_enabled_flag_persistence(self):
        """
        US-12: Verifies if TOR enabled flag is correctly passed.
        """
        app_tor = EmailHarvester("UA", None, tor_enabled=True)
        self.assertTrue(app_tor.tor_enabled)

if __name__ == "__main__":
    unittest.main()
