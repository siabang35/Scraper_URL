from typing import Dict, Optional, List, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import json
import time
from .base_scraper import BaseScraper
from .utils import clean_text, extract_emails, validate_url
from app.config import SCRAPING_PATTERNS, SCRAPING_CONFIG
import logging

class CohesiveScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    def scrape_company_info(self, url: str) -> Dict[str, Any]:
        """Scrape company information from a given URL"""
        if not validate_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return {}
            
        try:
            driver = self.get_driver()
            self.logger.info(f"Starting to scrape: {url}")
            
            def scrape_attempt():
                driver.get(url)
                wait = WebDriverWait(driver, SCRAPING_CONFIG['timeout'])
                
                # Extract all available company information
                company_data = {
                    'name': self._extract_company_name(driver, wait),
                    'website': url,
                    'email': self._extract_email(driver),
                    'phone': self._extract_phone(driver),
                    'employees': self._extract_employee_count(driver),
                    'location': self._extract_location(driver),
                    'industry': self._extract_industry(driver),
                    'social_links': self._extract_social_links(driver),
                    'technologies': self._extract_technologies(driver),
                    'meta_data': self._extract_meta_data(driver),
                    'contact_info': self._extract_contact_info(driver),
                    'description': self._extract_description(driver),
                    'founded_year': self._extract_founded_year(driver),
                    'company_size': self._extract_company_size(driver),
                    'revenue_range': self._extract_revenue_range(driver),
                    'headquarters': self._extract_headquarters(driver),
                    'keywords': self._extract_keywords(driver)
                }
                
                return self.clean_data(company_data)
                
            # Use retry mechanism for scraping
            result = self.retry_on_failure(scrape_attempt)
            
            driver.quit()
            return result or {}
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return {}
            
    def _extract_company_name(self, driver, wait) -> Optional[str]:
        """Extract company name using multiple methods"""
        selectors = [
            ('meta[property="og:site_name"]', 'content'),
            ('meta[name="application-name"]', 'content'),
            ('meta[property="og:title"]', 'content'),
            ('title', 'text'),
            ('h1', 'text'),
            ('.company-name', 'text'),
            ('#company-name', 'text')
        ]
        
        for selector, attr in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                value = element.get_attribute(attr) if attr != 'text' else element.text
                if value:
                    return clean_text(value)
            except (TimeoutException, NoSuchElementException):
                continue
        return None
        
    def _extract_email(self, driver) -> Optional[str]:
        """Extract email addresses from the page"""
        page_source = driver.page_source
        emails = extract_emails(page_source)
        
        # Filter out common invalid emails
        valid_emails = [
            email for email in emails
            if not any(invalid in email.lower() for invalid in ['example', 'test', 'placeholder'])
        ]
        
        return valid_emails[0] if valid_emails else None
        
    def _extract_phone(self, driver) -> Optional[str]:
        """Extract phone numbers using regex patterns"""
        page_source = driver.page_source
        phone_pattern = SCRAPING_PATTERNS['phone']
        phones = re.findall(phone_pattern, page_source)
        
        # Clean and validate phone numbers
        cleaned_phones = []
        for phone in phones:
            cleaned = re.sub(r'[^\d+]', '', phone)
            if len(cleaned) >= 10:
                cleaned_phones.append(cleaned)
                
        return cleaned_phones[0] if cleaned_phones else None
        
    def _extract_employee_count(self, driver) -> Optional[int]:
        """Extract employee count from various sources"""
        patterns = [
            r'(\d+)\+?\s*employees',
            r'team of (\d+)\+?',
            r'(\d+)\+?\s*people',
            r'company size:\s*(\d+)',
        ]
        
        page_source = driver.page_source.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                try:
                    return int(re.sub(r'[^\d]', '', matches[0]))
                except ValueError:
                    continue
        return None
        
    def _extract_location(self, driver) -> Optional[str]:
        """Extract company location"""
        location_selectors = [
            ('meta[property="business:contact_data:locality"]', 'content'),
            ('meta[property="og:locality"]', 'content'),
            ('.address', 'text'),
            ('.location', 'text'),
            ('[itemtype="http://schema.org/PostalAddress"]', 'text')
        ]
        
        for selector, attr in location_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                value = element.get_attribute(attr) if attr != 'text' else element.text
                if value:
                    return clean_text(value)
            except NoSuchElementException:
                continue
                
        return None
        
    def _extract_industry(self, driver) -> Optional[str]:
        """Extract company industry"""
        industry_selectors = [
            ('meta[property="business:industry"]', 'content'),
            ('.industry', 'text'),
            ('#industry', 'text'),
            ('[itemprop="industry"]', 'text')
        ]
        
        for selector, attr in industry_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                value = element.get_attribute(attr) if attr != 'text' else element.text
                if value:
                    return clean_text(value)
            except NoSuchElementException:
                continue
                
        return None
        
    def _extract_social_links(self, driver) -> Dict[str, str]:
        """Extract social media links"""
        social_links = {}
        page_source = driver.page_source
        
        for platform, pattern in SCRAPING_PATTERNS['social_media'].items():
            matches = re.findall(pattern, page_source)
            if matches:
                social_links[platform] = f"https://{matches[0]}"
                
        return social_links
        
    def _extract_technologies(self, driver) -> List[str]:
        """Extract technologies used by the company"""
        technologies = set()
        
        # Check meta tags
        meta_tags = driver.find_elements(By.TAG_NAME, 'meta')
        for tag in meta_tags:
            content = tag.get_attribute('content')
            if content:
                tech_matches = re.findall(r'(React|Angular|Vue|Python|Java|AWS|Azure|Docker)', content)
                technologies.update(tech_matches)
        
        # Check script tags
        script_tags = driver.find_elements(By.TAG_NAME, 'script')
        for script in script_tags:
            src = script.get_attribute('src')
            if src:
                tech_matches = re.findall(r'(react|angular|vue|jquery|bootstrap)', src.lower())
                technologies.update([t.capitalize() for t in tech_matches])
        
        return list(technologies)
        
    def _extract_meta_data(self, driver) -> Dict[str, str]:
        """Extract metadata from page"""
        meta_data = {}
        meta_tags = driver.find_elements(By.TAG_NAME, 'meta')
        
        for tag in meta_tags:
            name = tag.get_attribute('name') or tag.get_attribute('property')
            content = tag.get_attribute('content')
            if name and content:
                meta_data[name] = content
                
        return meta_data
        
    def _extract_contact_info(self, driver) -> Dict[str, Any]:
        """Extract all contact information"""
        contact_info = {
            'emails': extract_emails(driver.page_source),
            'phones': re.findall(SCRAPING_PATTERNS['phone'], driver.page_source),
            'address': self._extract_location(driver)
        }
        return {k: v for k, v in contact_info.items() if v}
        
    def _extract_description(self, driver) -> Optional[str]:
        """Extract company description"""
        description_selectors = [
            ('meta[name="description"]', 'content'),
            ('meta[property="og:description"]', 'content'),
            ('.company-description', 'text'),
            ('.about-us', 'text')
        ]
        
        for selector, attr in description_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                value = element.get_attribute(attr) if attr != 'text' else element.text
                if value:
                    return clean_text(value)
            except NoSuchElementException:
                continue
                
        return None
        
    def _extract_founded_year(self, driver) -> Optional[int]:
        """Extract company founding year"""
        patterns = [
            r'[Ff]ounded in (\d{4})',
            r'[Ee]stablished in (\d{4})',
            r'[Ss]ince (\d{4})'
        ]
        
        page_source = driver.page_source
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                try:
                    year = int(matches[0])
                    if 1800 <= year <= time.gmtime().tm_year:
                        return year
                except ValueError:
                    continue
                    
        return None
        
    def _extract_company_size(self, driver) -> Optional[str]:
        """Extract company size range"""
        size_patterns = [
            r'(\d+)-(\d+)\s+employees',
            r'(\d+)\+\s+employees',
            r'company size:\s*([^<>\n]+)'
        ]
        
        page_source = driver.page_source.lower()
        
        for pattern in size_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                return matches[0] if isinstance(matches[0], str) else f"{matches[0][0]}-{matches[0][1]}"
                
        return None
        
    def _extract_revenue_range(self, driver) -> Optional[str]:
        """Extract company revenue range"""
        revenue_patterns = [
            r'revenue[:\s]+\$(\d+(?:\.\d+)?)[MBK]?-\$(\d+(?:\.\d+)?)[MBK]?',
            r'annual revenue[:\s]+\$(\d+(?:\.\d+)?)[MBK]?'
        ]
        
        page_source = driver.page_source
        
        for pattern in revenue_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                return matches[0] if isinstance(matches[0], str) else f"${matches[0][0]}-${matches[0][1]}"
                
        return None
        
    def _extract_headquarters(self, driver) -> Optional[str]:
        """Extract company headquarters location"""
        hq_selectors = [
            ('[itemtype="http://schema.org/PostalAddress"]', 'text'),
            ('.headquarters', 'text'),
            ('.hq-location', 'text'),
            ('meta[property="business:contact_data:locality"]', 'content')
        ]
        
        for selector, attr in hq_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                value = element.get_attribute(attr) if attr != 'text' else element.text
                if value:
                    return clean_text(value)
            except NoSuchElementException:
                continue
                
        return None
        
    def _extract_keywords(self, driver) -> List[str]:
        """Extract relevant keywords from the page"""
        keywords = set()
        
        # Check meta keywords
        try:
            meta_keywords = driver.find_element(By.CSS_SELECTOR, 'meta[name="keywords"]')
            if meta_keywords:
                keywords.update(meta_keywords.get_attribute('content').split(','))
        except NoSuchElementException:
            pass
            
        # Extract from headings
        for tag in ['h1', 'h2', 'h3']:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for element in elements:
                words = element.text.split()
                keywords.update(words)
                
        return [clean_text(k) for k in keywords if len(clean_text(k)) > 2]