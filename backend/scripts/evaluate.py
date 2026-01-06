import os
import json
from pathlib import Path
from typing import List, Dict, Any
from app.embedder import CLIPEmbedder
from app.qdrant_client import QdrantService

BENCH_PATH = Path("benchmark") / "benchmark.json"
OUT_METRICS = Path("benchmark") / "metrics.json"
BASELINE = Path("benchmark") / "baseline_metrics.json"
FAILURES = Path("benchmark") / "failures.json"

def recall_at_k(ranks: List[int], k: int) -> float:
    # ranks: 1-based rank position of expected item, or 0 if not found
    hits = sum(1 for r in ranks if 1 <= r <= k)
    return hits / len(ranks) if ranks else 0.0

def mrr_at_k(ranks: List[int], k: int) -> float:
    # reciprocal rank if <=k else 0
    rr = 0.0
    for r in ranks:
        if 1 <= r <= k:
            rr += 1.0 / r
    return rr / len(ranks) if ranks else 0.0

def rank_of_expected(results: List[Dict[str, Any]], expected_pid: str) -> int:
    # results are ordered by score desc already
    for i, r in enumerate(results, start=1):
        if r.get("product_id") == expected_pid:
            return i
    return 0

def search_text(qs: QdrantService, vec: List[float], top_k: int) -> List[Dict[str, Any]]:
    return qs.search("text", vec, top_k)

def search_image(qs: QdrantService, vec: List[float], top_k: int) -> List[Dict[str, Any]]:
    return qs.search("image", vec, top_k)

def fuse(text_hits, image_hits, w_text=0.6, w_img=0.4):
    # merge by product_id with weighted sum
    t = {h["product_id"]: h["score"] for h in text_hits}
    i = {h["product_id"]: h["score"] for h in image_hits}
    all_pids = set(t) | set(i)
    fused = []
    for pid in all_pids:
        fused.append({
            "product_id": pid,
            "score": w_text * t.get(pid, 0.0) + w_img * i.get(pid, 0.0)
        })
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused

def main():
    if not BENCH_PATH.exists():
        raise FileNotFoundError(f"Missing benchmark: {BENCH_PATH}. Run make_benchmark.py first.")

    top_k = int(os.getenv("EVAL_TOPK", "10"))
    w_text = float(os.getenv("EVAL_W_TEXT", "0.6"))
    w_img = float(os.getenv("EVAL_W_IMG", "0.4"))

    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    embedder = CLIPEmbedder()
    qs = QdrantService(host=qdrant_host, port=qdrant_port)

    bench = json.loads(BENCH_PATH.read_text(encoding="utf-8"))

    ranks = []
    failures = []

    for ex in bench:
        typ = ex["type"]
        expected = ex["expected_product_id"]

        if typ == "text":
            qv = embedder.embed_text(ex["query"]).tolist()
            res = search_text(qs, qv, top_k=top_k)

        elif typ == "image":
            qv = embedder.embed_image(ex["image_path"]).tolist()
            res = search_image(qs, qv, top_k=top_k)

        elif typ == "text_image":
            qv_t = embedder.embed_text(ex["query"]).tolist()
            qv_i = embedder.embed_image(ex["image_path"]).tolist()
            text_hits = search_text(qs, qv_t, top_k=top_k)
            img_hits  = search_image(qs, qv_i, top_k=top_k)
            res = fuse(text_hits, img_hits, w_text=w_text, w_img=w_img)[:top_k]

        else:
            continue

        r = rank_of_expected(res, expected)
        ranks.append(r)

        if r == 0:
            failures.append({
                "id": ex.get("id"),
                "type": typ,
                "expected_product_id": expected,
                "query": ex.get("query", ""),
                "image_path": ex.get("image_path", ""),
                "top_results": res[:5]
            })

    metrics = {
        "count": len(ranks),
        "top_k": top_k,
        "weights": {"text": w_text, "image": w_img},
        "recall@1": recall_at_k(ranks, 1),
        "recall@5": recall_at_k(ranks, 5),
        "recall@10": recall_at_k(ranks, 10),
        "mrr@10": mrr_at_k(ranks, 10),
        "failures": len(failures),
    }

    OUT_METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    FAILURES.write_text(json.dumps(failures, indent=2), encoding="utf-8")

    print("✅ Evaluation complete")
    print(json.dumps(metrics, indent=2))

    # Optional regression check
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        # Fail if recall@5 drops by more than 0.05 (tune as you like)
        allowed_drop = float(os.getenv("REGRESSION_ALLOWED_DROP", "0.05"))
        if metrics["recall@5"] < base.get("recall@5", 0.0) - allowed_drop:
            raise SystemExit(
                f"❌ Regression detected: recall@5 {metrics['recall@5']:.3f} "
                f"< baseline {base.get('recall@5',0.0):.3f} - {allowed_drop}"
            )
        print("✅ No regression vs baseline")

if __name__ == "__main__":
    main()
