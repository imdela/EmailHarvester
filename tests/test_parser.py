import os
import sys
import unittest

# Insert project root to path for importing EmailHarvester
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.core import MyParser
except ImportError as e:
    print(f"Failed to import MyParser: {e}")
    sys.exit(1)


class TestMyParser(unittest.TestCase):
    def setUp(self):
        self.parser = MyParser()

    def test_extract_emails_valid(self):
        # A mix of valid and slightly noisy string simulating search engine return
        html_content = """
        <title>Search results</title>
        <div>
            <h1>Contact us</h1>
            <p>Reach out to alice.smith@example.com for more information.</p>
            <p>Or try bob-jones_123+newsletter@example.com</p>
            <b>Support: support@example.com</b>
        </div>
        """
        self.parser.extract(html_content, "example.com")
        emails = self.parser.emails()

        self.assertIn("alice.smith@example.com", emails)
        self.assertIn("bob-jones_123+newsletter@example.com", emails)
        self.assertIn("support@example.com", emails)
        self.assertEqual(len(emails), 3)

    def test_unique_emails(self):
        # Result should deduplicate duplicate emails
        html_content = "contact@example.com ... contact@example.com"
        self.parser.extract(html_content, "example.com")
        emails = self.parser.emails()
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], "contact@example.com")


if __name__ == "__main__":
    unittest.main()
