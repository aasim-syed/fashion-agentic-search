from sentence_transformers import SentenceTransformer
from PIL import Image
import numpy as np

class CLIPEmbedder:
    def __init__(self, model_name="sentence-transformers/clip-ViT-B-32"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> np.ndarray:
        v = self.model.encode([text], normalize_embeddings=True)[0]
        return v.astype("float32")

    def embed_image(self, image_path: str) -> np.ndarray:
        img = Image.open(image_path).convert("RGB")
        v = self.model.encode([img], normalize_embeddings=True)[0]
        return v.astype("float32")
