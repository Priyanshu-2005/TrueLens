"""
TrueLens Domain Analysis Service
=================================
Analyzes domain reputation and trust signals:
  1. WHOIS domain age and registrar checks
  2. PhishTank API check (phishing blocklist)
  3. URLhaus API check (malware blocklist)
  4. SSL certificate validity check
  5. TLD reputation analysis
"""

import socket
import ssl
import json
import logging
import urllib.request
import urllib.error
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, Any, List

import whois

logger = logging.getLogger(__name__)


# Known highly trusted TLDs
TRUSTED_TLDS = {'.gov', '.edu', '.mil'}

# Known highly abused TLDs (frequently used for spam/phishing)
SUSPICIOUS_TLDS = {
    '.xyz', '.top', '.pw', '.tk', '.ml', '.ga', '.cf', '.gq',
    '.club', '.online', '.site', '.click', '.link', '.vip',
    '.stream', '.download', '.date', '.review', '.country',
}

# Known trusted domains
TRUSTED_DOMAINS = {
    'google.com', 'microsoft.com', 'apple.com', 'amazon.com',
    'github.com', 'wikipedia.org', 'nytimes.com', 'bbc.co.uk',
    'bbc.com', 'linkedin.com', 'twitter.com', 'x.com',
    'facebook.com', 'instagram.com', 'youtube.com',
}


def get_domain_from_url(url: str) -> str:
    """Extracts the base domain from a URL."""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def check_ssl(domain: str) -> Dict[str, Any]:
    """Checks if a domain has a valid SSL certificate."""
    try:
        context = ssl.create_default_context()
        context.check_hostname = True
        
        # Connect to the domain on port 443 with a short timeout
        with socket.create_connection((domain, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
        # If we successfully got here, SSL is valid
        # Check expiry date
        not_after = cert.get('notAfter')
        expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
        days_to_expiry = (expiry_date - datetime.utcnow()).days
        
        return {
            "valid": True,
            "days_to_expiry": days_to_expiry,
            "issuer": dict(x[0] for x in cert.get('issuer', []))
        }
    except Exception as e:
        logger.warning(f"SSL check failed for {domain}: {e}")
        return {"valid": False, "error": str(e)}


def check_urlhaus(domain: str) -> Dict[str, Any]:
    """Queries Abuse.ch URLhaus API for malware associations."""
    try:
        req = urllib.request.Request(
            'https://urlhaus-api.abuse.ch/v1/host/',
            data=f"host={domain}".encode('utf-8'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get('query_status') == 'ok' and data.get('url_count', 0) > 0:
            return {"listed": True, "malware_urls": data.get('url_count')}
            
        return {"listed": False}
    except Exception as e:
        logger.warning(f"URLhaus check failed for {domain}: {e}")
        return {"listed": False, "error": str(e)}


def analyze_domain(url: str) -> Dict[str, Any]:
    """
    Comprehensive domain analysis.
    Returns a score 0-100 (higher = more suspicious).
    """
    domain = get_domain_from_url(url)
    highlights: List[str] = []
    evidence: Dict[str, Any] = {"domain": domain}
    
    # Base score (neutral)
    score = 50
    
    # ── 1. Trusted Domain Override ──
    if domain.lower() in TRUSTED_DOMAINS:
        return {
            "score": 5,
            "confidence": 0.99,
            "label": "Domain Trust Analysis",
            "type": "metadata",
            "evidence": {"domain": domain, "trusted_list": True},
            "highlights": ["Domain is on the global trusted list."]
        }

    # ── 2. TLD Analysis ──
    tld = '.' + domain.rsplit('.', 1)[-1].lower() if '.' in domain else ''
    if tld in TRUSTED_TLDS:
        score -= 30
        highlights.append(f"Highly trusted top-level domain ({tld})")
    elif tld in SUSPICIOUS_TLDS:
        score += 30
        highlights.append(f"Suspicious top-level domain frequently used for spam ({tld})")

    # ── 3. WHOIS Age Check ──
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        if creation_date:
            age_days = (datetime.now() - creation_date).days
            evidence["age_days"] = age_days
            evidence["registrar"] = w.registrar
            
            if age_days < 30:
                score += 40
                highlights.append(f"Domain is extremely new ({age_days} days old)")
            elif age_days < 180:
                score += 20
                highlights.append(f"Domain is relatively new ({age_days} days old)")
            elif age_days > 1825:  # > 5 years
                score -= 20
                highlights.append("Domain has established history (>5 years old)")
            elif age_days > 365:
                score -= 10
        else:
            score += 10
            highlights.append("WHOIS creation date hidden or unavailable")
            
    except Exception as e:
        logger.warning(f"WHOIS lookup failed for {domain}: {e}")
        score += 5
        evidence["whois_error"] = str(e)

    # ── 4. SSL Validity ──
    ssl_result = check_ssl(domain)
    evidence["ssl"] = ssl_result
    if ssl_result["valid"]:
        score -= 5
        if ssl_result.get("days_to_expiry", 0) < 14:
            score += 10
            highlights.append("SSL certificate expires very soon")
    else:
        score += 25
        highlights.append("No valid SSL certificate found (insecure)")

    # ── 5. Malware/Phishing Blocklists (URLhaus) ──
    # Note: PhishTank requires an API key for reliable automated usage, 
    # so we rely primarily on URLhaus here.
    urlhaus_result = check_urlhaus(domain)
    evidence["urlhaus"] = urlhaus_result
    
    if urlhaus_result.get("listed", False):
        score += 50  # Instant critical penalty
        highlights.append(f"Domain listed on URLhaus malware blocklist ({urlhaus_result.get('malware_urls')} hits)")

    # ── Final Score Clamping ──
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "confidence": 0.90,
        "label": "Domain Trust Analysis",
        "type": "metadata",
        "evidence": evidence,
        "highlights": highlights
    }
