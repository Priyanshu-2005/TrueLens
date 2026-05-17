"""
TrueLens News Analysis Service
==============================
Analyzes text specifically for journalistic integrity and fake news indicators.
Checks for sensationalism, emotional manipulation, lack of citations, and clickbait.
"""

import logging
import re
from typing import Dict, Any

from app.services.provenance import check_google_fact_check

logger = logging.getLogger(__name__)

# Fake news model pipeline
_news_model_pipeline = None
_news_model_attempted = False

def _get_news_pipeline():
    """Lazily loads a fake news transformer model if available."""
    global _news_model_pipeline, _news_model_attempted
    
    if _news_model_attempted:
        return _news_model_pipeline
        
    _news_model_attempted = True
    
    try:
        from transformers import pipeline
        # We use a general sentiment/text classification proxy if a specific
        # fake news model isn't available, but ideally this would point to a
        # fine-tuned model like mrm8488/bert-tiny-finetuned-fake-news-detection
        model_name = "mrm8488/bert-tiny-finetuned-fake-news-detection"
        logger.info(f"Loading fake news analysis model: {model_name}")
        _news_model_pipeline = pipeline("text-classification", model=model_name, truncation=True, max_length=512)
        logger.info("Successfully loaded fake news analysis model")
        return _news_model_pipeline
    except Exception as e:
        logger.warning(f"Failed to load fake news ML model: {e}")
        return None


def analyze_news_heuristics(text: str) -> Dict[str, Any]:
    """
    Evaluates journalistic integrity heuristics.
    Returns a base score where higher = more likely fake news.
    """
    highlights = []
    score = 50
    evidence = {}
    
    lower_text = text.lower()
    words = text.split()
    num_words = max(len(words), 1)
    
    evidence["word_count"] = num_words

    # 1. Sensationalism Index
    sensational_words = [
        "shocking", "bombshell", "destroyed", "outrage", "exposed", 
        "mind-blowing", "secret", "truth", "hoax", "conspiracy", "scandal"
    ]
    sensational_hits = sum(1 for w in sensational_words if w in lower_text)
    evidence["sensational_words"] = sensational_hits
    
    if sensational_hits > 2:
        score += 20
        highlights.append(f"Highly sensational language detected ({sensational_hits} flag words)")
    elif sensational_hits > 0:
        score += 10
        highlights.append("Contains sensationalized phrasing")

    # 2. Clickbait Patterns (usually found in first few sentences or title)
    first_300 = lower_text[:300]
    clickbait_phrases = [
        "you won't believe", "this one trick", "what happens next", 
        "will blow your mind", "left everyone speechless", "they don't want you to know"
    ]
    clickbait_hits = [p for p in clickbait_phrases if p in first_300]
    if clickbait_hits:
        score += 25
        highlights.append(f"Clickbait framing detected: '{clickbait_hits[0]}'")

    # 3. Citation Check
    # Authentic news heavily relies on named sources and specific attribution.
    citation_phrases = [
        "according to", "reported", "said", "stated", "researchers at", 
        "told", "announced", "officials", "spokesperson", "document", "study"
    ]
    citation_hits = sum(1 for w in citation_phrases if w in lower_text)
    evidence["citation_count"] = citation_hits
    
    if num_words > 150:
        if citation_hits == 0:
            score += 25
            highlights.append("Total lack of source citations or attribution")
        elif citation_hits < 2:
            score += 10
            highlights.append("Poor source attribution for an article of this length")
        else:
            score -= 15
            highlights.append("Healthy use of journalistic source attribution")

    # 4. Emotional Manipulation (All CAPS and Exclamation)
    caps_words = sum(1 for w in words if w == w.upper() and len(w) > 2)
    caps_ratio = caps_words / num_words
    evidence["caps_ratio"] = round(caps_ratio, 3)
    
    if caps_ratio > 0.05:
        score += 15
        highlights.append("Unprofessional capitalization (ALL CAPS manipulation)")
        
    exclamation_count = text.count("!")
    if exclamation_count > 3:
        score += 15
        highlights.append("Excessive use of exclamation marks (emotional framing)")

    return {
        "score": max(0, min(100, score)),
        "evidence": evidence,
        "highlights": highlights
    }


def analyze_news(text: str) -> Dict[str, Any]:
    """
    Main entry point for fake news detection.
    Combines heuristics and transformer ML analysis.
    """
    heuristics = analyze_news_heuristics(text)
    score = heuristics["score"]
    evidence = heuristics["evidence"]
    highlights = heuristics["highlights"]
    
    # Try ML model
    pipe = _get_news_pipeline()
    confidence = 0.75
    
    if pipe:
        try:
            result = pipe(text[:512])[0]
            label = result['label'].lower()  # Typically 'real' or 'fake'
            ml_score = result['score']
            
            evidence["ml_prediction"] = label
            evidence["ml_confidence"] = round(ml_score, 3)
            
            confidence = 0.90
            
            if 'fake' in label:
                score += 25
                highlights.append(f"AI Classifier flagged as Fake News (Confidence: {ml_score:.0%})")
            elif 'real' in label:
                score -= 20
                highlights.append(f"AI Classifier assessed as Real News (Confidence: {ml_score:.0%})")
                
        except Exception as e:
            logger.warning(f"ML news analysis error: {e}")
            
    # Fact-checking integration: Extract the first sentence as the core claim
    core_claim = text.split('.')[0][:100] if '.' in text else text[:100]
    fact_check_result = check_google_fact_check(core_claim)
    
    evidence["fact_check"] = fact_check_result
    
    if fact_check_result.get("claims_found", 0) > 0:
        reviews = fact_check_result.get("top_reviews", [])
        for review in reviews:
            rating = str(review.get("rating", "")).lower()
            if any(bad in rating for bad in ["false", "fake", "pants on fire", "misleading", "incorrect"]):
                score += 40
                highlights.append(f"Fact-Check: Core claim rated '{review.get('rating')}' by {review.get('publisher')}")
            elif any(good in rating for good in ["true", "correct", "accurate"]):
                score -= 30
                highlights.append(f"Fact-Check: Core claim verified as '{review.get('rating')}' by {review.get('publisher')}")
            
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "confidence": confidence,
        "label": "Fake News Analysis",
        "type": "news",
        "evidence": evidence,
        "highlights": highlights
    }
