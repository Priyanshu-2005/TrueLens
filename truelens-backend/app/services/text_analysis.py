# """
# TrueLens Text Analysis Service
# ==============================
# Multi-signal text analysis combining:
#   1. Transformer-based AI detection (DistilBERT/RoBERTa) — primary signal
#   2. Stylometry heuristics (burstiness, vocabulary richness) — secondary signal

# Falls back gracefully to stylometry-only if transformers aren't available.
# """

# import re
# import math
# import logging
# from typing import Dict, Any, List, Optional

# logger = logging.getLogger(__name__)

# # ── Lazy-load transformer model to avoid import-time overhead ──
# _transformer_pipeline = None
# _transformer_load_attempted = False


# def _get_transformer_pipeline():
#     """
#     Lazily loads the HuggingFace text classification pipeline.
#     Uses a RoBERTa model fine-tuned for AI-generated text detection.
#     Falls back to None if transformers/torch are not installed.
#     """
#     global _transformer_pipeline, _transformer_load_attempted

#     if _transformer_load_attempted:
#         return _transformer_pipeline

#     _transformer_load_attempted = True

#     try:
#         from transformers import pipeline

#         # Try a well-known AI-detection model first
#         model_candidates = [
#             "roberta-base-openai-detector",  # OpenAI's GPT-2 detector
#             "Hello-SimpleAI/chatgpt-detector-roberta",
#         ]

#         for model_name in model_candidates:
#             try:
#                 logger.info(f"Loading transformer model: {model_name}")
#                 _transformer_pipeline = pipeline(
#                     "text-classification",
#                     model=model_name,
#                     truncation=True,
#                     max_length=512,
#                 )
#                 logger.info(f"Successfully loaded: {model_name}")
#                 return _transformer_pipeline
#             except Exception as e:
#                 logger.warning(f"Failed to load {model_name}: {e}")
#                 continue

#         logger.warning("No transformer model available. Using stylometry-only mode.")
#         return None

#     except ImportError:
#         logger.warning(
#             "transformers/torch not installed. Using stylometry-only mode. "
#             "Install with: pip install transformers torch"
#         )
#         return None


# # ══════════════════════════════════════════════════════════════
# #  STYLOMETRY ANALYSIS
# # ══════════════════════════════════════════════════════════════

# def _extract_stylometry_features(text: str) -> Dict[str, float]:
#     """
#     Extracts linguistic features that distinguish human vs AI writing.
#     Returns a dictionary of features with their calculated values.
#     """
#     sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
#     words = text.split()
#     unique_words = set(w.lower() for w in words)

#     num_sentences = max(len(sentences), 1)
#     num_words = max(len(words), 1)
#     num_unique = max(len(unique_words), 1)

#     # ── Sentence-level features ──
#     words_per_sentence = [len(s.split()) for s in sentences] if sentences else [0]
#     avg_sentence_length = sum(words_per_sentence) / num_sentences
#     sentence_variance = (
#         sum((x - avg_sentence_length) ** 2 for x in words_per_sentence) / num_sentences
#     )

#     # ── Burstiness (paragraph length variation) ──
#     paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
#     para_lengths = [len(p.split()) for p in paragraphs] if paragraphs else [num_words]
#     avg_para_len = sum(para_lengths) / max(len(para_lengths), 1)
#     burstiness = (
#         math.sqrt(
#             sum((x - avg_para_len) ** 2 for x in para_lengths) / max(len(para_lengths), 1)
#         )
#         / max(avg_para_len, 1)
#         if len(para_lengths) > 1
#         else 0.5
#     )

#     # ── Vocabulary richness (Type-Token Ratio) ──
#     vocabulary_richness = num_unique / num_words

#     # ── Punctuation density ──
#     punctuation_count = len(re.findall(r'[.,;:!?\'"()\-—]', text))
#     punctuation_density = punctuation_count / num_words

#     # ── Word repetition ──
#     word_freq: Dict[str, int] = {}
#     for w in words:
#         lower = w.lower()
#         word_freq[lower] = word_freq.get(lower, 0) + 1
#     repeated_words = sum(1 for freq in word_freq.values() if freq > 2)
#     repetition_score = repeated_words / num_unique

