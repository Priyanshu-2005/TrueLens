"""
TrueLens Provenance Service
=============================
Checks the history and fact-check status of URLs and claims:
  1. Wayback Machine API: checks if and when a URL was archived.
  2. Google Fact Check API: checks if claims extracted from text have been fact-checked.
"""

import urllib.request
import urllib.parse
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def check_wayback_machine(url: str) -> Dict[str, Any]:
    """
    Queries the Internet Archive's Wayback Machine availability API.
    Returns the oldest available snapshot and the newest.
    """
    try:
        encoded_url = urllib.parse.quote(url, safe='/:?=&')
        api_url = f"https://archive.org/wayback/available?url={encoded_url}"
        
        req = urllib.request.Request(api_url, headers={"User-Agent": "TrueLens/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        snapshots = data.get('archived_snapshots', {})
        if not snapshots or 'closest' not in snapshots:
            return {
                "has_history": False,
                "message": "No historical snapshots found in the Wayback Machine."
            }
            
        closest = snapshots['closest']
        timestamp_str = closest.get('timestamp', '')
        
        # Wayback timestamp format: YYYYMMDDhhmmss
        snapshot_date = None
        if len(timestamp_str) >= 8:
            try:
                snapshot_date = datetime.strptime(timestamp_str[:8], "%Y%m%d").strftime("%Y-%m-%d")
            except ValueError:
                pass
                
        return {
            "has_history": True,
            "closest_snapshot": snapshot_date,
            "snapshot_url": closest.get('url'),
            "message": f"Historical snapshot available from {snapshot_date}." if snapshot_date else "Historical snapshot available."
        }
    except Exception as e:
        logger.warning(f"Wayback Machine API error for {url}: {e}")
        return {"has_history": False, "error": str(e)}


def check_google_fact_check(query: str) -> Dict[str, Any]:
    """
    Queries the Google Fact Check Tools API.
    Requires GOOGLE_FACT_CHECK_API_KEY in environment variables.
    """
    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
    if not api_key:
        return {
            "available": False,
            "error": "API key not configured"
        }
        
    try:
        # We need a meaningful query. If it's too long, truncate it.
        # Ideally, we would extract the core claim, but a simple heuristic is
        # taking the first ~100 characters of the most 'bursty' sentence.
        # For simplicity here, we just use the query directly but capped.
        search_query = query[:100]
        encoded_query = urllib.parse.quote(search_query)
        api_url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={encoded_query}&key={api_key}"
        
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        claims = data.get('claims', [])
        if not claims:
            return {"available": True, "claims_found": 0}
            
        # Parse top claims
        results = []
        for claim in claims[:3]:  # Top 3
            review = claim.get('claimReview', [{}])[0]
            results.append({
                "text": claim.get('text'),
                "claimant": claim.get('claimant'),
                "claim_date": claim.get('claimDate'),
                "publisher": review.get('publisher', {}).get('name'),
                "rating": review.get('textualRating'),
                "url": review.get('url')
            })
            
        return {
            "available": True,
            "claims_found": len(claims),
            "top_reviews": results
        }
    except Exception as e:
        logger.warning(f"Google Fact Check API error: {e}")
        return {"available": False, "error": str(e)}


def analyze_provenance(url: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """
    Combines Wayback and Fact Check signals into a single provenance score.
    Returns a score 0-100 (higher = more suspicious/fake).
    """
    highlights = []
    evidence = {}
    score = 50
    
    if url:
        wayback = check_wayback_machine(url)
        evidence["wayback"] = wayback
        
        if wayback.get("has_history"):
            # Having a history is generally a good sign for authentic content
            score -= 10
            highlights.append(f"Content provenance verified: {wayback.get('message')}")
        elif wayback.get("error") is None:
            # Explicitly not found (vs just an API error)
            score += 10
            highlights.append("No historical record found for this URL.")
            
    if text and len(text) > 50:
        # In a real system, we'd extract the top claim/headline from the text.
        # For now, we take the first sentence or up to 100 chars.
        claim_query = text.split('.')[0][:100] if '.' in text else text[:100]
        fact_check = check_google_fact_check(claim_query)
        evidence["fact_check"] = fact_check
        
        if fact_check.get("claims_found", 0) > 0:
            reviews = fact_check.get("top_reviews", [])
            for review in reviews:
                rating = str(review.get("rating", "")).lower()
                if any(bad in rating for bad in ["false", "fake", "pants on fire", "misleading", "incorrect"]):
                    score += 30
                    highlights.append(f"Fact-check alert: Claim rated '{review.get('rating')}' by {review.get('publisher')}")
                elif any(good in rating for good in ["true", "correct", "accurate"]):
                    score -= 20
                    highlights.append(f"Fact-check verified: Claim rated '{review.get('rating')}' by {review.get('publisher')}")

    score = max(0, min(100, score))
    
    return {
        "score": score,
        "confidence": 0.80,
        "label": "Provenance Analysis",
        "type": "provenance",
        "evidence": evidence,
        "highlights": highlights
    }
