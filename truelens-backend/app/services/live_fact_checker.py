import os
import json
import logging
import wikipedia
from typing import Dict, Any, List

# Lazy load Gemini to avoid startup crashes if missing
_gemini_model = None

logger = logging.getLogger(__name__)

def get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError("google-generativeai library is not installed.")
    return _gemini_model

def search_web_for_claim(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Searches Wikipedia for the given query and returns top snippets and URLs.
    """
    # Clean the query
    search_query = query.strip()
    lower_q = search_query.lower()
    for word in ["did ", "is ", "was ", "are ", "does ", "do ", "can ", "has ", "have "]:
        if lower_q.startswith(word):
            search_query = search_query[len(word):].strip()
            break
            
    # Remove question marks
    search_query = search_query.replace("?", "")

    results = []
    try:
        search_results = wikipedia.search(search_query, results=max_results)
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                results.append({
                    "title": page.title,
                    "snippet": page.summary[:500] + "...",
                    "url": page.url
                })
            except wikipedia.exceptions.DisambiguationError as e:
                try:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    results.append({
                        "title": page.title,
                        "snippet": page.summary[:500] + "...",
                        "url": page.url
                    })
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Wikipedia search failed: {e}")
    return results

def evaluate_claim_live(claim: str) -> Dict[str, Any]:
    """
    Performs an active web search and evaluates the claim using an LLM.
    Returns {"rating": "True|False|Mixture", "reasoning": "...", "sources": [...]}
    """
    try:
        model = get_gemini_model()
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

    # Step 1: Gather Context
    search_results = search_web_for_claim(claim, max_results=4)
    if not search_results:
        return {
            "available": True,
            "rating": "Unknown",
            "reasoning": "Could not find any relevant information on the live web to evaluate this claim.",
            "sources": []
        }

    # Format context for the prompt
    context_text = ""
    for i, res in enumerate(search_results, 1):
        context_text += f"\n[Source {i}]: {res['title']}\nSnippet: {res['snippet']}\nURL: {res['url']}\n"

    # Step 2: Evaluate with LLM
    prompt = f"""
You are a rigorous, unbiased journalistic fact-checker. Evaluate the following claim based ONLY on the provided web search context.

Claim: "{claim}"

Context:
{context_text}

Instructions:
1. Determine the 'rating': TRUE, FALSE, PARTIALLY TRUE, or UNVERIFIED. (If there is not enough context, use UNVERIFIED).
2. Provide a 'short_answer': A one-sentence direct answer to the claim.
3. Provide 'reasoning': 2-3 sentences explaining how the verdict was reached based on the context.
4. Determine the 'confidence': High, Medium, or Low (based on source agreement).
5. Output the result as raw JSON in exactly this format, with no extra text:
{{
  "rating": "FALSE",
  "short_answer": "...",
  "reasoning": "...",
  "confidence": "High"
}}
"""
    try:
        import google.generativeai as genai
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        content = response.text
        result_dict = json.loads(content)
        
        return {
            "available": True,
            "rating": result_dict.get("rating", "UNVERIFIED"),
            "short_answer": result_dict.get("short_answer", "No direct answer could be formulated."),
            "reasoning": result_dict.get("reasoning", "No reasoning provided."),
            "confidence": result_dict.get("confidence", "Low"),
            "sources": search_results
        }
    except Exception as e:
        logger.error(f"Live AI Fact Check LLM error: {e}")
        return {
            "available": False,
            "error": f"Failed to evaluate claim with Gemini: {str(e)}"
        }