#     # ── Average word length (AI tends toward longer, formal words) ──
#     avg_word_length = sum(len(w) for w in words) / num_words

#     # ── All-caps ratio (spam signal) ──
#     caps_words = [w for w in words if w == w.upper() and len(w) > 1 and w.isalpha()]
#     all_caps_ratio = len(caps_words) / num_words

#     # ── Exclamation density ──
#     exclamation_count = text.count('!')

#     # ── Hapax legomena ratio (words appearing exactly once) ──
#     hapax = sum(1 for freq in word_freq.values() if freq == 1)
#     hapax_ratio = hapax / num_unique

#     # ── Connective word ratio (AI overuses "Furthermore", "Moreover", etc.) ──
#     connectives = {
#         'furthermore', 'moreover', 'additionally', 'consequently', 'nevertheless',
#         'subsequently', 'therefore', 'nonetheless', 'accordingly', 'hence',
#         'thus', 'meanwhile', 'conversely', 'alternatively', 'specifically',
#     }
#     connective_count = sum(1 for w in words if w.lower() in connectives)
#     connective_ratio = connective_count / num_words

#     return {
#         "avg_sentence_length": round(avg_sentence_length, 2),
#         "sentence_variance": round(sentence_variance, 2),
#         "burstiness": round(burstiness, 4),
#         "vocabulary_richness": round(vocabulary_richness, 4),
#         "punctuation_density": round(punctuation_density, 4),
#         "repetition_score": round(repetition_score, 4),
#         "avg_word_length": round(avg_word_length, 2),
#         "all_caps_ratio": round(all_caps_ratio, 4),
#         "exclamation_count": exclamation_count,
#         "hapax_ratio": round(hapax_ratio, 4),
#         "connective_ratio": round(connective_ratio, 4),
#         "num_sentences": num_sentences,
#         "num_words": num_words,
#     }


# def analyze_text_stylometry(text: str) -> Dict[str, Any]:
#     """
#     Stylometry-based AI text detection.
#     Scores 0-100 where higher = more likely AI-generated (fake).
#     """
#     try:
#         features = _extract_stylometry_features(text)
#         highlights: List[str] = []

#         # Start with a base probability
#         fake_probability = 50.0

#         # ── Burstiness: human text has more variation ──
#         if features["burstiness"] > 0.4:
#             fake_probability -= 15
#         elif features["burstiness"] < 0.15:
#             fake_probability += 15
#             highlights.append("Very uniform paragraph structure (low burstiness)")

#         # ── Sentence length variance ──
#         if features["sentence_variance"] > 50:
#             fake_probability -= 10
#         elif features["sentence_variance"] < 8:
#             fake_probability += 12
#             highlights.append("Very uniform sentence lengths")

#         # ── Vocabulary richness ──
#         if features["vocabulary_richness"] > 0.7:
#             fake_probability -= 8
#         elif features["vocabulary_richness"] < 0.35:
#             fake_probability += 10
#             highlights.append("Low vocabulary diversity")

#         # ── Connective word overuse (AI signature) ──
#         if features["connective_ratio"] > 0.03:
#             fake_probability += 10
#             highlights.append("Overuse of formal connective words")
#         elif features["connective_ratio"] > 0.02:
#             fake_probability += 5

#         # ── Hapax ratio: human text has more unique words ──
#         if features["hapax_ratio"] > 0.65:
#             fake_probability -= 5
#         elif features["hapax_ratio"] < 0.4:
#             fake_probability += 5

#         # ── Punctuation density (natural range: 0.15-0.35) ──
#         if 0.15 < features["punctuation_density"] < 0.35:
#             fake_probability -= 3
#         elif features["punctuation_density"] < 0.08:
#             fake_probability += 5
#             highlights.append("Unusually low punctuation density")

#         # ── Spam signals ──
#         if features["all_caps_ratio"] > 0.15:
#             fake_probability += 10
#             highlights.append("Excessive ALL CAPS usage")
#         if features["exclamation_count"] > 5:
#             fake_probability += 8
#             highlights.append("Excessive exclamation marks")

