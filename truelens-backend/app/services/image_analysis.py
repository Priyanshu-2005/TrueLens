"""
TrueLens Image Forensics Service
=================================
Multi-signal image analysis combining:
  1. Error Level Analysis (ELA) — detects compression inconsistencies from splicing
  2. EXIF Metadata Analysis — flags editing software, stripped metadata, date mismatches
  3. GAN Fingerprint Detection — frequency-domain analysis for AI-generated artifacts

All methods are pure-Python using Pillow, numpy, and exifread.
"""

import io
import math
import struct
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from PIL import Image, ImageChops, ImageEnhance

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  1. ERROR LEVEL ANALYSIS (ELA)
# ══════════════════════════════════════════════════════════════

def calculate_ela(image_bytes: bytes, quality: int = 90) -> Dict[str, Any]:
    """
    Performs Error Level Analysis on an image.
    Regions pasted from different sources will show higher error levels
    after re-compression at a known quality.

    Returns a dict with score (0-100) and detailed metrics.
    """
    try:
        original = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Re-save at known quality
        temp_buffer = io.BytesIO()
        original.save(temp_buffer, "JPEG", quality=quality)
        temp_buffer.seek(0)
        resaved = Image.open(temp_buffer)

        # Pixel-level difference
        diff = ImageChops.difference(original, resaved)

        extrema = diff.getextrema()
        max_diff = max(ex[1] for ex in extrema)
        if max_diff == 0:
            max_diff = 1

        scale = 255.0 / max_diff
        enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale)

        # Calculate statistics on a downsampled version for speed
        small = enhanced_diff.resize((100, 100))
        pixels = list(small.getdata())
        avg_diff = sum(sum(p) / 3.0 for p in pixels) / len(pixels)

        # Standard deviation of differences (high stddev = non-uniform = likely spliced)
        mean_vals = [sum(p) / 3.0 for p in pixels]
        mean_of_means = sum(mean_vals) / len(mean_vals)
        stddev = math.sqrt(sum((v - mean_of_means) ** 2 for v in mean_vals) / len(mean_vals))

        # Score: high avg_diff + high stddev = likely tampered
        score = min(int((avg_diff / 50.0) * 70 + (stddev / 40.0) * 30), 100)

        return {
            "score": score,
            "avg_pixel_difference": round(avg_diff, 2),
            "difference_stddev": round(stddev, 2),
            "max_channel_diff": max_diff,
            "compression_quality_tested": quality,
        }

    except Exception as e:
        logger.error(f"ELA analysis error: {e}")
        return {
            "score": 50,
            "error": str(e),
        }


# ══════════════════════════════════════════════════════════════
#  2. EXIF METADATA ANALYSIS
# ══════════════════════════════════════════════════════════════

# Known image editing software signatures
EDITING_SOFTWARE = {
    'photoshop', 'gimp', 'paint.net', 'lightroom', 'affinity',
    'pixelmator', 'canva', 'snapseed', 'vsco', 'faceapp',
    'facetune', 'remini', 'fotor', 'picsart',
}

# Known AI generation software signatures
AI_SOFTWARE = {
    'dall-e', 'midjourney', 'stable diffusion', 'comfyui',
    'automatic1111', 'novelai', 'firefly', 'deepdream',
}


