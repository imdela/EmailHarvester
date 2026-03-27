import unittest
import subprocess
import os
import sys


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
