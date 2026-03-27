import os
import subprocess
import sys
import unittest


class TestEmailHarvesterCLI(unittest.TestCase):
    def setUp(self):
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "EmailHarvester.py",
        )
        self.venv_python = sys.executable  # using the runner's python

    def test_invalid_engine_parsing_fails_gracefully(self):
        result = subprocess.run(
            [self.venv_python, self.script_path, "-d", "example.com", "-e", "notexist"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("[-] Search engine plugin not found: notexist", result.stdout)

    def test_comma_separated_engines_invalid_mix_fails(self):
        result = subprocess.run(
            [
                self.venv_python,
                self.script_path,
                "-d",
                "example.com",
                "-e",
                "ask,notexist",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("[-] Search engine plugin not found: notexist", result.stdout)


if __name__ == "__main__":
    unittest.main()

class TestCliExecution(unittest.TestCase):
    def test_run_thread_returns_tuple(self):
        """
        US-09/11: Verifies thread workers return the required tuple structure (emails, status).
        """
        from src.cli import run_engine_thread
        from unittest.mock import MagicMock, patch
        
        with patch("src.cli.EmailHarvester") as mock_app:
            # Setup mock search engine
            mock_plugin = {"search": MagicMock(return_value=["test@domain.com"])}
            mock_app.return_value.get_plugins.return_value = {"bing": mock_plugin}
            mock_app.return_value.status = "SUCCESS"
            
            mock_progress = MagicMock()
            
            result, status = run_engine_thread(
                "bing", "domain.com", 1, "UA", None, False, mock_progress
            )
            
            self.assertEqual(result, ["test@domain.com"])
            self.assertEqual(status, "SUCCESS")
