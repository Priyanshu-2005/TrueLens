from fastapi import APIRouter, HTTPException, Path
import logging

from app.services.domain_analysis import analyze_domain

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{domain:path}")
def get_domain_trust(domain: str = Path(..., description="The domain or URL to analyze")):
    """
    Analyzes a domain for trust signals (WHOIS age, blocklists, SSL, TLD reputation).
    Returns a trust score from 0-100 (where higher score means MORE suspicious/fake).
    """
    try:
        # The analyze_domain service extracts the domain from URL if needed
        result = analyze_domain(domain)
        return result
    except Exception as e:
        logger.error(f"Error analyzing domain {domain}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during domain analysis")
