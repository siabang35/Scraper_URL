import re
import random
from typing import List, Optional, Dict, Any, Union, Set, Tuple
import validators
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
import logging
import json
import csv
from pathlib import Path
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import tldextract
import phonenumbers
from email_validator import validate_email as validate_email_format, EmailNotValidError
from app.config import PATHS, SCRAPING_PATTERNS
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning


logger = logging.getLogger(__name__)

# Optional: Hide warning if still needed
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

class TextCleaner:
    """Text cleaning and normalization utilities"""
    
    @staticmethod
    def is_probably_url(text: str) -> bool:
        """Check if the text is a URL-like string"""
        return re.match(r'https?://\S+', text) is not None

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text comprehensively"""
        if not text:
            return ""
            
        # Convert to string if not already
        text = str(text)

        # Remove HTML tags only if not a URL
        if not TextCleaner.is_probably_url(text):
            text = BeautifulSoup(text, 'html.parser').get_text()
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Remove special characters but keep essential punctuation
        text = re.sub(r'[^\w\s@.,-]', '', text)
        
        # Normalize multiple punctuation
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r',{2,}', ',', text)
        text = re.sub(r'-{2,}', '-', text)
        
        # Remove leading/trailing punctuation
        text = text.strip('.,- ')
        
        return text

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """Normalize company name with advanced cleaning"""
        if not name:
            return ""
            
        # Remove common business suffixes
        suffixes = [
            r'\b(Inc|LLC|Ltd|Corp|Corporation|Limited|Company|GmbH|SA|BV|NV|AG)',
            r'\b(Group|Holdings|Ventures|Solutions|Technologies|Tech|Software)',
            r'\b(International|Global|Worldwide|Industries|Systems)'
        ]
        
        name = name.strip()
        for suffix in suffixes:
            name = re.sub(f"{suffix}\.?", "", name, flags=re.IGNORECASE)
            
        # Clean and normalize
        name = TextCleaner.clean_text(name)
        
        # Capitalize words properly
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name.strip()

    @staticmethod
    def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
        """Extract relevant keywords from text"""
        if not text:
            return []
            
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over',
            'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        # Clean and tokenize
        text = TextCleaner.clean_text(text.lower())
        words = text.split()
        
        # Filter words
        valid_words = [
            word for word in words
            if len(word) >= min_length
            and word not in stop_words
            and not word.isnumeric()
        ]
        
        # Count frequencies
        from collections import Counter
        word_freq = Counter(valid_words)
        
        # Return most common words
        return [word for word, _ in word_freq.most_common(max_keywords)]

class ContactExtractor:
    """Contact information extraction utilities"""
    
    @staticmethod
    def extract_emails(text: str) -> Set[str]:
        """Extract and validate email addresses"""
        if not text:
            return set()
            
        email_pattern = SCRAPING_PATTERNS['email']
        emails = re.findall(email_pattern, text.lower())
        
        valid_emails = set()
        for email in emails:
            email = email.strip()
            if ContactExtractor.validate_email(email):
                valid_emails.add(email)
                
        return valid_emails

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email with comprehensive checks"""
        if not email or '@' not in email:
            return False
            
        try:
            # Use email-validator for format checking
            validate_email_format(email)
            
            # Additional checks
            domain = email.split('@')[1].lower()
            
            # Check against invalid domains
            invalid_domains = {
                'example.com', 'test.com', 'domain.com',
                'localhost', 'example.org', 'test.org'
            }
            
            if domain in invalid_domains:
                return False
                
            # Check for disposable email services
            disposable_domains = {'tempmail.com', 'throwaway.com'}
            if domain in disposable_domains:
                return False
                
            return True
            
        except EmailNotValidError:
            return False

    @staticmethod
    def extract_phones(text: str) -> List[str]:
        """Extract and validate phone numbers"""
        if not text:
            return []
            
        # Find potential phone numbers
        phone_pattern = SCRAPING_PATTERNS['phone']
        potential_phones = re.findall(phone_pattern, text)
        
        valid_phones = []
        for phone in potential_phones:
            formatted = ContactExtractor.format_phone(phone)
            if formatted:
                valid_phones.append(formatted)
                
        return list(set(valid_phones))

    @staticmethod
    def format_phone(phone: str) -> Optional[str]:
        """Format phone number with international support"""
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone, "US")  # Default to US
            
            if not phonenumbers.is_valid_number(parsed):
                return None
                
            # Format in international format
            formatted = phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            return formatted
            
        except phonenumbers.NumberParseException:
            return None

    @staticmethod
    def extract_social_links(text: str) -> Dict[str, str]:
        """Extract and validate social media links"""
        social_links = {}
        
        for platform, pattern in SCRAPING_PATTERNS['social_media'].items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize URL
                url = f"https://{match}"
                if validators.url(url):
                    # Remove tracking parameters
                    clean_url = URLHandler.remove_tracking_params(url)
                    social_links[platform] = clean_url
                
        return social_links

