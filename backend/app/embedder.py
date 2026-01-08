# backend/app/embedder.py
from __future__ import annotations
from typing import List
from io import BytesIO
from PIL import Image
from sentence_transformers import SentenceTransformer


class CLIPEmbedder:
    def __init__(self, model_name: str = "clip-ViT-B-32"):
        # If you already have a model, keep yours.
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        v = self.model.encode([text], normalize_embeddings=True)[0]
        return v.tolist() if hasattr(v, "tolist") else list(v)

    def embed_image_bytes(self, image_bytes: bytes) -> List[float]:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        v = self.model.encode([img], normalize_embeddings=True)[0]
        return v.tolist() if hasattr(v, "tolist") else list(v)
