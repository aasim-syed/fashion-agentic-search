import os
import json
import random
from pathlib import Path
from pymongo import MongoClient

OUT_DIR = Path("benchmark")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "benchmark.json"

def keywordize(desc: str) -> str:
    # deterministic “query-like” shortening without LLM
    # keep first ~8-12 tokens
    toks = [t.strip(" ,.;:()[]{}\"'").lower() for t in desc.split()]
    toks = [t for t in toks if t]
    return " ".join(toks[:10]) if toks else desc[:60]

def main():
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "fashion")
    coll_name = os.getenv("MONGO_COLL", "products")

    BENCH_N = int(os.getenv("BENCH_N", "150"))     # total items to sample
    SEED = int(os.getenv("BENCH_SEED", "123"))

    client = MongoClient(mongo_url)
    col = client[db_name][coll_name]

    docs = list(col.find({}, {"_id": 0, "product_id": 1, "description": 1, "image_path": 1}))
    if not docs:
        raise RuntimeError("Mongo has 0 products. Run ingest_mongo.py first.")

    rnd = random.Random(SEED)
    rnd.shuffle(docs)
    docs = docs[: min(BENCH_N, len(docs))]

    bench = []
    for d in docs:
        pid = d["product_id"]
        desc = d["description"]
        img = d["image_path"]

        # TEXT-only: identity ground truth
        bench.append({
            "id": f"text_identity_{pid}",
            "type": "text",
            "query": desc,
            "expected_product_id": pid
        })

        # TEXT-only: keywordized query variant (still deterministic)
        bench.append({
            "id": f"text_keywords_{pid}",
            "type": "text",
            "query": keywordize(desc),
            "expected_product_id": pid
        })

        # IMAGE-only: identity ground truth
        bench.append({
            "id": f"image_identity_{pid}",
            "type": "image",
            "image_path": img,
            "expected_product_id": pid
        })

        # TEXT + IMAGE: deterministic instruction
        bench.append({
            "id": f"text_image_{pid}",
            "type": "text_image",
            "query": "same style similar item",
            "image_path": img,
            "expected_product_id": pid
        })

    OUT_PATH.write_text(json.dumps(bench, indent=2), encoding="utf-8")
    print(f"✅ benchmark created: {OUT_PATH.resolve()}")
    print(f"✅ total cases: {len(bench)} (from {len(docs)} products)")

if __name__ == "__main__":
    main()
