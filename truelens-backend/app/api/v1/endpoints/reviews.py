from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import logging

from app.services.review_analysis import analyze_review

logger = logging.getLogger(__name__)
router = APIRouter()

class ReviewRequest(BaseModel):
    text: str

@router.post("/analyze")
def analyze_product_review(request: ReviewRequest = Body(...)):
    """
    Analyzes a product or business review for authenticity.
    Returns a score 0-100 where higher means more likely to be fake/spam.
    """
    if len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Review text too short for meaningful analysis")
        
    try:
        result = analyze_review(request.text)
        return result
    except Exception as e:
        logger.error(f"Review analysis failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during review analysis")
