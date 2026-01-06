# backend/app/retreiver.py
from typing import List, Dict, Any

from app.qdrant_store import QdrantStore

class Retriever:
    def __init__(self):
        self.qs = QdrantStore(host="localhost", port=6333)

    def search(self, namespace: str, vector: List[float], top_k: int = 10):
        return self.qs.search(namespace=namespace, vector=vector, top_k=top_k)
