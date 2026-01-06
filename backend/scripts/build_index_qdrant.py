# backend/scripts/build_index_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from pymongo import MongoClient
from app.embedder import CLIPEmbedder
from tqdm import tqdm
import uuid

COLLECTION = "fashion200k"

def main():
    qc = QdrantClient(host="localhost", port=6333)
    embedder = CLIPEmbedder()

    # Create collection with named vectors
    qc.recreate_collection(
        collection_name=COLLECTION,
        vectors_config={
            "text": VectorParams(size=512, distance=Distance.COSINE),
            "image": VectorParams(size=512, distance=Distance.COSINE),
        }
    )

    mc = MongoClient("mongodb://localhost:27017")
    col = mc["fashion"]["products"]

    points = []
    for doc in tqdm(col.find({})):
        pid = doc["product_id"]
        desc = doc["description"]
        img_path = doc["image_path"]

        v_text = embedder.embed_text(desc)
        v_img  = embedder.embed_image(img_path)

        points.append({
            "id": str(uuid.uuid4()),
            "payload": {"product_id": pid},
            "vector": {"text": v_text.tolist(), "image": v_img.tolist()}
        })

    qc.upsert(collection_name=COLLECTION, points=points)
    print("✅ Indexed into Qdrant:", len(points))

if __name__ == "__main__":
    main()
