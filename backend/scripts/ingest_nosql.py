# backend/scripts/ingest_nosql.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import os

from app.nosql_store import NoSQLStore

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLED_JSON = REPO_ROOT / "data" / "sampled_products.json"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "fashion")
MONGO_COLL = os.getenv("MONGO_COLL", "products")


def main():
    if not SAMPLED_JSON.exists():
        raise FileNotFoundError(f"Missing sampled file: {SAMPLED_JSON}")

    products: List[Dict[str, Any]] = json.loads(SAMPLED_JSON.read_text(encoding="utf-8"))

    # Expect each item contains: product_id, description, image_path, color, category, sub_category, brand
    store = NoSQLStore(mongo_uri=MONGO_URI, db_name=MONGO_DB, coll_name=MONGO_COLL)
    store.upsert_many(products)

    print(f"✅ MongoDB upserted: {len(products)} docs into {MONGO_DB}.{MONGO_COLL}")


if __name__ == "__main__":
    main()
