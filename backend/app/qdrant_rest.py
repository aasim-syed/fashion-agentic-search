# backend/app/qdrant_rest.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx


@dataclass
class QdrantPoint:
    id: Any
    score: float
    payload: Dict[str, Any]


class QdrantREST:
    """
    Uses Qdrant HTTP API directly.
    This avoids 'QdrantClient has no attribute search/search_points' issues caused by version mismatch.
    """

    def __init__(self, url: str = "http://localhost:6333", collection: str = "fashion200k", timeout_s: int = 60):
        self.url = url.rstrip("/")
        self.collection = collection
        self.timeout_s = timeout_s

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(f"{self.url}{path}", json=body)
            if r.status_code >= 400:
                raise RuntimeError(f"Qdrant search failed {r.status_code}: {r.text}")
            return r.json()

    def _put(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.put(f"{self.url}{path}", json=body)
            if r.status_code >= 400:
                raise RuntimeError(f"Qdrant upsert failed {r.status_code}: {r.text}")
            return r.json()

    def ensure_collection(self, vectors_config: Dict[str, Any]) -> None:
        """
        vectors_config example:
        {
          "text": {"size": 512, "distance": "Cosine"},
          "image": {"size": 512, "distance": "Cosine"}
        }
        """
        # Create or update is easiest by trying create; if exists, ignore.
        body = {"vectors": vectors_config}
        try:
            self._put(f"/collections/{self.collection}", {"vectors": vectors_config})
        except Exception:
            # Some Qdrant versions don't allow PUT /collections/{name}. If so, just assume it exists.
            pass

    def upsert_points(self, points: List[Dict[str, Any]]) -> None:
        """
        points: [{"id": <int/str>, "vector": {"text":[..], "image":[..]}, "payload": {...}}, ...]
        """
        body = {"points": points}
        self._put(f"/collections/{self.collection}/points?wait=true", body)

    def search(
        self,
        vector_name: str,
        vector: List[float],
        limit: int = 10,
        qfilter: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
    ) -> List[QdrantPoint]:
        """
        Uses named-vector search.
        """
        body: Dict[str, Any] = {
            "vector": {"name": vector_name, "vector": vector},
            "limit": limit,
            "with_payload": with_payload,
        }
        if qfilter:
            body["filter"] = qfilter

        out = self._post(f"/collections/{self.collection}/points/search", body)
        result = out.get("result") or []
        hits: List[QdrantPoint] = []
        for h in result:
            hits.append(
                QdrantPoint(
                    id=h.get("id"),
                    score=float(h.get("score", 0.0)),
                    payload=h.get("payload") or {},
                )
            )
        return hits
