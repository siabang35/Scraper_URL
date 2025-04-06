import pytest
from app.scraper import CohesiveScraper, clean_text, extract_emails, validate_url

def test_clean_text():
    """Test text cleaning functionality"""
    assert clean_text(" Test   String  ") == "Test String"
    assert clean_text("Test@email.com") == "Test@email.com"
    assert clean_text("") == ""

def test_extract_emails():
    """Test email extraction"""
    text = "Contact us at test@example.com or support@example.com"
    emails = extract_emails(text)
    assert len(emails) == 2
    assert "test@example.com" in emails
    assert "support@example.com" in emails

def test_validate_url():
    """Test URL validation"""
    assert validate_url("https://example.com") == True
    assert validate_url("not-a-url") == False
    assert validate_url("") == False

@pytest.fixture
def scraper():
    """Fixture for scraper instance"""
    return CohesiveScraper()

def test_scraper_initialization(scraper):
    """Test scraper initialization"""
    assert scraper is not None
    assert hasattr(scraper, 'logger')

def test_scraper_company_info(scraper):
    """Test company info scraping"""
    # Mock test data
    test_url = "https://example.com"
    result = scraper.scrape_company_info(test_url)
    assert isinstance(result, dict)