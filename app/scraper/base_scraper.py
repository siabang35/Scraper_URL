from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import logging.config
import time
import os
import random
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from app.config import SCRAPING_CONFIG, LOGGING_CONFIG, RATE_LIMITS
from .utils import clean_text, extract_emails, validate_url

# Setup logging
logging.config.dictConfig(LOGGING_CONFIG)

class BaseScraper(ABC):
    """Base class for web scraping with advanced features"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_agent = UserAgent()
        self.session = self._create_session()
        self.last_request_time = 0
        self._driver = None
        self._wait = None
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with rotating file handler"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.logger.info("Initializing scraper...")

    def _create_session(self) -> requests.Session:
        """Create and configure HTTP session with rotating headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        return session

    def get_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver with advanced anti-detection"""
        if self._driver is not None:
            return self._driver

        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.user_agent.random}')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-javascript')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth settings
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-canvas-aa')
        options.add_argument('--disable-2d-canvas-clip-aa')
        options.add_argument('--disable-accelerated-2d-canvas')
        
        self.logger.debug("Chrome options configured.")

        # Proxy configuration
        proxy_cfg = SCRAPING_CONFIG.get('proxy', {})
        if proxy_cfg.get('enabled'):
            server = proxy_cfg.get('server')
            username = proxy_cfg.get('username')
            password = proxy_cfg.get('password')
            if server:
                auth = f"{username}:{password}@" if username and password else ""
                proxy_url = f"{auth}{server}"
                options.add_argument(f'--proxy-server={proxy_url}')
                self.logger.info(f"🔌 Using proxy: {proxy_url}")

        # ChromeDriver setup
        driver_path = SCRAPING_CONFIG.get('chrome_driver_path')
        driver_file = Path(driver_path) if driver_path else None

        if not driver_file or not driver_file.exists():
            raise FileNotFoundError(f" ChromeDriver not found at: {driver_path}")

        self.logger.info(f" Using ChromeDriver at: {driver_file}")

        try:
            service = Service(executable_path=str(driver_file))
            self._driver = webdriver.Chrome(service=service, options=options)
            self._driver.set_page_load_timeout(SCRAPING_CONFIG.get('timeout', 30))
            self._wait = WebDriverWait(self._driver, SCRAPING_CONFIG.get('timeout', 30))
            
            # Execute stealth JavaScript
            self._execute_stealth_js()
            
            self.logger.info("ChromeDriver initialized successfully.")
            return self._driver
            
        except WebDriverException as e:
            self.logger.error(f" Failed to start ChromeDriver: {e}")
            raise RuntimeError("ChromeDriver initialization failed. Check compatibility.")

    def _execute_stealth_js(self):
        """Execute JavaScript to mask automation"""
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """
        try:
            self._driver.execute_script(stealth_js)
        except Exception as e:
            self.logger.warning(f"Failed to execute stealth JS: {e}")

    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """Wait for element with improved error handling"""
        timeout = timeout or SCRAPING_CONFIG.get('timeout', 30)
        try:
            return WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {value}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element: {e}")
            return None

    def handle_rate_limiting(self, rate_limit_type: str = 'default'):
        """Apply intelligent rate limiting with burst handling"""
        rate_limit = RATE_LIMITS.get(rate_limit_type, RATE_LIMITS['default'])
        min_interval = 1.0 / rate_limit['requests_per_second']
        burst_size = rate_limit.get('burst_size', 1)

        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Add random jitter to appear more human-like
        jitter = random.uniform(0.1, 0.5)
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last + jitter
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def extract_text_from_element(self, element_or_selector: Any, clean: bool = True) -> Optional[str]:
        """Extract text from element with cleaning"""
        try:
            if isinstance(element_or_selector, str):
                element = self._driver.find_element(By.CSS_SELECTOR, element_or_selector)
            else:
                element = element_or_selector
                
            text = element.text or element.get_attribute('textContent')
            return clean_text(text) if clean else text
            
        except (NoSuchElementException, AttributeError):
            return None

    def get_page_source_parsed(self) -> BeautifulSoup:
        """Get parsed page source with BeautifulSoup"""
        return BeautifulSoup(self._driver.page_source, 'html.parser')

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data comprehensively"""
        if not data:
            return False
            
        required_fields = SCRAPING_CONFIG.get('required_fields', ['name', 'website'])
        
        # Check required fields
        if not all(data.get(field) for field in required_fields):
            return False
            
        # Validate specific fields
        if 'email' in data and data['email']:
            if not self._validate_email_format(data['email']):
                return False
                
        if 'website' in data and data['website']:
            if not validate_url(data['website']):
                return False
                
        if 'phone' in data and data['phone']:
            if not self._validate_phone_format(data['phone']):
                return False
                
        return True

    def _validate_email_format(self, email: str) -> bool:
        """Validate email format with strict rules"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
            
        # Additional validation
        domain = email.split('@')[1]
        invalid_domains = ['example.com', 'test.com', 'localhost']
        if domain.lower() in invalid_domains:
            return False
            
        return True

    def _validate_phone_format(self, phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Remove all non-numeric characters
        digits = re.sub(r'\D', '', phone)
        # Check if we have a reasonable number of digits
        return 10 <= len(digits) <= 15

    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize all data fields"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_val = clean_text(value)
            elif isinstance(value, (list, tuple)):
                cleaned_val = [clean_text(str(v)) for v in value if v]
            elif isinstance(value, dict):
                cleaned_val = self.clean_data(value)
            else:
                cleaned_val = value
            if cleaned_val:  # Remove empty values
                cleaned[key] = cleaned_val
        return cleaned

    def retry_on_failure(self, func: callable, max_retries: int = None) -> Any:
        """Retry function with exponential backoff and cleanup"""
        max_retries = max_retries or SCRAPING_CONFIG.get('retry_attempts', 3)
        delay = SCRAPING_CONFIG.get('delay_between_requests', 2)

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                wait = (2 ** attempt) * delay
                self.logger.warning(f" Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                
                # Cleanup between attempts
                if self._driver:
                    self._driver.delete_all_cookies()
                    self._execute_stealth_js()
                    
                time.sleep(wait)

        self.logger.error(f" All {max_retries} retries failed.")
        return None

    @abstractmethod
    def scrape_company_info(self, url: str) -> Dict[str, Any]:
        """Subclasses must implement this method"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        if self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
                
        try:
            self.session.close()
        except Exception as e:
            self.logger.error(f"Error closing session: {e}")