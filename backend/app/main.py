# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from pymongo import MongoClient
import os, uuid
from app.embedder import CLIPEmbedder
from app.retreiver import Retriever
from app.responder import build_answer
from app.planner import plan

app = FastAPI()
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

mc = MongoClient("mongodb://localhost:27017")
products = mc["fashion"]["products"]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)



# Dummy LLM wrapper placeholder
class DummyLLM:
    def generate(self, system, user):
        # fallback if you don't plug a real LLM yet
        return """{
          "intermediate_queries": ["red dress", "similar style red"],
          "weights": {"text": 0.6, "image": 0.4},
          "top_k": 12,
          "filters": {}
        }"""

llm = DummyLLM()

@app.post("/api/chat")
async def chat(message: str = Form(""), image: UploadFile = File(None)):
    has_image = image is not None

    # 1) planner
    p = plan( message=message, has_image=has_image, chat_history=[])

    # 2) retrieval
    top_k = int(p.get("top_k", 12))
    w_text = float(p["weights"].get("text", 0.6))
    w_img  = float(p["weights"].get("image", 0.4))

    text_hits, img_hits = [], []
    if message.strip():
        q_text = embedder.embed_text(p["intermediate_queries"][0])
        text_hits = retriever.search("text", q_text, top_k=top_k)

    img_path = None
    if has_image:
        fn = f"{uuid.uuid4()}_{image.filename}"
        img_path = os.path.join(UPLOAD_DIR, fn)
        with open(img_path, "wb") as f:
            f.write(await image.read())
        q_img = embedder.embed_image(img_path)
        img_hits = retriever.search("image", q_img, top_k=top_k)

    fused = retriever.fuse(text_hits, img_hits, w_text=w_text, w_img=w_img)[:top_k]

    # 3) hydrate results from Mongo
    result_cards = []
    for r in fused:
        doc = products.find_one({"product_id": r["product_id"]})
        if not doc: 
            continue
        result_cards.append({
            "product_id": doc["product_id"],
            "description": doc["description"],
            "image": doc["image_path"],
            "score": r["score"]
        })

    assistant_message = build_answer(message, p, result_cards)

    return {
        "assistant_message": assistant_message,
        "results": result_cards,
        "debug": {
            "intermediate_queries": p.get("intermediate_queries", []),
            "weights": p.get("weights", {}),
            "top_k": top_k
        }
    }
