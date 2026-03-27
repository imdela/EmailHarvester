from src.core import EmailHarvester, EngineProbe, LinkExtractor


def test_link_extractor_valid_urls() -> None:
    html = """
    <html>
        <body>
            <a href="https://example.com/about">About Us</a>
            <a href="https://google.com/search?q=test">Search</a>
            <a href="https://other.com/page">Other</a>
            <a href="http://testing.example.com/contact">Contact</a>
        </body>
    </html>
    """
    domain = "example.com"
    links = LinkExtractor.extract_links(html, domain)

    # google should be blacklisted
    assert "https://google.com/search?q=test" not in links
    # example.com domain targets should be kept
    assert "https://example.com/about" in links
    assert "http://testing.example.com/contact" in links
    # other domain should be excluded since domain is "example.com"
    assert "https://other.com/page" not in links


def test_link_extractor_blacklisting() -> None:
    html = """
    <a href="https://www.bing.com/results">Bing</a>
    <a href="https://search.yahoo.com/yhs">Yahoo</a>
    <a href="https://example.com/valid">Valid</a>
    """
    domain = "example.com"
    links = LinkExtractor.extract_links(html, domain)

    assert "https://example.com/valid" in links
    assert len(links) == 1


def test_engine_probe_initialization() -> None:
    harvester = EmailHarvester("test-ua", None, tor_enabled=False)
    probe = EngineProbe(harvester)
    # Basic check that it registers and returns True for dummy verification
    # since we didn't implement complex network logic in the probe yet
    assert probe.verify_plugin("google") is True
    assert probe.verify_plugin("non-existent") is False
