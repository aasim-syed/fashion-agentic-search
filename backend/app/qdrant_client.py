from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

COLLECTION_NAME = "fashion200k"

class QdrantService:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)

    def create_collection(self, vector_size: int = 512):
        # Named vectors: text + image
        self.client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "text": VectorParams(size=vector_size, distance=Distance.COSINE),
                "image": VectorParams(size=vector_size, distance=Distance.COSINE),
            }
        )
        print(f"✅ Qdrant collection '{COLLECTION_NAME}' created")

    def upsert_point(self, point_id: str, text_vector, image_vector, payload: dict):
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        "text": text_vector,
                        "image": image_vector
                    },
                    payload=payload
                )
            ]
        )

    def search(self, vector_name: str, query_vector, top_k: int = 10):
        """
        vector_name: "text" or "image"
        """
        # IMPORTANT: use search() with named vector tuple (stable API)
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=(vector_name, query_vector),
            limit=top_k,
            with_payload=True
        )

        formatted = []
        for r in results:
            formatted.append({
                "id": r.id,
                "product_id": r.payload.get("product_id") if r.payload else None,
                "score": float(r.score)
            })
        return formatted
