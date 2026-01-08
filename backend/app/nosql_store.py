# backend/app/nosql_store.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pymongo import MongoClient, ASCENDING


class NoSQLStore:
    """
    MongoDB store for metadata (separate from vector DB).
    Collection: products (keyed by product_id)
    """

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "fashion", coll_name: str = "products"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.coll = self.db[coll_name]
        self.coll.create_index([("product_id", ASCENDING)], unique=True)

    def upsert_many(self, docs: List[Dict[str, Any]]) -> None:
        if not docs:
            return
        ops = []
        from pymongo import UpdateOne

        for d in docs:
            pid = d.get("product_id")
            if not pid:
                continue
            ops.append(UpdateOne({"product_id": pid}, {"$set": d}, upsert=True))
        if ops:
            self.coll.bulk_write(ops, ordered=False)

    def get_many(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not product_ids:
            return {}
        cur = self.coll.find({"product_id": {"$in": product_ids}})
        out: Dict[str, Dict[str, Any]] = {}
        for d in cur:
            d.pop("_id", None)
            out[d["product_id"]] = d
        return out
