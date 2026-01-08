from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter


class Retriever:
    def __init__(self, qdrant_url: str = "http://localhost:6333", collection: str = "fashion200k"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection = collection

    def search(
        self,
        vector_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ):
        qdrant_filter = None

        if filters:
            # convert dict -> Qdrant Filter
            must = []
            for k, v in filters.items():
                if isinstance(v, list):
                    must.append({"key": k, "match": {"any": v}})
                else:
                    must.append({"key": k, "match": {"value": v}})
            qdrant_filter = Filter(must=must)

        res = self.client.search(
            collection_name=self.collection,
            query_vector=(vector_name, query_vector),
            limit=top_k,
            with_payload=True,
            query_filter=qdrant_filter,
        )

        return res
