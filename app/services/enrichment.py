import re
import os
import requests
from urllib.parse import urlparse
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")

# ─────────────────────────────────────────────
# Validation & Utility Functions
# ─────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Validate email using regex."""
    if not email:
        return False
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None


def extract_domain_from_url(url: str) -> str:
    """Extract domain from a given URL."""
    if not url:
        return ""
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace("www.", "").strip()


def extract_company_from_email(email: str) -> str:
    """Extract company name from email domain."""
    if not email or '@' not in email:
        return ""
    domain = email.split('@')[1]
    company = domain.split('.')[0]
    return company.strip()


# ─────────────────────────────────────────────
# Lead Scoring
# ─────────────────────────────────────────────

def score_lead(lead: Dict[str, Any]) -> int:
    """Assign score based on available lead information."""
    score = 0
    if is_valid_email(lead.get('email', '')):
        score += 30
    if lead.get('company'):
        score += 20
    if lead.get('linkedin'):
        score += 25
    if lead.get('website'):
        score += 25
    return score


# ─────────────────────────────────────────────
# Enrichment via Proxycurl
# ─────────────────────────────────────────────

def enrich_with_proxycurl(website: str) -> Dict[str, Any]:
    """Use Proxycurl API to enrich company data."""
    if not PROXYCURL_API_KEY:
        print("⚠️  PROXYCURL_API_KEY is not set.")
        return {}

    if not website:
        return {}

    domain = extract_domain_from_url(website)
    headers = {
        "Authorization": f"Bearer {PROXYCURL_API_KEY}"
    }
    api_url = "https://nubela.co/proxycurl/api/linkedin/company"
    params = {
        "url": f"https://{domain}",
        "use_cache": "if-present"
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Proxycurl HTTP error: {e} | Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Proxycurl connection error: {e}")
    except Exception as e:
        print(f"❌ Proxycurl unknown error: {e}")
    
    return {}


# ─────────────────────────────────────────────
# Master Lead Enrichment Function
# ─────────────────────────────────────────────

def enrich_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead with derived fields and third-party data.
    """
    enriched = lead.copy()
    email = lead.get('email', '')
    website = lead.get('website', '')

    # Local enrichment
    enriched['email_valid'] = is_valid_email(email)
    enriched['domain'] = extract_domain_from_url(website)
    enriched['company_extracted'] = extract_company_from_email(email)

    # Third-party enrichment (Proxycurl)
    if PROXYCURL_API_KEY and website:
        proxycurl_data = enrich_with_proxycurl(website)
        enriched.update(proxycurl_data)

    # Scoring
    enriched['lead_score'] = score_lead(enriched)
    return enriched
