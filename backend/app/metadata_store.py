# backend/app/metadata_store.py
from __future__ import annotations
from typing import Any, Dict, Optional
from tinydb import TinyDB, Query

class MetadataStore:
    def __init__(self, path: str = "data/metadata_db.json"):
        self.db = TinyDB(path)
        self.q = Query()

    def upsert(self, product_id: str, doc: Dict[str, Any]) -> None:
        self.db.upsert({"product_id": product_id, **doc}, self.q.product_id == product_id)

    def get(self, product_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get(self.q.product_id == product_id)
