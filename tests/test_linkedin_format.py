import unittest
from unittest.mock import MagicMock
from src.plugins import linkedin

class TestLinkedInPlugin(unittest.TestCase):
    """
    Test suite for LinkedIn plugin technical compliance.
    """
    
    def test_url_formatting_placeholders(self):
        """
        Verify that search URLs use single {word}/{counter} braces.
        """
        mock_app = MagicMock()
        # Hijack init_search to capture URLs
        captured_urls = []
        def mock_init(url, *args, **kwargs):
            captured_urls.append(url)
        
        mock_app.init_search = mock_init
        linkedin.app_emailharvester = mock_app
        
        # Trigger plugin search
        linkedin.search("example.com", 10)
        
        # Inspect captured URLs
        for url in captured_urls:
            with self.subTest(url=url):
                # Should contain single braces for string.format()
                self.assertIn("{word}", url, f"URL {url} missing {{word}}")
                self.assertIn("{counter}", url, f"URL {url} missing {{counter}}")
                # Should NOT contain double braces (common mistake)
                self.assertNotIn("{{word}}", url)
                self.assertNotIn("{{counter}}", url)

if __name__ == '__main__':
    unittest.main()
