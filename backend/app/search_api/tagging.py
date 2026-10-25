"""Zero-shot category tagging with CLIP.

Your catalog's category is the same generic label ("AMAZON FASHION") for every
product, so category filters can't separate socks from hoodies. This assigns a
real category to each product by comparing its stored vector with CLIP text
embeddings of a fixed label list (zero-shot classification). It runs once at
startup, in well under a second for a few thousand products.

It is approximate: spot-check it (see the startup log + the README steps).
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger("search_api.tagging")

# category name shown in the API -> phrase used for the CLIP text prompt
CATEGORY_PROMPTS = {
    "T-Shirts": "a t-shirt",
    "Hoodies & Sweatshirts": "a hoodie or sweatshirt",
    "Sweaters": "a knit sweater",
    "Jackets & Coats": "a jacket or coat",
    "Dresses": "a dress",
    "Jeans & Pants": "jeans or trousers",
    "Shorts": "shorts",
    "Skirts": "a skirt",
    "Underwear & Lingerie": "underwear or lingerie",
    "Socks": "socks",
    "Sleepwear": "pajamas or sleepwear",
    "Activewear": "activewear or leggings",
    "Swimwear": "swimwear",
    "Shoes": "shoes",
    "Boots": "boots",
    "Sandals & Slippers": "sandals or slippers",
    "Hats & Caps": "a hat or cap",
    "Bags & Backpacks": "a bag or backpack",
    "Watches": "a wrist watch",
    "Jewelry": "jewelry",
    "Scarves & Gloves": "a scarf or gloves",
    "Belts & Accessories": "a belt or fashion accessory",
    "Sunglasses": "sunglasses",
}

GENERIC_CATEGORIES = {"", "amazon fashion", "clothing, shoes & jewelry", "all"}


def assign_categories(index, embedder, catalog, only_generic: bool = True) -> dict[str, int]:
    """Set `category` on catalog products in place. Returns {category: count}."""
    names = list(CATEGORY_PROMPTS)
    text = np.vstack(
        [embedder.embed_text(f"a product photo of {CATEGORY_PROMPTS[n]}") for n in names]
    ).astype("float32")
    try:
        vecs = index.index.reconstruct_n(0, index.size)
    except Exception as exc:  # e.g. compressed index types can't reconstruct
        logger.warning("Zero-shot tagging skipped (cannot read vectors from index): %s", exc)
        return {}

    best = (vecs @ text.T).argmax(axis=1)
    counts: dict[str, int] = {}
    for pid, b in zip(index.ids, best):
        prod = catalog.get(pid)
        if prod is None:
            continue
        current = (prod.get("category") or "").strip().lower()
        if only_generic and current not in GENERIC_CATEGORIES:
            continue
        prod["category"] = names[int(b)]
        counts[names[int(b)]] = counts.get(names[int(b)], 0) + 1
    logger.info("Zero-shot categories assigned: %s", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    return counts
