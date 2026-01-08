# backend/scripts/evaluate.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_JSON = REPO_ROOT / "data" / "eval_set.json"
BASELINE_JSON = REPO_ROOT / "data" / "eval_baseline.json"

BACKEND = "http://localhost:8000"


def hit_at_k(results: List[Dict], expected_pid: str, k: int) -> int:
    top = results[:k]
    return 1 if any(str(r.get("product_id")) == str(expected_pid) for r in top) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=BACKEND)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--save-baseline", action="store_true")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()

    eval_items = json.loads(EVAL_JSON.read_text(encoding="utf-8"))

    total = 0
    h1 = h3 = h10 = 0

    for item in eval_items:
        q = item["query"]
        expected = item["expected_product_id"]

        r = requests.post(f"{args.backend}/api/chat", files={"message": (None, q)})
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []

        total += 1
        h1 += hit_at_k(results, expected, 1)
        h3 += hit_at_k(results, expected, 3)
        h10 += hit_at_k(results, expected, 10)

    metrics = {
        "total": total,
        "hit@1": h1 / max(1, total),
        "hit@3": h3 / max(1, total),
        "hit@10": h10 / max(1, total),
    }

    print("✅ metrics:", json.dumps(metrics, indent=2))

    if args.save_baseline:
        BASELINE_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"✅ saved baseline -> {BASELINE_JSON}")

    if args.compare:
        if not BASELINE_JSON.exists():
            raise FileNotFoundError("No baseline found. Run with --save-baseline first.")
        base = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))

        # Simple regression check:
        # require new metrics not worse by > 0.02 on hit@10
        if metrics["hit@10"] + 0.02 < base["hit@10"]:
            raise SystemExit(f"❌ Regression: hit@10 dropped from {base['hit@10']} to {metrics['hit@10']}")
        print("✅ Regression check passed (no significant drop).")


if __name__ == "__main__":
    main()
