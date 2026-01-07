# backend/app/ollama_client.py
import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

def ollama_generate(system: str, user: str, model: str = "llama3.2:1b", timeout_s: int = 600) -> str:
    """
    Uses Ollama /api/generate (non-stream) and returns plain text response.
    """
    payload = {
        "model": model,
        "prompt": f"{system}\n\nUSER:\n{user}\n",
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }
    # (connect timeout, read timeout)
    r = requests.post(OLLAMA_URL, json=payload, timeout=(10, timeout_s))
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()
