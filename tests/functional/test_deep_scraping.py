from unittest.mock import MagicMock, patch

from src.core import EmailHarvester, LinkExtractor


def test_deep_scraping_off_by_default() -> None:
    harvester = EmailHarvester("UA", None)
    assert harvester.deep_scraping is False


@patch("src.core.requests.get")
def test_deep_scraping_logic_visit_links(mock_get: MagicMock) -> None:
    # Setup harvester with deep scraping enabled
    harvester = EmailHarvester("UA", None)
    harvester.deep_scraping = True
    harvester.word = "target.com"

    # Mock search result with a link to target.com
    html_search_result = '<html><body>Some results <a href="https://target.com/page1">Link 1</a></body></html>'
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.content = html_search_result.encode("utf-8")
    mock_response1.encoding = "utf-8"

    # Mock deep-scraping result containing an email
    html_deep_result = "<html><body>Contact: alice@target.com</body></html>"
    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.content = html_deep_result.encode("utf-8")
    mock_response2.encoding = "utf-8"

    # Mock requests.get to return search results first, then the deep-scraped page
    mock_get.side_effect = [mock_response1, mock_response2]

    # Configure search
    harvester.init_search("http://engine.com/{counter}&q={word}", "target.com", 1, 0, 1, "TestEngine")

    # Run one search step
    harvester.do_search()

    # 2 requests should have been made: 1 search + 1 deep scrape
    assert mock_get.call_count == 2

    # Emails should include the one from deep page
    emails = harvester.get_emails()
    assert "alice@target.com" in emails
    assert len(emails) == 1


def test_link_extractor_filters_search_engine_noise() -> None:
    # Verify that search engines are blacklisted from deep scraping
    html = """
    <a href="https://www.google.com/search">Google Search link</a>
    <a href="https://target.com/valid">Target Page</a>
    """
    links = LinkExtractor.extract_links(html, "target.com")
    assert "https://target.com/valid" in links
    assert "https://www.google.com/search" not in links
