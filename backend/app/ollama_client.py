# backend/app/ollama_client.py
from __future__ import annotations

import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/generate"


def ollama_generate(system: str, user: str, model: str = "llama3.2:1b", timeout_s: int = 600) -> str:
    payload = {
        "model": model,
        "prompt": user,
        "system": system,
        "stream": False,
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")
