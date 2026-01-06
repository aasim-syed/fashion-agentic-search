import json
from app.ollama_client import ollama_generate

PLANNER_SYSTEM = """You are a fashion search planner.
Return ONLY valid JSON. No markdown. No explanation.
"""

PLANNER_USER = """Given chat context and user input, produce a retrieval plan.

Input:
- message: {message}
- has_image: {has_image}
- chat_history: {chat_history}

Output JSON schema:
{{
  "intermediate_queries": ["..."],
  "weights": {{"text": 0.0-1.0, "image": 0.0-1.0}},
  "top_k": 5-30,
  "filters": {{}}
}}

Rules:
- If has_image=true and message empty → image weight high.
- If has_image=true and message like "same style but X" → keep both.
- Keep queries short and searchable.
"""

def plan(message: str, has_image: bool, chat_history=None):
    chat_history = chat_history or []

    user_prompt = PLANNER_USER.format(
        message=message,
        has_image=has_image,
        chat_history=chat_history
    )

    raw = ollama_generate(
        system=PLANNER_SYSTEM,
        user=user_prompt,
        model="mistral"
    )

    try:
        return json.loads(raw)
    except Exception as e:
        print("❌ Planner JSON parse failed. Raw output:\n", raw)
        raise e
