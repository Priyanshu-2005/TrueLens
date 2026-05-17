from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import logging

from app.services.news_analysis import analyze_news

logger = logging.getLogger(__name__)
router = APIRouter()

class NewsRequest(BaseModel):
    text: str

@router.post("/analyze")
def analyze_news_article(request: NewsRequest = Body(...)):
    """
    Analyzes a news article or report for journalistic integrity.
    Returns a score 0-100 where higher means more likely to be fake/sensationalized news.
    """
    if len(request.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text too short for meaningful news analysis")
        
    try:
        result = analyze_news(request.text)
        return result
    except Exception as e:
        logger.error(f"News analysis failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during news analysis")