#         # ── Average word length (AI tends toward formal, longer words) ──
#         if features["avg_word_length"] > 5.5:
#             fake_probability += 5
#             highlights.append("Unusually formal word choice")

#         # ── Keyword dead giveaways ──
#         lower_text = text.lower()
#         if "as an ai" in lower_text or "language model" in lower_text:
#             fake_probability = 99
#             highlights.append('Contains AI self-identification phrases')
#         elif "i cannot" in lower_text and "ethical" in lower_text:
#             fake_probability = max(fake_probability, 90)
#             highlights.append("Contains AI refusal patterns")

#         fake_probability = max(0, min(100, fake_probability))
#         confidence = min(0.85, 0.5 + abs(fake_probability - 50) / 100)

#         return {
#             "score": round(fake_probability),
#             "confidence": round(confidence, 3),
#             "label": "Stylometric Text Analysis",
#             "type": "text",
#             "evidence": {
#                 **features,
#                 "model_used": "advanced_stylometry_v2",
#             },
#             "highlights": highlights,
#         }

#     except Exception as e:
#         logger.error(f"Stylometry analysis failed: {e}")
#         return {
#             "score": 50,
#             "confidence": 0.0,
#             "label": "Stylometric Text Analysis",
#             "type": "text",
#             "evidence": {"error": str(e)},
#             "highlights": [],
#         }


# # ══════════════════════════════════════════════════════════════
# #  TRANSFORMER-BASED ANALYSIS
# # ══════════════════════════════════════════════════════════════

# def analyze_text_transformer(text: str) -> Optional[Dict[str, Any]]:
#     """
#     Uses a fine-tuned transformer model (RoBERTa) for AI text detection.
#     Returns None if the model is unavailable.

#     The model classifies text as 'Real' or 'Fake' (AI-generated).
#     Score: 0-100 where higher = more likely AI-generated.
#     """
#     pipe = _get_transformer_pipeline()
#     if pipe is None:
#         return None

#     try:
#         # Truncate to model's max length; use the first 512 tokens' worth
#         truncated = text[:2048]
#         results = pipe(truncated)

#         if not results:
#             return None

#         result = results[0]
#         label = result["label"].upper()
#         raw_score = result["score"]

#         # Normalize: higher score = more likely fake/AI
#         if label in ("FAKE", "LABEL_1"):
#             fake_probability = raw_score * 100
#         else:
#             fake_probability = (1 - raw_score) * 100

#         fake_probability = max(0, min(100, fake_probability))
#         confidence = raw_score  # The model's own confidence

#         highlights = []
#         if fake_probability > 70:
#             highlights.append(f"Transformer model ({pipe.model.name_or_path}) flagged as AI-generated")
#         elif fake_probability < 30:
#             highlights.append(f"Transformer model ({pipe.model.name_or_path}) classified as human-written")

#         return {
#             "score": round(fake_probability),
#             "confidence": round(confidence, 3),
#             "label": "AI Text Detection (Transformer)",
#             "type": "text",
#             "evidence": {
#                 "model_used": pipe.model.name_or_path,
#                 "raw_label": label,
#                 "raw_score": round(raw_score, 4),
#             },
#             "highlights": highlights,
#         }

#     except Exception as e:
#         logger.error(f"Transformer analysis failed: {e}")
#         return None


# # ══════════════════════════════════════════════════════════════
# #  ENSEMBLE TEXT ANALYSIS
# # ══════════════════════════════════════════════════════════════

# def analyze_text_ensemble(text: str) -> Dict[str, Any]:
#     """
#     Combines transformer and stylometry signals into a single text analysis result.

#     Weighting:
#       - Transformer available: 70% transformer + 30% stylometry
#       - Transformer unavailable: 100% stylometry
#     """
#     stylometry_result = analyze_text_stylometry(text)
#     transformer_result = analyze_text_transformer(text)

#     if transformer_result is None:
#         # Fallback: stylometry only
#         logger.info("Using stylometry-only mode (transformer unavailable)")
#         return stylometry_result

