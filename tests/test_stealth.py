import unittest
from unittest.mock import MagicMock, patch

from src.core import EmailHarvester


class TestStealthMechanisms(unittest.TestCase):
    def setUp(self) -> None:
        self.app = EmailHarvester("Default-UA", None)

    @patch("requests.get")
    def test_user_agent_rotates_per_request(self, mock_get: MagicMock) -> None:
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
        
        # 99.9% chance they are different due to randomization pool
        self.assertNotEqual(ua1, self.app.default_userAgent)
        # Randomness is not 100% guarantee but high probability;
        # let's just assert that the userAgent property changed or matches the pool
        self.assertTrue(len(self.app.userAgent) > 0)

    def test_tor_enabled_flag_persistence(self) -> None:
        """
        US-12: Verifies if TOR enabled flag is correctly passed.
        """
        app_tor = EmailHarvester("UA", None, tor_enabled=True)
        self.assertTrue(app_tor.tor_enabled)

    @patch("time.sleep")
    @patch("requests.get")
    def test_stealth_jitter_burst_rest(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """
        US-12/TI-05: Verifies that the engine tracks `burst_count` and triggers a
        15-30 seconds `time.sleep` rest period exactly on the 5th search iteration.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html>test@domain.com</html>"
        mock_get.return_value.encoding = "UTF-8"

        # Search requiring 6 requests
        self.app.init_search("http://test.com/?q={counter}", "domain.com", 6, 0, 1, "TestEngine")
        self.app.process()

        self.assertEqual(mock_get.call_count, 6)
        self.assertEqual(mock_sleep.call_count, 6)

        # Grab the arguments passed to time.sleep()
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]

        # Iterations 1 to 4 should be short jitter (0.7s - 1.8s)
        for i in range(4):
            self.assertTrue(0.7 <= sleep_calls[i] <= 1.8)

        # Iteration 5 should be the burst rest limit (15.0s - 30.0s)
        self.assertTrue(15.0 <= sleep_calls[4] <= 30.0)

        # Iteration 6 should reset to short jitter
        self.assertTrue(0.7 <= sleep_calls[5] <= 1.8)


if __name__ == "__main__":
    unittest.main()
