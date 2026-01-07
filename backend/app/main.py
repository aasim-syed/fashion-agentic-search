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
from app.retreiver import Retriever  # keep typo filename retreiver.py


app = FastAPI(title="Fashion Agentic Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# repo_root = .../fashion-agentic-search
REPO_ROOT = Path(__file__).resolve().parents[2]

# ✅ Set this to the REAL folder that contains women/men/
DATA_ROOT = (REPO_ROOT / "data").resolve()
# If your images are under benchmark/data, use:
# DATA_ROOT = (REPO_ROOT / "benchmark" / "data").resolve()

embedder = Embedder()
retriever = Retriever()


def _extract_json_from_llm(raw: str) -> Dict[str, Any]:
    if not raw:
        raise ValueError("Empty planner output")

    s = raw.strip()

    # Remove ``` fences
    if "```" in s:
        parts = s.split("```")
        if len(parts) >= 3:
            s = parts[1].strip()
            if s.lower().startswith("json"):
                s = s[4:].strip()

    # Extract first JSON object
    if not s.lstrip().startswith("{"):
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Planner output not JSON:\n{s}")
        s = s[start : end + 1]

    return json.loads(s)


def _normalize_plan(p: Any) -> Dict[str, Any]:
    if isinstance(p, str):
        p = _extract_json_from_llm(p)
    if not isinstance(p, dict):
        raise ValueError("Plan must be a dict")

    inter = p.get("intermediate_queries") or []
    norm_inter: List[Dict[str, Any]] = []

    for x in inter:
        if isinstance(x, str):
            norm_inter.append({"query": x, "weight": 1.0})
        elif isinstance(x, dict):
            q = x.get("query")
            if not isinstance(q, str):
                continue
            w = x.get("weight", 1.0)
            try:
                w = float(w)
            except Exception:
                w = 1.0
            norm_inter.append({"query": q, "weight": w})

    if not norm_inter:
        norm_inter = [{"query": "", "weight": 1.0}]

    weights = p.get("weights") or {"text": 1.0, "image": 0.0}
    if not isinstance(weights, dict):
        weights = {"text": 1.0, "image": 0.0}

    try:
        w_text = float(weights.get("text", 1.0))
    except Exception:
        w_text = 1.0
    try:
        w_img = float(weights.get("image", 0.0))
    except Exception:
        w_img = 0.0

    top_k = p.get("top_k", 20)
    try:
        top_k = int(top_k)
    except Exception:
        top_k = 20

    filters = p.get("filters") or {}
    if not isinstance(filters, dict):
        filters = {}

    return {
        "intermediate_queries": norm_inter,
        "weights": {"text": w_text, "image": w_img},
        "top_k": top_k,
        "filters": filters,
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/image")
def get_image(path: str = Query(..., description="Relative under DATA_ROOT or absolute inside DATA_ROOT")):
    raw = (path or "").strip().strip('"').strip("'")

    # normalize slashes
    raw = raw.replace("/", os.sep)

    p = Path(raw)

    # relative -> under DATA_ROOT
    if not p.is_absolute():
        p = DATA_ROOT / p

    try:
        p_resolved = p.resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    # allow only under DATA_ROOT
    try:
        p_resolved.relative_to(DATA_ROOT)
    except Exception:
        raise HTTPException(status_code=404, detail="Not found")

    if not p_resolved.exists() or not p_resolved.is_file():
        raise HTTPException(status_code=404, detail=f"File missing: {p_resolved}")

    return FileResponse(str(p_resolved))


@app.post("/api/chat")
async def chat(
    message: str = Form(""),
    image: Optional[UploadFile] = File(None),
):
    msg = (message or "").strip()
    has_image = image is not None

    if not msg and not has_image:
        raise HTTPException(status_code=400, detail="Provide message or image")

    # 1) Planner
    raw_plan = plan(message=msg, has_image=has_image, chat_history=[])
    try:
        p = _normalize_plan(raw_plan)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Planner parse failed: {str(e)}", "raw_plan": str(raw_plan)},
        )

    # 2) Best query
    best = max(p["intermediate_queries"], key=lambda x: float(x.get("weight", 1.0)) or 0.0)
    query_used = (best.get("query") or "").strip() or msg
    top_k = int(p.get("top_k", 20))
    filters = p.get("filters", {})

    # 3) Embed + Search
    try:
        q_text_vec = embedder.embed_text(query_used)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Embed failed: {str(e)}", "query_used": query_used, "plan": p},
        )

    try:
        # ✅ FIX: use q_text_vec (not q_text)
        text_hits = retriever.search("text", q_text_vec, top_k=top_k, filters=filters)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Search failed: {str(e)}", "query_used": query_used, "plan": p},
        )

    # 4) Normalize hits
    hits = retriever.search("text", q_text_vec, top_k=top_k, filters=p.get("filters"))

    results = []
    for h in hits:
        payload = (h.get("payload") or {})
        results.append({
            "product_id": payload.get("product_id") or str(h.get("id")),
            "score": float(h.get("score", 0.0)),
            "description": payload.get("description"),
            "image_path": payload.get("image_path") or payload.get("image_abs_path"),
        })
    return {"plan": p, "query_used": query_used, "results": results}