#     # ── Weighted ensemble ──
#     TRANSFORMER_WEIGHT = 0.70
#     STYLOMETRY_WEIGHT = 0.30

#     ensemble_score = (
#         transformer_result["score"] * TRANSFORMER_WEIGHT
#         + stylometry_result["score"] * STYLOMETRY_WEIGHT
#     )
#     ensemble_confidence = (
#         transformer_result["confidence"] * TRANSFORMER_WEIGHT
#         + stylometry_result["confidence"] * STYLOMETRY_WEIGHT
#     )

#     # Merge highlights
#     all_highlights = list(set(
#         transformer_result.get("highlights", [])
#         + stylometry_result.get("highlights", [])
#     ))

#     # Merge evidence
#     merged_evidence = {
#         "ensemble_mode": "transformer_stylometry",
#         "transformer_score": transformer_result["score"],
#         "stylometry_score": stylometry_result["score"],
#         "transformer_weight": TRANSFORMER_WEIGHT,
#         "stylometry_weight": STYLOMETRY_WEIGHT,
#         "transformer_model": transformer_result["evidence"].get("model_used", "unknown"),
#         # Include stylometry features for transparency
#         **{k: v for k, v in stylometry_result["evidence"].items() if k != "model_used"},
#     }

#     return {
#         "score": round(ensemble_score),
#         "confidence": round(ensemble_confidence, 3),
#         "label": "AI Text Detection (Ensemble)",
#         "type": "text",
#         "evidence": merged_evidence,
#         "highlights": all_highlights,
#     }
"""
TrueLens Text Analysis Service
==============================
Multi-signal text analysis combining:
  1. Transformer-based AI detection (fakespot-ai/roberta-base-ai-text-detection-v1) — primary signal
  2. Stylometry heuristics (burstiness, vocabulary richness) — secondary signal

Falls back gracefully to stylometry-only if transformers aren't available.
"""

import re
import math
import logging
from html import unescape
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Lazy-load transformer model to avoid import-time overhead ──
_transformer_pipeline = None
_transformer_load_attempted = False


# ══════════════════════════════════════════════════════════════
#  FAKESPOT TEXT PREPROCESSING
#  Mirrors utils.py from fakespot-ai/roberta-base-ai-text-detection-v1
#  Applied before inference for best model accuracy.
# ══════════════════════════════════════════════════════════════

