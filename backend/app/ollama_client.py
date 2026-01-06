import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(system: str, user: str, model: str = "mistral") -> str:
    payload = {
        "model": model,
        "system": system,
        "prompt": user,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()

    return data["response"]
