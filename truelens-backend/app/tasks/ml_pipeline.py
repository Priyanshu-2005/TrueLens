"""
TrueLens ML Pipeline — Celery Task
====================================
Orchestrates the multi-signal analysis pipeline:
  - Text analysis: transformer ensemble (RoBERTa + stylometry)
  - Domain analysis: WHOIS + TLD reputation
  - Image forensics: ELA + EXIF + GAN detection
  - Document analysis: OCR + fonts + arithmetic validation

The pipeline processes scans asynchronously via Celery and stores
results (signals + verdict) in the database.
"""

import time
import uuid
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.models import Scan, Signal, ScanStatusEnum, VerdictEnum
from app.services.text_analysis import analyze_text_ensemble
from app.services.domain_analysis import analyze_domain
from app.services.provenance import analyze_provenance
from app.services.review_analysis import analyze_review
from app.services.news_analysis import analyze_news

logger = logging.getLogger(__name__)


# ── Signal weights for ensemble scoring ──
SIGNAL_WEIGHTS = {
    "text": 0.40,
    "metadata": 0.25,  # domain/EXIF signals
    "image": 0.20,
    "review": 0.10,
    "news": 0.20,      # Fake news weight
    "provenance": 0.05,
}


def _calculate_trust_score(signals: List[Dict[str, Any]]) -> int:
    """
    Calculates the final trust score from individual signals.

    Each signal has a 'score' (0-100, where higher = more likely fake)
    and a 'confidence' (0-1).

    The trust score is: 100 - weighted_average_fake_probability
    """
    if not signals:
        return 50

    weighted_sum = 0.0
    weight_total = 0.0

    for signal in signals:
        sig_type = signal.get("type", "text")
        weight = SIGNAL_WEIGHTS.get(sig_type, 0.10)
        confidence = signal.get("confidence", 0.5)

        # Weight by both signal weight and confidence
        effective_weight = weight * confidence
        weighted_sum += signal["score"] * effective_weight
        weight_total += effective_weight

    if weight_total == 0:
        return 50

    avg_fake_probability = weighted_sum / weight_total
    trust_score = int(100 - avg_fake_probability)
    return max(0, min(100, trust_score))


def _determine_verdict(trust_score: int) -> VerdictEnum:
    """Maps trust score to a verdict enum."""
    if trust_score >= 80:
        return VerdictEnum.authentic
    elif trust_score >= 40:
        return VerdictEnum.suspicious
    else:
        return VerdictEnum.ai_generated


def _scrape_url_text(url: str) -> str:
    """
    Attempts to fetch and extract text from a URL.
    Falls back to a placeholder if fetching fails.
    """
    try:
        import urllib.request
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'noscript'):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'noscript'):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    stripped = data.strip()
                    if stripped:
                        self.texts.append(stripped)

        req = urllib.request.Request(url, headers={"User-Agent": "TrueLens/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

        extractor = TextExtractor()
        extractor.feed(html)
        text = ' '.join(extractor.texts)

        # Return at least 100 chars for meaningful analysis
        if len(text) < 100:
            return f"Minimal content from {url}. {text}"
        return text[:5000]  # Cap at 5000 chars

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return f"Content from {url}. Unable to scrape — using URL metadata only."


@celery_app.task(bind=True, name="process_scan_task")
def process_scan_task(self, scan_id: str):
    """
    Main Celery task: processes a scan through the full ML pipeline.
    """
    db = SessionLocal()
    start_time = time.time()

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"status": "error", "message": "Scan not found"}

        scan.status = ScanStatusEnum.processing
        db.commit()

        signals_data: List[Dict[str, Any]] = []

        # ═══════════════════════════════════════════════════════
        #  TEXT CONTENT → Text Analysis (Ensemble)
        # ═══════════════════════════════════════════════════════
        if scan.raw_text:
            text_signal = analyze_text_ensemble(scan.raw_text)
            signals_data.append(text_signal)
            
            # Provenance analysis for raw text (fact checking)
            provenance_signal = analyze_provenance(text=scan.raw_text)
            signals_data.append(provenance_signal)
            
            # Review check heuristic
            lower_text = scan.raw_text.lower()
            is_review = any(word in lower_text for word in ["recommend", "stars", "product", "bought", "purchase", "customer service"])
            if is_review and len(scan.raw_text) < 1000:
                review_signal = analyze_review(scan.raw_text)
                signals_data.append(review_signal)
                
            # Fake News check heuristic
            is_news = any(word in lower_text for word in ["news", "report", "breaking", "update", "sources", "journalist"])
            if is_news and len(scan.raw_text) > 150:
                news_signal = analyze_news(scan.raw_text)
                signals_data.append(news_signal)

        # ═══════════════════════════════════════════════════════
        #  URL → Domain + Text Analysis
        # ═══════════════════════════════════════════════════════
        elif scan.url:
            # Domain analysis (WHOIS, TLD, etc.)
            domain_signal = analyze_domain(scan.url)
            signals_data.append(domain_signal)

            # Provenance analysis (Wayback Machine)
            provenance_signal = analyze_provenance(url=scan.url)
            signals_data.append(provenance_signal)

            # Scrape and analyze text from the URL
            scraped_text = _scrape_url_text(scan.url)
            if len(scraped_text) > 50:
                text_signal = analyze_text_ensemble(scraped_text)
                signals_data.append(text_signal)
                
                # Also run fact check on the scraped text
                fact_check_signal = analyze_provenance(text=scraped_text)
                signals_data.append(fact_check_signal)
                
                # Review check
                lower_text = scraped_text.lower()
                is_review = any(word in lower_text for word in ["recommend", "stars", "product", "bought", "purchase", "customer service"])
                if is_review:
                    review_signal = analyze_review(scraped_text)
                    signals_data.append(review_signal)
                    
                # Fake News check
                is_news = any(word in lower_text for word in ["news", "report", "breaking", "update", "sources", "journalist"])
                if is_news and len(scraped_text) > 150:
                    news_signal = analyze_news(scraped_text)
                    signals_data.append(news_signal)

        # ═══════════════════════════════════════════════════════
        #  CALCULATE FINAL SCORES
        # ═══════════════════════════════════════════════════════
        final_trust_score = _calculate_trust_score(signals_data)
        verdict = _determine_verdict(final_trust_score)

        # Store signals in the database
        for s_data in signals_data:
            signal = Signal(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                type=s_data.get("type", "text"),
                score=s_data.get("score", 50),
                label=s_data.get("label", "Analysis"),
                confidence=s_data.get("confidence", 0.5),
                evidence=s_data.get("evidence"),
                highlights=s_data.get("highlights", []),
            )
            db.add(signal)

        scan.trust_score = final_trust_score
        scan.verdict = verdict
        scan.status = ScanStatusEnum.completed
        scan.scan_duration = round(time.time() - start_time, 2)
        scan.completed_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(
            f"Scan {scan_id} completed: score={final_trust_score}, "
            f"verdict={verdict.value}, signals={len(signals_data)}, "
            f"duration={scan.scan_duration}s"
        )

        return {
            "status": "success",
            "scan_id": scan_id,
            "trust_score": final_trust_score,
            "verdict": verdict.value,
            "num_signals": len(signals_data),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Scan {scan_id} failed: {e}")
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = ScanStatusEnum.failed
                db.commit()
        except Exception:
            pass
        raise e
    finally:
        db.close()
