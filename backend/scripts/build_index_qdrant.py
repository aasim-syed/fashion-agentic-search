# backend/scripts/build_index_qdrant.py
import json
import os
from typing import Any, Dict, List, Optional

from qdrant_client.http import models as qm

from app.embedder import CLIPEmbedder
from app.qdrant_store import QdrantStore, COLLECTION_NAME


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLED_JSON = os.path.join(ROOT, "data", "sampled_products.json")

# If your images live somewhere else, update this.
# Many fashion200k dumps store images inside data/fashion200k/
DEFAULT_IMG_ROOT = os.path.join(ROOT, "data")


def _safe_str(x) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, str):
        return x
    return str(x)


def load_products(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing sampled file: {path}. Run sample_dataset first.")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "products" in data:
        data = data["products"]

    if not isinstance(data, list):
        raise RuntimeError(f"sampled_products.json must be a list (or dict with 'products'). Got {type(data)}")
    return data


def resolve_image_path(p: Dict[str, Any]) -> Optional[str]:
    """
    Returns a local filesystem path if possible.
    Your dataset might store image like:
      - "image_path": "fashion200k/women/....jpg"
      - OR absolute path
    We'll normalize to an absolute path if relative.
    """
    img = p.get("image_path") or p.get("image") or p.get("img_path")
    img = _safe_str(img)
    if not img:
        return None

    # If it's already absolute, keep it
    if os.path.isabs(img):
        return img

    # Otherwise join with DEFAULT_IMG_ROOT
    abs_path = os.path.join(DEFAULT_IMG_ROOT, img)
    return abs_path


def main():
    print(f"📦 Reading products from: {SAMPLED_JSON}")
    products = load_products(SAMPLED_JSON)
    print(f"✅ Loaded {len(products)} sampled products")

    embedder = CLIPEmbedder()  # text embeddings (and can be extended later)
    qs = QdrantStore(host="localhost", port=6333)

    # text embedding dim for clip-ViT-B-32 is 512
    qs.ensure_collection(vector_size=512)
    print(f"✅ Qdrant collection ensured: {COLLECTION_NAME}")

    points: List[qm.PointStruct] = []

    for idx, p in enumerate(products):
        product_id = _safe_str(p.get("product_id") or p.get("id") or p.get("pid") or idx)
        desc = _safe_str(p.get("description") or p.get("caption") or p.get("title") or "")

        # IMPORTANT: keep a usable image_path for UI
        img_abs = resolve_image_path(p)
        img_rel = _safe_str(p.get("image_path"))  # keep original too if you want

        # create text embedding
        vec_text = embedder.embed_text(desc if desc else product_id)

        payload = {
            "product_id": product_id,
            "description": desc,
            # store both raw + resolved absolute for debugging
            "image_path": img_rel,
            "image_abs_path": img_abs,
            # optional metadata if exists:
            "category": p.get("category"),
            "sub_category": p.get("sub_category"),
            "color": p.get("color"),
            "brand": p.get("brand"),
        }

        # named vector format: vectors={"text":[...], "image":[...]}
        # For now only text (image can be added later)
        point = qm.PointStruct(
            id=idx,
            vector={"text": vec_text},
            payload=payload,
        )
        points.append(point)

        if (idx + 1) % 200 == 0:
            qs.upsert_points(points)
            print(f"⬆️ Upserted {idx+1} points...")
            points = []

    if points:
        qs.upsert_points(points)
        print(f"⬆️ Upserted final batch. Total={len(products)}")

    print("🎉 Done. Now /api/chat results should include description + image_path.")


if __name__ == "__main__":
    main()
