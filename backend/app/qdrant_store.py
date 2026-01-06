# backend/app/qdrant_store.py
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

COLLECTION_NAME = "fashion200k"

class QdrantStore:
    def __init__(self, host: str = "localhost", port: int = 6333):
        # If versions mismatch, don't hard fail
        self.client = QdrantClient(host=host, port=port, check_compatibility=False)

    def ensure_collection(self, vector_size: int = 512):
        # named vectors: "text" and "image"
        try:
            self.client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "text": qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
                    "image": qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
                },
            )
        except Exception:
            # if recreate not supported / already exists, try create
            try:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={
                        "text": qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
                        "image": qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
                    },
                )
            except Exception:
                pass

    def upsert_points(self, points: List[qm.PointStruct]):
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)

    def search(self, namespace: str, vector: List[float], top_k: int = 10, flt: Optional[qm.Filter] = None):
        """
        Supports multiple qdrant-client versions:
        - new: query_points
        - old: search_points / search
        We always pass `vector` as plain list[float] (NOT NamedVector) to avoid fastembed query errors.
        """
        # 1) Newer API: query_points
        try:
            res = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=vector,            # plain floats
                using=namespace,         # selects named vector "text"/"image"
                limit=top_k,
                with_payload=True,
                query_filter=flt,
            )
            return res.points
        except TypeError:
            pass
        except Exception:
            # try other signatures
            pass

        # 2) Alternate signature for some versions
        try:
            res = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                using=namespace,
                limit=top_k,
                with_payload=True,
                filter=flt,
            )
            return res.points
        except TypeError:
            pass
        except Exception:
            pass

        # 3) Older API: search
        try:
            res = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=(namespace, vector),  # sometimes supports tuple
                limit=top_k,
                with_payload=True,
                query_filter=flt,
            )
            return res
        except Exception:
            pass

        # 4) Oldest: search without namespace
        res = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )
        return res
