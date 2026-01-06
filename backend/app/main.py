# backend/app/main.py
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.planner import plan
from app.embedder import CLIPEmbedder
from app.retreiver import Retriever  # keep your current spelling if that's in repo

app = FastAPI()

# ✅ CORS for React dev server
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

embedder = CLIPEmbedder()
retriever = Retriever()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    image: UploadFile | None = File(None),
):
    has_image = image is not None

    p = plan(message=message, has_image=has_image, chat_history=[])

    # hard safety
    if isinstance(p, str) or not isinstance(p, dict):
        p = {
            "intermediate_queries": [{"query": message, "weight": 1.0}],
            "weights": {"text": 1.0, "image": 0.0},
            "top_k": 10,
            "filters": {},
        }

    top_k = int(p.get("top_k", 10))
    iq = p.get("intermediate_queries", [{"query": message, "weight": 1.0}])

    # take first query (good enough for MVP)
    q_text = iq[0].get("query", message)
    q_vec = embedder.embed_text(q_text)

    # Qdrant search on "text" vector namespace
    hits = retriever.search("text", q_vec, top_k=top_k)

    # normalize output
    results = []
    for h in hits:
        payload = getattr(h, "payload", None) or {}
        score = getattr(h, "score", None)
        results.append({
            "score": score,
            "product_id": payload.get("product_id"),
            "description": payload.get("description"),
            "image_path": payload.get("image_path"),
        })

    return {
        "plan": p,
        "query_used": q_text,
        "results": results,
    }
