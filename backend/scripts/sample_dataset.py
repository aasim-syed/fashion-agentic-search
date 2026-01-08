# backend/scripts/sample_dataset.py
from __future__ import annotations

import json
from pathlib import Path
import random

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_JSON = REPO_ROOT / "data" / "products.json"
OUT_JSON = REPO_ROOT / "data" / "sampled_products.json"


def main(n: int = 1000, seed: int = 42):
    if not DATA_JSON.exists():
        raise FileNotFoundError(f"Missing dataset file: {DATA_JSON}")

    random.seed(seed)
    products = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    if not isinstance(products, list):
        raise ValueError("products.json must be a list")

    if len(products) <= n:
        sampled = products
    else:
        sampled = random.sample(products, n)

    OUT_JSON.write_text(json.dumps(sampled, indent=2), encoding="utf-8")
    print(f"✅ Wrote {len(sampled)} products -> {OUT_JSON}")


if __name__ == "__main__":
    main()
