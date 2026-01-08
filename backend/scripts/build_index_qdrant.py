# backend/scripts/build_index_qdrant.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import os

from app.embedder import CLIPEmbedder
from app.qdrant_rest import QdrantREST

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLED_JSON = REPO_ROOT / "data" / "sampled_products.json"

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "fashion200k")


def main():
    if not SAMPLED_JSON.exists():
        raise FileNotFoundError(f"Missing sampled file: {SAMPLED_JSON}. Run sample_dataset first.")

    products: List[Dict[str, Any]] = json.loads(SAMPLED_JSON.read_text(encoding="utf-8"))
    print(f"✅ Loaded {len(products)} sampled products")

    embedder = CLIPEmbedder()
    q = QdrantREST(url=QDRANT_URL, collection=COLLECTION)

    # Ensure collection has named vectors
    # (If already exists, Qdrant will keep it. Your /collections/fashion200k showed text/image already.)
    q.ensure_collection(
        vectors_config={
            "text": {"size": 512, "distance": "Cosine"},
            "image": {"size": 512, "distance": "Cosine"},
        }
    )
    print(f"✅ Qdrant collection ensured: {COLLECTION}")

    points = []
    for idx, p in enumerate(products):
        pid = p.get("product_id") or str(idx)
        desc = p.get("description") or ""
        img_path = p.get("image_path") or p.get("image_abs_path")

        v_text = embedder.embed_text(desc)

        # image vector optional if file exists
        v_img = None
        if img_path:
            ip = Path(img_path)
            if ip.exists():
                v_img = embedder.embed_image_bytes(ip.read_bytes())

        vectors = {"text": v_text, "image": v_img if v_img is not None else [0.0] * 512}

        payload = {
            "product_id": pid,
            "description": desc,
            "image_path": img_path,
            "image_abs_path": img_path,
            "brand": p.get("brand"),
            "category": p.get("category"),
            "sub_category": p.get("sub_category"),
            "color": p.get("color"),
        }

        points.append({"id": idx, "vector": vectors, "payload": payload})

        if len(points) >= 64:
            q.upsert_points(points)
            points = []

    if points:
        q.upsert_points(points)

    print("✅ Qdrant indexing complete.")


if __name__ == "__main__":
    main()
