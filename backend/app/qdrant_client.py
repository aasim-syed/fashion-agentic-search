from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

COLLECTION_NAME = "fashion200k"

class QdrantService:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)

    def create_collection(self, vector_size: int = 512):
        """
        Creates (or recreates) collection with named vectors for text + image
        """
        self.client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "text": VectorParams(size=vector_size, distance=Distance.COSINE),
                "image": VectorParams(size=vector_size, distance=Distance.COSINE),
            }
        )
        print(f"✅ Qdrant collection '{COLLECTION_NAME}' created")

    def upsert_point(self, point_id: str, text_vector, image_vector, payload: dict):
        """
        Insert or update a single product point
        """
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                {
                    "id": point_id,
                    "vector": {
                        "text": text_vector,
                        "image": image_vector
                    },
                    "payload": payload
                }
            ]
        )

    def search(self, vector_name: str, query_vector, top_k: int = 10):
        """
        vector_name: "text" or "image"
        """
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=(vector_name, query_vector),
            limit=top_k
        )

        formatted = []
        for r in results:
            formatted.append({
                "id": r.id,
                "product_id": r.payload.get("product_id"),
                "score": float(r.score)
            })

        return formatted
