# backend/scripts/make_eval_set.py
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLED_JSON = REPO_ROOT / "data" / "sampled_products.json"
EVAL_JSON = REPO_ROOT / "data" / "eval_set.json"


def main(n: int = 100):
    products: List[Dict[str, Any]] = json.loads(SAMPLED_JSON.read_text(encoding="utf-8"))
    random.shuffle(products)

    eval_items = []
    for p in products[:n]:
        pid = p.get("product_id")
        desc = (p.get("description") or "").strip()
        if not pid or not desc:
            continue

        # Simple query generation: take last 2-4 words as a query
        words = desc.split()
        query = " ".join(words[-3:]) if len(words) >= 3 else desc

        eval_items.append({"query": query, "expected_product_id": pid})

    EVAL_JSON.write_text(json.dumps(eval_items, indent=2), encoding="utf-8")
    print(f"✅ Wrote eval set: {EVAL_JSON} ({len(eval_items)} queries)")


if __name__ == "__main__":
    main()
