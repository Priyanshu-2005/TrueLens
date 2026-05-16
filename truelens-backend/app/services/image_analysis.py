import os
from PIL import Image, ImageChops, ImageEnhance
import io

def calculate_ela(image_bytes: bytes, quality: int = 90) -> float:
    """
    Performs Error Level Analysis (ELA) on an image to detect tampering.
    Returns a score representing the variance in error levels.
    """
    try:
        original = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Save at known quality to a buffer
        temp_buffer = io.BytesIO()
        original.save(temp_buffer, "JPEG", quality=quality)
        temp_buffer.seek(0)
        
        resaved = Image.open(temp_buffer)
        
        # Calculate the absolute difference
        diff = ImageChops.difference(original, resaved)
        
        # Enhance the difference for calculation
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
            
        scale = 255.0 / max_diff
        enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale)
        
        # Calculate a basic metric: average pixel difference in the enhanced image
        # High average difference indicates areas that lost a lot of quality,
        # which usually means they were pasted in from a different source.
        stat = enhanced_diff.resize((100, 100)).getdata()
        avg_diff = sum([sum(p)/3.0 for p in stat]) / len(stat)
        
        # Scale the score 0-100 (where > 50 means likely tampered)
        score = min(int((avg_diff / 50.0) * 100), 100)
        
        return score
    except Exception as e:
        print(f"ELA Analysis Error: {e}")
        return 50

def analyze_image(image_bytes: bytes):
    """Entrypoint for image forensics."""
    ela_score = calculate_ela(image_bytes)
    
    return {
        "score": ela_score,
        "confidence": 0.8,
        "label": "Image Error Level Analysis",
        "type": "image",
        "evidence": {
            "ela_variance_score": ela_score,
            "compression_quality_test": 90
        },
        "highlights": ["High variance in error levels detected, suggesting manipulation."] if ela_score > 60 else []
    }
