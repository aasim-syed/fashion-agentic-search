# backend/app/planner.py
import json

PLANNER_SYSTEM = """You are a fashion search planner.
Return ONLY valid JSON. No extra text.
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
  "filters": {{"category": "...optional..."}}
}}

Rules:
- If has_image=true and message is empty => image weight high.
- If has_image=true and message asks "same but X" => keep both.
- Keep queries short, searchable.
"""
