import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
if not load_dotenv():
    print("⚠️  .env file not found or failed to load. Make sure it's in the project root.")

def get_env(key: str, default: Optional[Any] = None) -> Any:
    """Get environment variable with optional default fallback."""
    return os.getenv(key, default)

# ──────────────────────────────
# Scraping Configuration
# ──────────────────────────────
SCRAPING_CONFIG: Dict[str, Any] = {
    'timeout': int(get_env('SELENIUM_TIMEOUT', 30)),
    'retry_attempts': int(get_env('MAX_RETRIES', 3)),
    'delay_between_requests': int(get_env('DELAY_BETWEEN_REQUESTS', 2)),
    'max_urls_per_batch': int(get_env('BATCH_SIZE', 50)),

    'chrome_driver_path': get_env(
        'CHROME_DRIVER_PATH',
        'C:\\Users\\wilda\\Downloads\\chromedriver-win64_135\\chromedriver.exe'  # fallback path
    ),

    'proxy': {
        'enabled': get_env('ENABLE_PROXY', 'false').lower() == 'true',
        'server': get_env('PROXY_SERVER', ''),
        'username': get_env('PROXY_USERNAME', ''),
        'password': get_env('PROXY_PASSWORD', ''),
    }
}

# ──────────────────────────────
# LinkedIn / Proxycurl API Keys
# ──────────────────────────────
API_KEYS: Dict[str, Optional[str]] = {
    'proxycurl': get_env('PROXYCURL_API_KEY'),
    'linkedin_client_id': get_env('LINKEDIN_CLIENT_ID'),
    'linkedin_client_secret': get_env('LINKEDIN_CLIENT_SECRET')
}

# ──────────────────────────────
# Data Processing
# ──────────────────────────────
DATA_PROCESSING: Dict[str, Any] = {
    'min_data_points': 3,
    'required_fields': ['name', 'website', 'email'],
    'export_formats': ['csv', 'xlsx', 'json'],
    'export_path': get_env('DATA_EXPORT_PATH', './data/exports')
}

# ──────────────────────────────
# Logging Configuration
# ──────────────────────────────
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': get_env('LOG_LEVEL', 'INFO')
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/scraper.log',
            'formatter': 'standard',
            'level': get_env('LOG_LEVEL', 'INFO')
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': get_env('LOG_LEVEL', 'INFO'),
            'propagate': True
        }
    }
}

# ──────────────────────────────
# Directory Paths
# ──────────────────────────────
PATHS: Dict[str, str] = {
    'raw_data': 'data/raw',
    'processed_data': 'data/processed',
    'logs': 'logs',
    'exports': DATA_PROCESSING['export_path'],
    'cache': 'data/cache'
}

# Ensure directories exist
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)

# ──────────────────────────────
# Regex Patterns
# ──────────────────────────────
SCRAPING_PATTERNS: Dict[str, Any] = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    'social_media': {
        'linkedin': r'linkedin\.com/(?:company|in)/[^/"]+',
        'twitter': r'twitter\.com/[^/"]+',
        'facebook': r'facebook\.com/[^/"]+',
        'instagram': r'instagram\.com/[^/"]+',
    }
}

# ──────────────────────────────
# Enrichment Configuration
# ──────────────────────────────
ENRICHMENT_CONFIG: Dict[str, Any] = {
    'linkedin': {
        'enabled': bool(API_KEYS['proxycurl']),
        'source': 'proxycurl',
        'auth': {
            'client_id': API_KEYS['linkedin_client_id'],
            'client_secret': API_KEYS['linkedin_client_secret']
        },
        'fields': [
            'name', 'description', 'location', 'industry',
            'employee_count', 'linkedin_url'
        ]
    }
}

# ──────────────────────────────
# Rate Limiting
# ──────────────────────────────
RATE_LIMITS: Dict[str, Any] = {
    'default': {
        'requests_per_second': 1,
        'burst_size': 5
    },
    'linkedin': {
        'requests_per_minute': 60,
        'daily_limit': 5000
    }
}
