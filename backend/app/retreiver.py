# backend/app/retriever.py
from qdrant_client import QdrantClient
from collections import defaultdict

COLLECTION = "fashion200k"

class Retriever:
    def __init__(self):
        self.qc = QdrantClient(host="localhost", port=6333)

    def search(self, vector_name: str, query_vec, top_k=12):
        res = self.qc.search(
            collection_name=COLLECTION,
            query_vector=(vector_name, query_vec.tolist()),
            limit=top_k
        )
        return [{"product_id": r.payload["product_id"], "score": float(r.score)} for r in res]

    def fuse(self, text_hits, image_hits, w_text=0.6, w_img=0.4):
        scores = defaultdict(float)
        seen = set()

        text_map = {h["product_id"]: h["score"] for h in text_hits}
        img_map  = {h["product_id"]: h["score"] for h in image_hits}

        all_pids = set(text_map.keys()) | set(img_map.keys())
        for pid in all_pids:
            st = text_map.get(pid, 0.0)
            si = img_map.get(pid, 0.0)
            scores[pid] = w_text * st + w_img * si
            seen.add(pid)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{"product_id": pid, "score": sc} for pid, sc in ranked]
