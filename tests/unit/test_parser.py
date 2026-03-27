import pytest

from src.core import MyParser


@pytest.fixture
def parser() -> MyParser:
    return MyParser()


def test_extract_emails_valid(parser: MyParser) -> None:
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
    parser.extract(html_content, "example.com")
    emails = parser.emails()

    assert "alice.smith@example.com" in emails
    assert "bob-jones_123+newsletter@example.com" in emails
    assert "support@example.com" in emails
    assert len(emails) == 3


def test_unique_emails(parser: MyParser) -> None:
    # Result should deduplicate duplicate emails
    html_content = "contact@example.com ... contact@example.com"
    parser.extract(html_content, "example.com")
    emails = parser.emails()
    assert len(emails) == 1
    assert emails[0] == "contact@example.com"