def _fakespot_clean_text(text: str) -> str:
    """
    Pre-processing recommended by fakespot-ai/roberta-base-ai-text-detection-v1.
    Strips markdown formatting and normalises whitespace.
    Mirrors the clean_text + clean_markdown functions in the model's utils.py.
    """
    # ── Strip markdown ──
    # Remove fenced code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]*`', '', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove links but keep link text
    text = re.sub(r'\[([^\]]+)\]\(.*?\)', r'\1', text)
    # Remove bold and italic
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove headings
    text = re.sub(r'#+ ', '', text)
    # Remove blockquotes
    text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
    # Remove list markers
    text = re.sub(r'^(\s*[-*+]|\d+\.)\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove tables
    text = re.sub(r'\|.*?\|', '', text)
    # Remove raw HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Decode HTML entities
    text = unescape(text)

    # ── Normalise whitespace ──
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = text.replace("^M", " ")
    text = text.replace("\r", " ")
    text = text.replace(" ,", ",")
    text = re.sub(r' +', ' ', text)

    return text.strip()


# ══════════════════════════════════════════════════════════════
#  TRANSFORMER PIPELINE LOADER
# ══════════════════════════════════════════════════════════════

def _get_transformer_pipeline():
    """
    Lazily loads the HuggingFace text classification pipeline.
    Uses fakespot-ai/roberta-base-ai-text-detection-v1, a RoBERTa model
    fine-tuned specifically for AI-generated text detection.
    Falls back to None if transformers/torch are not installed.
    """
    global _transformer_pipeline, _transformer_load_attempted

    if _transformer_load_attempted:
        return _transformer_pipeline

    _transformer_load_attempted = True

    try:
        from transformers import pipeline

        model_name = "fakespot-ai/roberta-base-ai-text-detection-v1"

        try:
            logger.info(f"Loading transformer model: {model_name}")
            _transformer_pipeline = pipeline(
                "text-classification",
                model=model_name,
                truncation=True,
                max_length=512,
            )
            logger.info(f"Successfully loaded: {model_name}")
            return _transformer_pipeline
        except Exception as e:
            logger.warning(f"Failed to load {model_name}: {e}")

        logger.warning("Transformer model unavailable. Using stylometry-only mode.")
        return None

    except ImportError:
        logger.warning(
            "transformers/torch not installed. Using stylometry-only mode. "
            "Install with: pip install transformers torch"
        )
        return None


# ══════════════════════════════════════════════════════════════
#  STYLOMETRY ANALYSIS
# ══════════════════════════════════════════════════════════════

def _extract_stylometry_features(text: str) -> Dict[str, float]:
    """
    Extracts linguistic features that distinguish human vs AI writing.
    Returns a dictionary of features with their calculated values.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = text.split()
    unique_words = set(w.lower() for w in words)

    num_sentences = max(len(sentences), 1)
    num_words = max(len(words), 1)
    num_unique = max(len(unique_words), 1)

    # ── Sentence-level features ──
    words_per_sentence = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sentence_length = sum(words_per_sentence) / num_sentences
    sentence_variance = (
        sum((x - avg_sentence_length) ** 2 for x in words_per_sentence) / num_sentences
    )

    # ── Burstiness (paragraph length variation) ──
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    para_lengths = [len(p.split()) for p in paragraphs] if paragraphs else [num_words]
    avg_para_len = sum(para_lengths) / max(len(para_lengths), 1)
    burstiness = (
        math.sqrt(
            sum((x - avg_para_len) ** 2 for x in para_lengths) / max(len(para_lengths), 1)
        )
        / max(avg_para_len, 1)
        if len(para_lengths) > 1
        else 0.5
    )

    # ── Vocabulary richness (Type-Token Ratio) ──
    vocabulary_richness = num_unique / num_words

    # ── Punctuation density ──
    punctuation_count = len(re.findall(r'[.,;:!?\'"()\-—]', text))
    punctuation_density = punctuation_count / num_words

    # ── Word repetition ──
    word_freq: Dict[str, int] = {}
    for w in words:
        lower = w.lower()
        word_freq[lower] = word_freq.get(lower, 0) + 1
    repeated_words = sum(1 for freq in word_freq.values() if freq > 2)
    repetition_score = repeated_words / num_unique

    # ── Average word length (AI tends toward longer, formal words) ──
    avg_word_length = sum(len(w) for w in words) / num_words

    # ── All-caps ratio (spam signal) ──
    caps_words = [w for w in words if w == w.upper() and len(w) > 1 and w.isalpha()]
    all_caps_ratio = len(caps_words) / num_words

    # ── Exclamation density ──
    exclamation_count = text.count('!')

    # ── Hapax legomena ratio (words appearing exactly once) ──
    hapax = sum(1 for freq in word_freq.values() if freq == 1)
    hapax_ratio = hapax / num_unique

    # ── Connective word ratio (AI overuses "Furthermore", "Moreover", etc.) ──
    connectives = {
        'furthermore', 'moreover', 'additionally', 'consequently', 'nevertheless',
        'subsequently', 'therefore', 'nonetheless', 'accordingly', 'hence',
        'thus', 'meanwhile', 'conversely', 'alternatively', 'specifically',
    }
    connective_count = sum(1 for w in words if w.lower() in connectives)
    connective_ratio = connective_count / num_words

    return {
        "avg_sentence_length": round(avg_sentence_length, 2),
        "sentence_variance": round(sentence_variance, 2),
        "burstiness": round(burstiness, 4),
        "vocabulary_richness": round(vocabulary_richness, 4),
        "punctuation_density": round(punctuation_density, 4),
        "repetition_score": round(repetition_score, 4),
        "avg_word_length": round(avg_word_length, 2),
        "all_caps_ratio": round(all_caps_ratio, 4),
        "exclamation_count": exclamation_count,
        "hapax_ratio": round(hapax_ratio, 4),
        "connective_ratio": round(connective_ratio, 4),
        "num_sentences": num_sentences,
        "num_words": num_words,
    }


def analyze_text_stylometry(text: str) -> Dict[str, Any]:
    """
    Stylometry-based AI text detection.
    Scores 0-100 where higher = more likely AI-generated (fake).
    """
    try:
        features = _extract_stylometry_features(text)
        highlights: List[str] = []

        # Start with a base probability
        fake_probability = 50.0

        # ── Burstiness: human text has more variation ──
        if features["burstiness"] > 0.4:
            fake_probability -= 15
        elif features["burstiness"] < 0.15:
            fake_probability += 15
            highlights.append("Very uniform paragraph structure (low burstiness)")

        # ── Sentence length variance ──
        if features["sentence_variance"] > 50:
            fake_probability -= 10
        elif features["sentence_variance"] < 8:
            fake_probability += 12
            highlights.append("Very uniform sentence lengths")

        # ── Vocabulary richness ──
        if features["vocabulary_richness"] > 0.7:
            fake_probability -= 8
        elif features["vocabulary_richness"] < 0.35:
            fake_probability += 10
            highlights.append("Low vocabulary diversity")

        # ── Connective word overuse (AI signature) ──
        if features["connective_ratio"] > 0.03:
            fake_probability += 10
            highlights.append("Overuse of formal connective words")
        elif features["connective_ratio"] > 0.02:
            fake_probability += 5

        # ── Hapax ratio: human text has more unique words ──
        if features["hapax_ratio"] > 0.65:
            fake_probability -= 5
        elif features["hapax_ratio"] < 0.4:
            fake_probability += 5

        # ── Punctuation density (natural range: 0.15-0.35) ──
        if 0.15 < features["punctuation_density"] < 0.35:
            fake_probability -= 3
        elif features["punctuation_density"] < 0.08:
            fake_probability += 5
            highlights.append("Unusually low punctuation density")

        # ── Spam signals ──
        if features["all_caps_ratio"] > 0.15:
            fake_probability += 10
            highlights.append("Excessive ALL CAPS usage")
        if features["exclamation_count"] > 5:
            fake_probability += 8
            highlights.append("Excessive exclamation marks")

        # ── Average word length (AI tends toward formal, longer words) ──
        if features["avg_word_length"] > 5.5:
            fake_probability += 5
            highlights.append("Unusually formal word choice")

        # ── Keyword dead giveaways ──
        lower_text = text.lower()
        if "as an ai" in lower_text or "language model" in lower_text:
            fake_probability = 99
            highlights.append('Contains AI self-identification phrases')
        elif "i cannot" in lower_text and "ethical" in lower_text:
            fake_probability = max(fake_probability, 90)
            highlights.append("Contains AI refusal patterns")

        fake_probability = max(0, min(100, fake_probability))
        confidence = min(0.85, 0.5 + abs(fake_probability - 50) / 100)

        return {
            "score": round(fake_probability),
            "confidence": round(confidence, 3),
            "label": "Stylometric Text Analysis",
            "type": "text",
            "evidence": {
                **features,
                "model_used": "advanced_stylometry_v2",
            },
            "highlights": highlights,
        }

    except Exception as e:
        logger.error(f"Stylometry analysis failed: {e}")
        return {
            "score": 50,
            "confidence": 0.0,
            "label": "Stylometric Text Analysis",
            "type": "text",
            "evidence": {"error": str(e)},
            "highlights": [],
        }


# ══════════════════════════════════════════════════════════════
#  TRANSFORMER-BASED ANALYSIS
# ══════════════════════════════════════════════════════════════

# Label sets for the fakespot model ("AI" / "HUMAN").
# Additional aliases guard against HuggingFace renaming them.
_AI_LABELS    = {"AI", "FAKE", "LABEL_1"}
_HUMAN_LABELS = {"HUMAN", "REAL", "LABEL_0"}


def analyze_text_transformer(text: str) -> Optional[Dict[str, Any]]:
    """
    Uses fakespot-ai/roberta-base-ai-text-detection-v1 for AI text detection.
    Returns None if the model is unavailable.

    Applies the model's recommended clean_text pre-processing before inference.
    Score: 0-100 where higher = more likely AI-generated.
    """
    pipe = _get_transformer_pipeline()
    if pipe is None:
        return None

    try:
        # Apply fakespot's recommended pre-processing for best accuracy
        cleaned = _fakespot_clean_text(text)
        if not cleaned:
            logger.warning("Text was empty after cleaning; skipping transformer analysis.")
            return None

        # The pipeline handles tokenisation and truncation (max_length=512)
        results = pipe(cleaned)
        if not results:
            return None

        result = results[0]
        label     = result["label"].upper()   # e.g. "AI" or "HUMAN"
        raw_score = result["score"]           # model's confidence in its own prediction

        # Normalise to fake_probability: higher → more likely AI-generated
        if label in _AI_LABELS:
            fake_probability = raw_score * 100
        elif label in _HUMAN_LABELS:
            fake_probability = (1 - raw_score) * 100
        else:
            # Unknown label scheme — log and default to neutral
            logger.warning(
                f"Unrecognised transformer label '{label}' from model "
                f"'{pipe.model.name_or_path}'. Defaulting fake_probability to 50."
            )
            fake_probability = 50.0

        fake_probability = max(0.0, min(100.0, fake_probability))
        model_name = pipe.model.name_or_path

        highlights = []
        if fake_probability > 70:
            highlights.append(f"Transformer model ({model_name}) flagged as AI-generated")
        elif fake_probability < 30:
            highlights.append(f"Transformer model ({model_name}) classified as human-written")

        return {
            "score": round(fake_probability),
            "confidence": round(raw_score, 3),
            "label": "AI Text Detection (Transformer)",
            "type": "text",
            "evidence": {
                "model_used": model_name,
                "raw_label": label,
                "raw_score": round(raw_score, 4),
            },
            "highlights": highlights,
        }

    except Exception as e:
        logger.error(f"Transformer analysis failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  ENSEMBLE TEXT ANALYSIS
# ══════════════════════════════════════════════════════════════

def analyze_text_ensemble(text: str) -> Dict[str, Any]:
    """
    Combines transformer and stylometry signals into a single text analysis result.

    Weighting:
      - Transformer available: 70% transformer + 30% stylometry
      - Transformer unavailable: 100% stylometry
    """
    stylometry_result  = analyze_text_stylometry(text)
    transformer_result = analyze_text_transformer(text)

    if transformer_result is None:
        # Fallback: stylometry only
        logger.info("Using stylometry-only mode (transformer unavailable)")
        return stylometry_result

    # ── Weighted ensemble ──
    TRANSFORMER_WEIGHT = 0.70
    STYLOMETRY_WEIGHT  = 0.30

    ensemble_score = (
        transformer_result["score"] * TRANSFORMER_WEIGHT
        + stylometry_result["score"] * STYLOMETRY_WEIGHT
    )
    ensemble_confidence = (
        transformer_result["confidence"] * TRANSFORMER_WEIGHT
        + stylometry_result["confidence"] * STYLOMETRY_WEIGHT
    )

    # Merge highlights (deduplicated)
    all_highlights = list(set(
        transformer_result.get("highlights", [])
        + stylometry_result.get("highlights", [])
    ))

    # Merge evidence
    merged_evidence = {
        "ensemble_mode":       "transformer_stylometry",
        "transformer_score":   transformer_result["score"],
        "stylometry_score":    stylometry_result["score"],
        "transformer_weight":  TRANSFORMER_WEIGHT,
        "stylometry_weight":   STYLOMETRY_WEIGHT,
        "transformer_model":   transformer_result["evidence"].get("model_used", "unknown"),
        # Include stylometry features for transparency
        **{k: v for k, v in stylometry_result["evidence"].items() if k != "model_used"},
    }

    return {
        "score":      round(ensemble_score),
        "confidence": round(ensemble_confidence, 3),
        "label":      "AI Text Detection (Ensemble)",
        "type":       "text",
        "evidence":   merged_evidence,
        "highlights": all_highlights,
    }