"""Product metadata lookup (loaded from Phase 1's catalog.jsonl).

`to_product` is the ONE place that maps your catalog's field names to the API's
fields. If your catalog.jsonl uses different names, edit the fallbacks here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional


def _first(rec: dict, *keys):
    for k in keys:
        v = rec.get(k)
        if v not in (None, "", []):
            return v
    return None


def _price(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"\d+(?:[.,]\d+)?", str(v).replace(",", ""))
    return float(m.group()) if m else None


def _image(rec: dict) -> Optional[str]:
    direct = _first(rec, "image_url", "image_path", "image")
    if isinstance(direct, str):
        return direct
    imgs = rec.get("images")
    if isinstance(imgs, list) and imgs:
        first = imgs[0]
        if isinstance(first, dict):
            return _first(first, "large", "hi_res", "thumb")
        if isinstance(first, str):
            return first
    if isinstance(imgs, dict):  # {"large": [...], "hi_res": [...]}
        for key in ("large", "hi_res", "thumb"):
            vals = imgs.get(key)
            if vals:
                return vals[0]
    return None


def to_product(rec: dict) -> Optional[dict]:
    pid = _first(rec, "id", "product_id", "parent_asin", "asin")
    title = _first(rec, "title", "name")
    if pid is None or title is None:
        return None
    category = _first(rec, "category", "main_category")
    if category is None and isinstance(rec.get("categories"), list) and rec["categories"]:
        category = rec["categories"][-1]
    return {
        "id": str(pid),
        "title": str(title),
        "category": str(category) if category else None,
        "price": _price(rec.get("price")),
        "image_url": _image(rec),
    }


class Catalog:
    def __init__(self, products: dict[str, dict]):
        self._products = products

    @classmethod
    def from_jsonl(cls, path: str) -> "Catalog":
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} not found. Run Phase 1 `normalize` or set CATALOG_PATH.")
        products: dict[str, dict] = {}
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                prod = to_product(json.loads(line))
                if prod:
                    products[prod["id"]] = prod
        return cls(products)

    def get(self, pid: str) -> Optional[dict]:
        return self._products.get(pid)

    def category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for product in self._products.values():
            category = product.get("category")
            if category:
                counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items()))

    def __len__(self) -> int:
        return len(self._products)
