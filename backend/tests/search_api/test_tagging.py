import faiss
import numpy as np

from backend.app.search_api.catalog import Catalog
from backend.app.search_api.embedder import l2_normalize
from backend.app.search_api.index_store import VectorIndex
from backend.app.search_api.tagging import CATEGORY_PROMPTS, assign_categories


class PromptEmbedder:
    """Maps each category prompt to its own one-hot-ish direction."""
    dim = len(CATEGORY_PROMPTS)

    def embed_text(self, text: str) -> np.ndarray:
        v = np.zeros((1, self.dim), dtype="float32")
        for i, phrase in enumerate(CATEGORY_PROMPTS.values()):
            if phrase in text:
                v[0, i] = 1.0
        return l2_normalize(v)


def _setup(categories):
    names = list(CATEGORY_PROMPTS)
    emb = PromptEmbedder()
    # product 0 looks like "socks", product 1 like "dresses"
    vecs = np.vstack([emb.embed_text(f"a product photo of {CATEGORY_PROMPTS['Socks']}"),
                      emb.embed_text(f"a product photo of {CATEGORY_PROMPTS['Dresses']}")])
    idx = faiss.IndexFlatIP(emb.dim)
    idx.add(vecs)
    products = {
        "a": {"id": "a", "title": "x", "category": categories[0], "price": None, "image_url": None},
        "b": {"id": "b", "title": "y", "category": categories[1], "price": None, "image_url": None},
    }
    return emb, VectorIndex(idx, ["a", "b"]), Catalog(products)


def test_generic_categories_are_replaced():
    emb, index, catalog = _setup(["AMAZON FASHION", None])
    counts = assign_categories(index, emb, catalog)
    assert catalog.get("a")["category"] == "Socks"
    assert catalog.get("b")["category"] == "Dresses"
    assert counts == {"Socks": 1, "Dresses": 1}


def test_real_categories_are_kept():
    emb, index, catalog = _setup(["Footwear", "AMAZON FASHION"])
    assign_categories(index, emb, catalog)
    assert catalog.get("a")["category"] == "Footwear"
    assert catalog.get("b")["category"] == "Dresses"
