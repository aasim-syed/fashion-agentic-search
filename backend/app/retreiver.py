# backend/app/retreiver.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Literal, Union

import requests

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "fashion200k")


def _to_list(vec: Any) -> List[float]:
    """Accepts numpy / torch / list and returns python list[float]."""
    if vec is None:
        return []
    if hasattr(vec, "tolist"):
        vec = vec.tolist()
    if isinstance(vec, (list, tuple)):
        return [float(x) for x in vec]
    raise TypeError(f"Vector must be list-like. Got {type(vec)}")


class Retriever:
    """
    Qdrant retriever using REST.

    Collection config shows named vectors:
      - text
      - image

    So we MUST use vector: {name: "...", vector: [...]}
    """

    def __init__(self, qdrant_url: str = QDRANT_URL, collection: str = COLLECTION_NAME):
        self.qdrant_url = qdrant_url.rstrip("/")
        self.collection = collection

    def _search_rest(
        self,
        vector_name: str,
        vector: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.qdrant_url}/collections/{self.collection}/points/search"

        body: Dict[str, Any] = {
            "limit": int(top_k),
            "with_payload": True,
            "with_vector": False,
            "vector": {"name": vector_name, "vector": vector},
        }

        # (Optional) If later you implement proper Qdrant filter schema, put it here
        # For now: ignore filters if they are not already in Qdrant format
        # to prevent 400s from invalid filter structure.
        if isinstance(filters, dict) and filters:
            # Only pass if it already looks like Qdrant filter
            # e.g. {"must":[{"key":"color","match":{"any":["black"]}}]}
            if any(k in filters for k in ("must", "should", "must_not")):
                body["filter"] = filters

        r = requests.post(url, json=body, timeout=120)
        if not r.ok:
            raise RuntimeError(f"Qdrant search failed {r.status_code}: {r.text}")

        return r.json().get("result", []) or []

    def search(
        self,
        mode: Literal["text", "image"],
        query_vector: Union[List[float], Any],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        vec = _to_list(query_vector)
        if not vec:
            return []

        if mode not in ("text", "image"):
            raise ValueError("mode must be 'text' or 'image'")

        # ✅ vector names must match your collection config exactly
        vector_name = "text" if mode == "text" else "image"

        hits = self._search_rest(vector_name=vector_name, vector=vec, top_k=top_k, filters=filters)

        # Normalize to a simple dict list that your main.py can handle
        out: List[Dict[str, Any]] = []
        for h in hits:
            payload = h.get("payload") or {}
            out.append(
                {
                    "id": h.get("id"),
                    "score": float(h.get("score", 0.0)),
                    "payload": payload,
                    # convenience mirrors (so you don't lose them)
                    "product_id": payload.get("product_id"),
                    "description": payload.get("description"),
                    "image_path": payload.get("image_path") or payload.get("image_abs_path"),
                }
            )
        return out
