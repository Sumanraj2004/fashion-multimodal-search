"""Search logic: retrieve candidates, filter, paginate, cache."""
from __future__ import annotations

import json
import logging
from typing import Optional

import numpy as np

from .cache import make_key
from .catalog import Catalog
from .config import Settings
from .embedder import Embedder
from .index_store import VectorIndex
from .schemas import Filters, TextSearchRequest

logger = logging.getLogger("search_api.service")


def passes_filters(product: dict, f: Filters) -> bool:
    if f.category and (product.get("category") or "").lower() != f.category.lower():
        return False
    price = product.get("price")
    if f.min_price is not None and (price is None or price < f.min_price):
        return False
    if f.max_price is not None and (price is None or price > f.max_price):
        return False
    return True


def paginate(items: list, page: int, size: int) -> tuple[list, bool]:
    start = (page - 1) * size
    return items[start : start + size], len(items) > start + size


class SearchService:
    def __init__(self, embedder: Embedder, index: VectorIndex, catalog: Catalog, cache, settings: Settings):
        self.embedder = embedder
        self.index = index
        self.catalog = catalog
        self.cache = cache
        self.settings = settings

    def candidate_count(self, top_k: int, page: int) -> int:
        # FAISS cannot filter, so we over-fetch, filter by metadata, then page.
        # Trade-off: a very strict filter may leave fewer matches than a full page
        # (even though matching products exist deeper in the index). Raise
        # CANDIDATE_MULTIPLIER / CANDIDATE_CAP to trade latency for recall.
        return min(self.settings.candidate_cap, top_k * page * self.settings.candidate_multiplier)

    def _search_vector(self, vec: np.ndarray, top_k: int, page: int, f: Filters) -> dict:
        raw = self.index.search(vec, self.candidate_count(top_k, page))
        matches = []
        for pid, score in raw:
            prod = self.catalog.get(pid)
            if prod and passes_filters(prod, f):
                matches.append({**prod, "score": score})
        results, has_more = paginate(matches, page, top_k)
        return {
            "results": results,
            "page": page,
            "top_k": top_k,
            "total_matches": len(matches),
            "has_more": has_more,
        }

    def search_text(self, req: TextSearchRequest) -> tuple[dict, bool]:
        """Returns (response_dict_without_timing, cache_hit)."""
        key = make_key("text", **req.model_dump())
        hit = self.cache.get(key)
        if hit is not None:
            logger.info("text search cache=HIT")
            return json.loads(hit), True

        emb_key = make_key("emb", q=req.query)
        raw = self.cache.get(emb_key)
        if raw is not None:
            vec = np.asarray(json.loads(raw), dtype="float32")
        else:
            vec = self.embedder.embed_text(req.query)
            self.cache.set(emb_key, json.dumps(vec.tolist()))

        resp = self._search_vector(vec, req.top_k, req.page, req)
        self.cache.set(key, json.dumps(resp))
        logger.info("text search cache=MISS")
        return resp, False

    def search_image(self, data: bytes, top_k: int, page: int, f: Filters) -> dict:
        vec = self.embedder.embed_image(data)
        return self._search_vector(vec, top_k, page, f)
