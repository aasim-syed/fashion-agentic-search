# backend/app/retreiver.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

import requests

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "fashion200k")


def _to_qdrant_filter(filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Converts your simple dict filters into Qdrant REST filter JSON.

    Example input:
      {"color": ["black"], "category": "dresses"}

    Output (Qdrant):
      {"must": [
          {"key":"color","match":{"any":["black"]}},
          {"key":"category","match":{"value":"dresses"}}
      ]}
    """
    if not filters or not isinstance(filters, dict):
        return None

    must = []
    for key, val in filters.items():
        if val is None:
            continue

        # list -> match any
        if isinstance(val, list):
            if len(val) == 0:
                continue
            must.append({"key": key, "match": {"any": val}})
        # scalar -> match value
        else:
            must.append({"key": key, "match": {"value": val}})

    return {"must": must} if must else None


class Retriever:
    """
    Qdrant retriever using REST API (works regardless of python qdrant-client version).
    """

    def __init__(self, qdrant_url: str = QDRANT_URL, collection: str = COLLECTION_NAME):
        self.qdrant_url = qdrant_url.rstrip("/")
        self.collection = collection

    def search(
        self,
        vector_name: str,
        query_vector: Union[List[float], Any],
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        vector_name: "text" or "image" (named vector in Qdrant)
        query_vector: list[float]
        """
        # convert numpy/torch to list
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()

        if not isinstance(query_vector, list):
            raise TypeError("query_vector must be a list[float] (or array-like with .tolist())")

        url = f"{self.qdrant_url}/collections/{self.collection}/points/search"

        body: Dict[str, Any] = {
            "limit": int(top_k),
            "with_payload": bool(with_payload),
            # Named vector format:
            "vector": {"name": vector_name, "vector": query_vector},
        }

        q_filter = _to_qdrant_filter(filters)
        if q_filter:
            body["filter"] = q_filter

        r = requests.post(url, json=body, timeout=60)

        if r.status_code != 200:
            raise RuntimeError(f"Qdrant search failed: HTTP {r.status_code} - {r.text}")

        data = r.json()
        hits = data.get("result") or []
        out: List[Dict[str, Any]] = []

        for h in hits:
            out.append(
                {
                    "id": h.get("id"),
                    "score": float(h.get("score", 0.0)),
                    "payload": h.get("payload") or {},
                }
            )

        return out