class URLHandler:
    """URL handling and validation utilities"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL with comprehensive checks"""
        if not url:
            return False
            
        # Basic format validation
        if not validators.url(url):
            return False
            
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False
                
            # Ensure scheme is http or https
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # Extract domain info
            ext = tldextract.extract(url)
            
            # Check for valid TLD
            if not ext.suffix:
                return False
                
            # Check for suspicious domains
            suspicious_domains = {'example', 'test', 'localhost'}
            if ext.domain in suspicious_domains:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract and clean domain from URL"""
        try:
            ext = tldextract.extract(url)
            domain = f"{ext.domain}.{ext.suffix}"
            if ext.subdomain and ext.subdomain != 'www':
                domain = f"{ext.subdomain}.{domain}"
            return domain.lower()
        except Exception:
            return None

    @staticmethod
    def remove_tracking_params(url: str) -> str:
        """Remove tracking parameters from URL"""
        try:
            parsed = urlparse(url)
            
            # Common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign',
                'utm_term', 'utm_content', 'fbclid',
                'gclid', 'ref', 'source', 'medium'
            }
            
            if parsed.query:
                # Parse query parameters
                params = parse_qs(parsed.query)
                
                # Filter out tracking parameters
                clean_params = {
                    k: v for k, v in params.items()
                    if not any(t in k.lower() for t in tracking_params)
                }
                
                # Rebuild URL
                clean_query = urlencode(clean_params, doseq=True)
                return urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    clean_query,
                    parsed.fragment
                ))
                
        except Exception as e:
            logger.error(f"Error cleaning URL {url}: {str(e)}")
            
        return url

class DataHandler:
    """Data handling and storage utilities"""
    
    @staticmethod
    def save_to_file(data: List[Dict[str, Any]], filename: str, format: str = 'json') -> bool:
        """Save data to file with advanced formatting"""
        if not data:
            logger.warning("No data to save")
            return False
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{filename}_{timestamp}"
        
        try:
            output_dir = Path(PATHS['exports'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                output_path = output_dir / f"{base_filename}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                output_path = output_dir / f"{base_filename}.csv"
                if data:
                    # Flatten nested data
                    flattened_data = [
                        DataHandler.flatten_dict(item)
                        for item in data
                    ]
                    
                    # Get all unique fields
                    fieldnames = set()
                    for item in flattened_data:
                        fieldnames.update(item.keys())
                    
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                        writer.writeheader()
                        writer.writerows(flattened_data)
                        
            else:
                logger.error(f"Unsupported format: {format}")
                return False
                
            logger.info(f"Data saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False

    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items: List = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(DataHandler.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)):
                items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
                
        return dict(items)

class CacheHandler:
    """Cache handling utilities"""
    
    @staticmethod
    def generate_cache_key(url: str) -> str:
        """Generate unique cache key for URL"""
        domain = URLHandler.extract_domain(url) or ''
        key_base = f"{domain}_{url}"
        return hashlib.md5(key_base.encode()).hexdigest()

    @staticmethod
    def save_to_cache(key: str, data: Dict[str, Any]) -> bool:
        """Save data to cache with metadata"""
        try:
            cache_dir = Path(PATHS['cache'])
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'metadata': {
                    'version': '1.0',
                    'source': 'scraper',
                    'cache_date': datetime.now().strftime('%Y-%m-%d')
                }
            }
            
            cache_file = cache_dir / f"{key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return False

    @staticmethod
    def load_from_cache(key: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Load data from cache with validation"""
        try:
            cache_file = Path(PATHS['cache']) / f"{key}.json"
            if not cache_file.exists():
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                
            # Validate cache structure
            if not all(k in cached for k in ['timestamp', 'data', 'metadata']):
                return None
                
            # Check cache age
            cache_time = datetime.fromisoformat(cached['timestamp'])
            age = datetime.now() - cache_time
            
            if age.total_seconds() > (max_age_hours * 3600):
                return None
                
            return cached['data']
        except Exception as e:
            logger.error(f"Cache load error: {e}")
            return None

# Convenience functions
clean_text = TextCleaner.clean_text
normalize_company_name = TextCleaner.normalize_company_name
extract_keywords = TextCleaner.extract_keywords
extract_emails = ContactExtractor.extract_emails
validate_email = ContactExtractor.validate_email
extract_phones = ContactExtractor.extract_phones
format_phone = ContactExtractor.format_phone
extract_social_links = ContactExtractor.extract_social_links
validate_url = URLHandler.validate_url
extract_domain = URLHandler.extract_domain
remove_tracking_params = URLHandler.remove_tracking_params
save_to_file = DataHandler.save_to_file
flatten_dict = DataHandler.flatten_dict
generate_cache_key = CacheHandler.generate_cache_key
save_to_cache = CacheHandler.save_to_cache
load_from_cache = CacheHandler.load_from_cache