# backend/app/responder.py
from __future__ import annotations

from typing import Any, Dict, List


def build_assistant_message(query_used: str, plan: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """
    Lightweight responder: no LLM required.
    Produces Perplexity-style short summary.
    """
    top = results[:3]
    if not top:
        return f'I couldn’t find good matches for "{query_used}". Try adding details like fabric, occasion, or fit.'

    # Extract a few hints from plan filters
    filters = plan.get("filters") or {}
    ftxt = ""
    if filters:
        parts = []
        for k, v in filters.items():
            if isinstance(v, list):
                parts.append(f"{k}={','.join(map(str, v))}")
            else:
                parts.append(f"{k}={v}")
        if parts:
            ftxt = " (filters: " + "; ".join(parts) + ")"

    return (
        f'Here are the closest matches for "{query_used}"{ftxt}. '
        f"Top hit score: {top[0].get('score'):.2f}. "
        "You can upload an image to prioritize visual similarity, or add constraints like color/occasion."
    )
