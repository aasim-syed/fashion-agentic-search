# backend/app/planner.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

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
- intermediate_queries must be list of objects with keys: query, weight
- top_k must be int 1..50
- filters must be an object (can be empty)
- DO NOT wrap in ``` fences
"""


def _extract_json(raw: str) -> Dict[str, Any]:
    s = (raw or "").strip()

    # If model still outputs garbage, extract first {...last}
    i = s.find("{")
    j = s.rfind("}")
    if i == -1 or j == -1 or j <= i:
        raise ValueError("Planner output did not contain JSON object")

    return json.loads(s[i : j + 1])


def _normalize(p: Dict[str, Any], message: str, has_image: bool) -> Dict[str, Any]:
    iq = p.get("intermediate_queries")
    if not isinstance(iq, list) or not iq:
        iq = [{"query": message, "weight": 1.0}]

    fixed = []
    for it in iq:
        if isinstance(it, str):
            fixed.append({"query": it, "weight": 1.0})
        elif isinstance(it, dict):
            q = it.get("query", message)
            w = it.get("weight", 1.0)
            if not isinstance(q, str):
                q = str(q)
            try:
                w = float(w)
            except Exception:
                w = 1.0
            fixed.append({"query": q, "weight": w})
        else:
            fixed.append({"query": message, "weight": 1.0})

    weights = p.get("weights") if isinstance(p.get("weights"), dict) else {}
    try:
        text_w = float(weights.get("text", 1.0))
    except Exception:
        text_w = 1.0
    try:
        img_w = float(weights.get("image", 0.0 if not has_image else 0.3))
    except Exception:
        img_w = 0.0 if not has_image else 0.3

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
        "intermediate_queries": fixed,
        "weights": {"text": text_w, "image": img_w},
        "top_k": top_k,
        "filters": filters,
    }


def plan(message: str, has_image: bool, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    prompt = f"""
User message: {message}
Has image: {has_image}
Chat history: {chat_history or []}

Return JSON plan only.
""".strip()

    # If Ollama OOM, we fallback cleanly (so assignment still runs)
    try:
        raw = ollama_generate(system=PLANNER_SYSTEM, user=prompt, model="mistral:latest", timeout_s=600)
        parsed = _extract_json(raw)
        return _normalize(parsed, message, has_image)
    except Exception as e:
        print("❌ Planner failed, fallback used:", repr(e))
        return {
            "intermediate_queries": [{"query": message, "weight": 1.0}],
            "weights": {"text": 1.0, "image": 0.0 if not has_image else 0.3},
            "top_k": 10,
            "filters": {},
        }
