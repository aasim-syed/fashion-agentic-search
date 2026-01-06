# backend/app/embedder.py
from typing import List
from sentence_transformers import SentenceTransformer

class CLIPEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/clip-ViT-B-32"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        if not isinstance(text, str):
            text = str(text)
        v = self.model.encode([text], normalize_embeddings=True)[0]
        return v.tolist()
