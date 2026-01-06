import os
import uuid
from pymongo import MongoClient
from tqdm import tqdm

from app.embedder import CLIPEmbedder
from app.qdrant_client import QdrantService

def main():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "fashion")
    coll_name = os.getenv("MONGO_COLL", "products")

    # Qdrant
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    embedder = CLIPEmbedder()
    qs = QdrantService(host=qdrant_host, port=qdrant_port)
    qs.create_collection(vector_size=512)

    client = MongoClient(mongo_url)
    col = client[db_name][coll_name]

    count = col.count_documents({})
    if count == 0:
        raise RuntimeError("Mongo has 0 products. Run ingest_mongo.py first.")

    upserted = 0
    for doc in tqdm(col.find({}), total=count):
        pid = doc["product_id"]
        desc = doc["description"]
        img_path = doc["image_path"]

        v_text = embedder.embed_text(desc).tolist()
        v_img = embedder.embed_image(img_path).tolist()

        qs.upsert_point(
            point_id=str(uuid.uuid4()),
            text_vector=v_text,
            image_vector=v_img,
            payload={"product_id": pid}
        )
        upserted += 1

    print(f"✅ indexed into Qdrant: {upserted} products")

if __name__ == "__main__":
    main()
