import whois
from urllib.parse import urlparse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_domain_from_url(url: str) -> str:
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url

def analyze_domain(url: str):
    """
    Analyzes a domain's WHOIS data.
    Returns a score from 0-100 where higher score means higher probability of being fake/malicious.
    New domains (< 1 year old) have higher fake probabilities.
    """
    domain = get_domain_from_url(url)
    
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        if not creation_date:
            raise ValueError("No creation date found")

        age_days = (datetime.now() - creation_date).days
        
        # Domain Trust Heuristic:
        # If age < 30 days -> Score 90 (Highly suspicious)
        # If age < 365 days -> Score 60 (Suspicious)
        # If age > 5 years -> Score 10 (Trusted)
        
        score = 50
        if age_days < 30:
            score = 90
        elif age_days < 180:
            score = 75
        elif age_days < 365:
            score = 60
        elif age_days > 1825: # 5 years
            score = 10
        elif age_days > 365:
            score = 30
            
        return {
            "score": score,
            "confidence": 0.95,
            "label": "Domain WHOIS Trust",
            "type": "metadata",
            "evidence": {
                "domain": domain,
                "age_days": age_days,
                "registrar": w.registrar
            },
            "highlights": [f"Domain is very new ({age_days} days old), use caution."] if score > 70 else []
        }
        
    except Exception as e:
        logger.error(f"WHOIS analysis failed for {domain}: {e}")
        return {
            "score": 50, # Neutral fallback
            "confidence": 0.0,
            "label": "Domain WHOIS Trust",
            "type": "metadata",
            "evidence": {"domain": domain, "error": str(e)},
            "highlights": ["WHOIS data unavailable or protected."]
        }