def analyze_exif(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes EXIF metadata for signs of manipulation.

    Checks:
      - Presence/absence of EXIF data
      - Editing software in Software/ProcessingSoftware tags
      - GPS data presence
      - Date inconsistencies (original vs digitized vs modified)
      - Camera make/model
    """
    highlights: List[str] = []
    evidence: Dict[str, Any] = {}
    score = 0  # 0 = clean, higher = more suspicious

    try:
        import exifread
        tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
    except ImportError:
        logger.warning("exifread not installed, skipping EXIF analysis")
        return {"score": 50, "evidence": {"error": "exifread not installed"}, "highlights": []}
    except Exception as e:
        logger.error(f"EXIF read error: {e}")
        return {"score": 50, "evidence": {"error": str(e)}, "highlights": []}

    if not tags:
        score += 25
        highlights.append("No EXIF metadata found — may have been stripped (suspicious)")
        evidence["exif_present"] = False
        return {"score": min(score, 100), "evidence": evidence, "highlights": highlights}

    evidence["exif_present"] = True
    evidence["tag_count"] = len(tags)

    # ── Check for editing software ──
    software_tags = ['Image Software', 'Image ProcessingSoftware', 'EXIF Software']
    for tag_name in software_tags:
        if tag_name in tags:
            software = str(tags[tag_name]).lower()
            evidence["software"] = str(tags[tag_name])

            if any(ai_sw in software for ai_sw in AI_SOFTWARE):
                score += 40
                highlights.append(f"AI generation software detected: {tags[tag_name]}")
            elif any(edit_sw in software for edit_sw in EDITING_SOFTWARE):
                score += 20
                highlights.append(f"Image editing software detected: {tags[tag_name]}")
            break

    # ── Check for camera info (authentic photos usually have this) ──
    make = str(tags.get('Image Make', ''))
    model = str(tags.get('Image Model', ''))
    if make and model:
        evidence["camera"] = f"{make} {model}"
        score -= 10  # Having camera info is a positive signal
    else:
        evidence["camera"] = None

    # ── Check GPS data ──
    has_gps = any('GPS' in str(tag) for tag in tags.keys())
    evidence["has_gps"] = has_gps
    if has_gps:
        score -= 5  # GPS data suggests a real photo

    # ── Date consistency check ──
    date_tags = {
        'original': 'EXIF DateTimeOriginal',
        'digitized': 'EXIF DateTimeDigitized',
        'modified': 'Image DateTime',
    }
    dates: Dict[str, Optional[str]] = {}
    for key, tag_name in date_tags.items():
        if tag_name in tags:
            dates[key] = str(tags[tag_name])

    evidence["dates"] = dates

    if dates.get('original') and dates.get('modified'):
        if dates['original'] != dates['modified']:
            score += 15
            highlights.append("Modification date differs from original capture date")

    if not dates:
        score += 10
        highlights.append("No date metadata found")

    # ── Check image dimensions tag vs actual ──
    try:
        img = Image.open(io.BytesIO(image_bytes))
        actual_w, actual_h = img.size
        exif_w = tags.get('EXIF ExifImageWidth')
        exif_h = tags.get('EXIF ExifImageLength')
        if exif_w and exif_h:
            if int(str(exif_w)) != actual_w or int(str(exif_h)) != actual_h:
                score += 20
                highlights.append("EXIF dimensions don't match actual image dimensions (cropped/resized)")
    except Exception:
        pass

    score = max(0, min(100, score))
    return {"score": score, "evidence": evidence, "highlights": highlights}


# ══════════════════════════════════════════════════════════════
#  3. GAN FINGERPRINT DETECTION (Frequency Domain)
# ══════════════════════════════════════════════════════════════

def detect_gan_fingerprint(image_bytes: bytes) -> Dict[str, Any]:
    """
    Detects GAN-generated images using frequency-domain analysis.

    GAN-generated images often contain periodic spectral artifacts
    that appear as peaks in the Fourier transform. This is because
    upsampling layers in GANs create predictable frequency patterns.

    Uses numpy for FFT if available, falls back to a basic pixel-level check.
    """
    highlights: List[str] = []
    evidence: Dict[str, Any] = {}

    try:
        import numpy as np

        img = Image.open(io.BytesIO(image_bytes)).convert('L')  # Grayscale
        img_resized = img.resize((256, 256))
        img_array = np.array(img_resized, dtype=np.float64)

        # ── 2D FFT ──
        f_transform = np.fft.fft2(img_array)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.log1p(np.abs(f_shift))

        # ── Analyze spectral characteristics ──
        center_y, center_x = magnitude.shape[0] // 2, magnitude.shape[1] // 2

        # Ratio of high-frequency energy to total energy
        # GAN images tend to have more energy in specific high-frequency bands
        total_energy = np.sum(magnitude)
        center_mask = np.zeros_like(magnitude, dtype=bool)
        radius = 30
        y, x = np.ogrid[-center_y:magnitude.shape[0] - center_y, -center_x:magnitude.shape[1] - center_x]
        center_mask[y * y + x * x <= radius * radius] = True

        low_freq_energy = np.sum(magnitude[center_mask])
        high_freq_energy = total_energy - low_freq_energy
        hf_ratio = high_freq_energy / max(total_energy, 1e-10)

        evidence["high_freq_ratio"] = round(float(hf_ratio), 4)
        evidence["total_spectral_energy"] = round(float(total_energy), 2)

        # ── Check for periodic peaks (GAN artifacts) ──
        # Look for unusually strong peaks outside the center
        outer_region = magnitude.copy()
        outer_region[center_mask] = 0
        peak_threshold = np.mean(outer_region) + 3 * np.std(outer_region)
        num_peaks = int(np.sum(outer_region > peak_threshold))

        evidence["spectral_peaks"] = num_peaks
        evidence["peak_threshold"] = round(float(peak_threshold), 2)

        # ── Checkerboard artifact detection ──
        # GAN upsampling creates checkerboard patterns visible in high-freq
        # Check corners of FFT (where checkerboard would appear)
        corner_size = 20
        corners = [
            magnitude[:corner_size, :corner_size],
            magnitude[:corner_size, -corner_size:],
            magnitude[-corner_size:, :corner_size],
            magnitude[-corner_size:, -corner_size:],
        ]
        corner_energy = sum(float(np.mean(c)) for c in corners) / 4
        center_energy = float(np.mean(magnitude[center_mask]))
        corner_ratio = corner_energy / max(center_energy, 1e-10)

        evidence["corner_energy_ratio"] = round(corner_ratio, 4)

        # ── Scoring ──
        score = 0

        # High-frequency ratio scoring
        if hf_ratio > 0.85:
            score += 30
            highlights.append("Unusually high spectral energy in high frequencies")
        elif hf_ratio > 0.75:
            score += 15

        # Periodic peaks scoring
        if num_peaks > 50:
            score += 30
            highlights.append(f"Detected {num_peaks} periodic spectral peaks (GAN artifact signature)")
        elif num_peaks > 25:
            score += 15

        # Corner energy scoring (checkerboard artifacts)
        if corner_ratio > 0.4:
            score += 25
            highlights.append("Checkerboard artifacts detected in frequency domain")
        elif corner_ratio > 0.25:
            score += 10

        score = max(0, min(100, score))
        evidence["analysis_method"] = "fft_spectral"

        return {"score": score, "evidence": evidence, "highlights": highlights}

    except ImportError:
        logger.warning("numpy not installed, using basic pixel-level GAN check")
        return _basic_gan_check(image_bytes)

    except Exception as e:
        logger.error(f"GAN fingerprint detection error: {e}")
        return {"score": 50, "evidence": {"error": str(e)}, "highlights": []}


def _basic_gan_check(image_bytes: bytes) -> Dict[str, Any]:
    """
    Fallback GAN detection without numpy.
    Checks for color distribution uniformity (GAN images often have
    smoother color transitions than real photos).
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_small = img.resize((64, 64))
        pixels = list(img_small.getdata())

        # Calculate color channel histograms
        r_vals = [p[0] for p in pixels]
        g_vals = [p[1] for p in pixels]
        b_vals = [p[2] for p in pixels]

        # Check for unnaturally smooth gradients
        def calc_roughness(vals):
            diffs = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
            return sum(diffs) / max(len(diffs), 1)

        roughness = (calc_roughness(r_vals) + calc_roughness(g_vals) + calc_roughness(b_vals)) / 3

        score = 0
        highlights = []
        if roughness < 10:
            score += 30
            highlights.append("Unusually smooth color transitions (possible GAN artifact)")

        return {
            "score": min(score, 100),
            "evidence": {"analysis_method": "basic_pixel", "color_roughness": round(roughness, 2)},
            "highlights": highlights,
        }

    except Exception as e:
        return {"score": 50, "evidence": {"error": str(e)}, "highlights": []}


# ══════════════════════════════════════════════════════════════
#  COMBINED IMAGE ANALYSIS
# ══════════════════════════════════════════════════════════════

def analyze_image(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Entrypoint for image forensics. Runs all three analysis methods
    and returns a list of signal dicts ready for the scan pipeline.

    Returns list of signals: [ela_signal, exif_signal, gan_signal]
    """
    signals: List[Dict[str, Any]] = []

    # ── 1. Error Level Analysis ──
    ela_result = calculate_ela(image_bytes)
    signals.append({
        "score": ela_result["score"],
        "confidence": 0.80,
        "label": "Error Level Analysis (ELA)",
        "type": "image",
        "evidence": ela_result,
        "highlights": (
            ["High variance in error levels detected — possible pixel-level splicing"]
            if ela_result["score"] > 60 else []
        ),
    })

    # ── 2. EXIF Metadata Analysis ──
    exif_result = analyze_exif(image_bytes)
    signals.append({
        "score": exif_result["score"],
        "confidence": 0.90,
        "label": "EXIF Metadata Analysis",
        "type": "metadata",
        "evidence": exif_result["evidence"],
        "highlights": exif_result["highlights"],
    })

    # ── 3. GAN Fingerprint Detection ──
    gan_result = detect_gan_fingerprint(image_bytes)
    signals.append({
        "score": gan_result["score"],
        "confidence": 0.75,
        "label": "GAN Fingerprint Detection",
        "type": "image",
        "evidence": gan_result["evidence"],
        "highlights": gan_result["highlights"],
    })

    return signals
