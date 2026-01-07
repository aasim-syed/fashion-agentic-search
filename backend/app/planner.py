# backend/app/planner.py
import json
from typing import Any, Dict, List

from app.ollama_client import ollama_generate

PLANNER_SYSTEM = """You are a planner for a fashion search system.
Return ONLY a valid JSON object. No markdown. No backticks. No explanations.

Schema:
{
  "intermediate_queries": [{"query": string, "weight": float}],
  "weights": {"text": float, "image": float},
  "top_k": int,
  "filters": {}
}
Rules:
- intermediate_queries must be a list of objects with keys: query, weight
- weights.text + weights.image can be any floats (not necessarily sum to 1)
- top_k must be int between 1 and 50
- filters must be an object (can be empty)
"""

def _extract_json_object(raw: str) -> Dict[str, Any]:
    """
    Robust extraction:
    - strips ```json ``` wrappers
    - finds first '{' and last '}' and parses that slice
    - if multiple JSON blocks exist, this still works (takes outermost)
    """
    s = (raw or "").strip()
    s = s.replace("```json", "").replace("```", "").strip()

    i = s.find("{")
    j = s.rfind("}")
    if i == -1 or j == -1 or j <= i:
        raise ValueError("No JSON object found in planner output")

    return json.loads(s[i : j + 1])

def _normalize_plan(p: Dict[str, Any], message: str, has_image: bool) -> Dict[str, Any]:
    # Ensure keys exist + types are correct
    iq = p.get("intermediate_queries")
    if not isinstance(iq, list) or len(iq) == 0:
        iq = [{"query": message, "weight": 1.0}]

    fixed_iq = []
    for item in iq:
        if isinstance(item, str):
            fixed_iq.append({"query": item, "weight": 1.0})
        elif isinstance(item, dict):
            q = item.get("query", message)
            w = item.get("weight", 1.0)
            if not isinstance(q, str):
                q = str(q)
            try:
                w = float(w)
            except Exception:
                w = 1.0
            fixed_iq.append({"query": q, "weight": w})
        else:
            fixed_iq.append({"query": message, "weight": 1.0})

    weights = p.get("weights", {})
    if not isinstance(weights, dict):
        weights = {}
    text_w = weights.get("text", 1.0)
    image_w = weights.get("image", 0.0 if not has_image else 0.2)
    try:
        text_w = float(text_w)
    except Exception:
        text_w = 1.0
    try:
        image_w = float(image_w)
    except Exception:
        image_w = 0.0 if not has_image else 0.2

    top_k = p.get("top_k", 10)
    try:
        top_k = int(top_k)
    except Exception:
        top_k = 10
    top_k = max(1, min(50, top_k))

    filters = p.get("filters", {})
    if not isinstance(filters, dict):
        filters = {}

    return {
        "intermediate_queries": fixed_iq,
        "weights": {"text": text_w, "image": image_w},
        "top_k": top_k,
        "filters": filters,
    }

def plan(message: str, has_image: bool, chat_history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    user_prompt = f"""
User message: {message}
Has image: {has_image}
Chat history: {chat_history or []}

Return the JSON plan.
""".strip()

    try:
        raw = ollama_generate(system=PLANNER_SYSTEM, user=user_prompt, model="llama3.2:1b", timeout_s=600)
        p = _extract_json_object(raw)
        return _normalize_plan(p, message, has_image)
    except Exception as e:
        # IMPORTANT: never crash; return fallback dict plan
        print("❌ Planner failed, using fallback. Error:", repr(e))
        return {
            "intermediate_queries": [{"query": message, "weight": 1.0}],
            "weights": {"text": 1.0, "image": 0.0 if not has_image else 0.2},
            "top_k": 10,
            "filters": {},
        }
