import os
import json
from pathlib import Path
from pymongo import MongoClient, ASCENDING

IN_PATH = Path("data") / "sampled_products.json"

def main():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "fashion")
    coll_name = os.getenv("MONGO_COLL", "products")

    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing sampled file: {IN_PATH}. Run sample_dataset first.")

    items = json.loads(IN_PATH.read_text(encoding="utf-8"))

    client = MongoClient(mongo_url)
    col = client[db_name][coll_name]

    # idempotent: unique index on product_id
    col.create_index([("product_id", ASCENDING)], unique=True)

    inserted = 0
    updated = 0
    for it in items:
        res = col.update_one(
            {"product_id": it["product_id"]},
            {"$set": it},
            upsert=True
        )
        if res.upserted_id is not None:
            inserted += 1
        else:
            updated += 1

    print(f"✅ Mongo ingest complete. inserted={inserted} updated={updated}")
    print(f"📚 DB: {db_name}, Collection: {coll_name}")

if __name__ == "__main__":
    main()
