# backend/app/main.py
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.planner import plan
from app.embedder import CLIPEmbedder as Embedder
from app.retreiver import Retriever
from app.nosql_store import NoSQLStore
from app.responder import build_assistant_message

app = FastAPI(title="Fashion Agentic Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = (REPO_ROOT / "data").resolve()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "fashion200k")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "fashion")
MONGO_COLL = os.getenv("MONGO_COLL", "products")
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "fashion200k"

embedder = Embedder()
retriever = Retriever(qdrant_url=QDRANT_URL, collection=QDRANT_COLLECTION)
nosql = NoSQLStore(mongo_uri=MONGO_URI, db_name=MONGO_DB, coll_name=MONGO_COLL)


def _extract_json_from_llm(raw: str) -> Dict[str, Any]:
    if not raw:
        raise ValueError("Empty planner output")
    s = raw.strip()
    if "```" in s:
        parts = s.split("```")
        if len(parts) >= 3:
            s = parts[1].strip()
            if s.lower().startswith("json"):
                s = s[4:].strip()
    if not s.lstrip().startswith("{"):
        i, j = s.find("{"), s.rfind("}")
        if i == -1 or j == -1 or j <= i:
            raise ValueError("Planner output not JSON")
        s = s[i : j + 1]
    return json.loads(s)


def _normalize_plan(p: Any) -> Dict[str, Any]:
    if isinstance(p, str):
        p = _extract_json_from_llm(p)
    if not isinstance(p, dict):
        raise ValueError("Plan must be dict")

    inter = p.get("intermediate_queries") or []
    norm_inter: List[Dict[str, Any]] = []
    for x in inter:
        if isinstance(x, str):
            norm_inter.append({"query": x, "weight": 1.0})
        elif isinstance(x, dict):
            q = x.get("query")
            if isinstance(q, str):
                w = x.get("weight", 1.0)
                try:
                    w = float(w)
                except Exception:
                    w = 1.0
                norm_inter.append({"query": q, "weight": w})

    if not norm_inter:
        norm_inter = [{"query": "", "weight": 1.0}]

    weights = p.get("weights") or {}
    if not isinstance(weights, dict):
        weights = {}
    try:
        w_text = float(weights.get("text", 1.0))
    except Exception:
        w_text = 1.0
    try:
        w_img = float(weights.get("image", 0.0))
    except Exception:
        w_img = 0.0

    try:
        top_k = int(p.get("top_k", 10))
    except Exception:
        top_k = 10
    top_k = max(1, min(50, top_k))

    filters = p.get("filters") or {}
    if not isinstance(filters, dict):
        filters = {}

    return {"intermediate_queries": norm_inter, "weights": {"text": w_text, "image": w_img}, "top_k": top_k, "filters": filters}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/image")
def get_image(path: str = Query(...)):
    raw = path.strip().strip('"').strip("'")
    raw = raw.replace("/", os.sep)
    p = Path(raw)

    if not p.is_absolute():
        p = DATA_ROOT / p

    try:
        p_resolved = p.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        p_resolved.relative_to(DATA_ROOT)
    except Exception:
        raise HTTPException(status_code=404, detail="Not found")

    if not p_resolved.exists() or not p_resolved.is_file():
        raise HTTPException(status_code=404, detail=f"File missing: {p_resolved}")

    return FileResponse(str(p_resolved))


@app.post("/api/chat")
async def chat(message: str = Form(""), image: Optional[UploadFile] = File(None)):
    msg = (message or "").strip()
    has_image = image is not None

    if not msg and not has_image:
        raise HTTPException(status_code=400, detail="Provide message or image")

    raw_plan = plan(message=msg, has_image=has_image, chat_history=[])
    try:
        p = _normalize_plan(raw_plan)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Planner parse failed: {e}", "raw_plan": str(raw_plan)})

    best = max(p["intermediate_queries"], key=lambda x: float(x.get("weight", 1.0)) or 0.0)
    query_used = (best.get("query") or "").strip() or msg
    top_k = int(p["top_k"])
    filters = p.get("filters") or {}

    # text vector always if message present
    text_hits = []
    image_hits = []

    try:
        if query_used:
            v_text = embedder.embed_text(query_used)
            text_hits = retriever.search("text", v_text, top_k=top_k, filters=filters)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Text search failed: {e}", "query_used": query_used, "plan": p})

    try:
        if has_image:
            img_bytes = await image.read()
            v_img = embedder.embed_image_bytes(img_bytes)
            image_hits = retriever.search("image", v_img, top_k=top_k, filters=filters)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Image search failed: {e}", "query_used": query_used, "plan": p})

    w_text = float(p["weights"].get("text", 1.0))
    w_img = float(p["weights"].get("image", 0.0))

    if has_image and w_img > 0 and (text_hits or image_hits):
        fused = retriever.fuse(text_hits, image_hits, w_text=w_text, w_image=w_img, top_k=top_k)
        hits = fused
    else:
        hits = text_hits if text_hits else image_hits

    # Build results from Qdrant payload + NoSQL join
    product_ids = []
    for h in hits:
        pid = h.payload.get("product_id") or str(h.id)
        product_ids.append(pid)

    meta = nosql.get_many(product_ids)  # ✅ NoSQL join

    results = []
    for h in hits:
        pid = h.payload.get("product_id") or str(h.id)
        m = meta.get(pid, {})

        # ✅ Prefer NoSQL values, fallback to Qdrant payload
        desc = m.get("description") or h.payload.get("description")
        imgp = m.get("image_path") or h.payload.get("image_path") or h.payload.get("image_abs_path")

        results.append(
            {
                "product_id": pid,
                "score": float(h.score),
                "description": desc,
                "image_path": imgp,
                "brand": m.get("brand") or h.payload.get("brand"),
                "category": m.get("category") or h.payload.get("category"),
                "sub_category": m.get("sub_category") or h.payload.get("sub_category"),
                "color": m.get("color") or h.payload.get("color"),
            }
        )

    assistant_message = build_assistant_message(query_used, p, results)

    return {"plan": p, "query_used": query_used, "assistant_message": assistant_message, "results": results}
