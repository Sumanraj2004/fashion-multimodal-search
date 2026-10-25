import numpy as np
import pytest
from pydantic import ValidationError

from backend.app.search_api.cache import MemoryCache, make_key
from backend.app.search_api.catalog import to_product
from backend.app.search_api.embedder import l2_normalize
from backend.app.search_api.schemas import Filters, TextSearchRequest
from backend.app.search_api.service import paginate, passes_filters


def test_embedding_is_unit_length():
    v = l2_normalize(np.array([[3.0, 4.0]]))
    assert v.shape == (1, 2)
    assert np.isclose(np.linalg.norm(v), 1.0)


def test_filter_logic():
    p = {"category": "Shoes", "price": 50.0}
    assert passes_filters(p, Filters(category="shoes"))
    assert not passes_filters(p, Filters(category="Hoodies"))
    assert passes_filters(p, Filters(min_price=10, max_price=50))
    assert not passes_filters(p, Filters(max_price=49))
    assert not passes_filters({"category": "Shoes", "price": None}, Filters(min_price=1))


def test_pagination_math():
    items = list(range(25))
    assert paginate(items, 1, 10) == (list(range(10)), True)
    assert paginate(items, 3, 10) == (list(range(20, 25)), False)
    assert paginate(items, 4, 10) == ([], False)


def test_cache_key_stable_and_distinct():
    a = make_key("t", q="x", page=1)
    assert a == make_key("t", page=1, q="x")
    assert a != make_key("t", q="x", page=2)


def test_memory_cache_roundtrip_and_expiry():
    c = MemoryCache(ttl_seconds=-1)
    c.set("k", "v")
    assert c.get("k") is None
    c2 = MemoryCache(ttl_seconds=60)
    c2.set("k", "v")
    assert c2.get("k") == "v"


def test_schema_validation():
    with pytest.raises(ValidationError):
        Filters(min_price=10, max_price=5)
    with pytest.raises(ValidationError):
        TextSearchRequest(query="   ")
    assert TextSearchRequest(query="  hoodie ").query == "hoodie"


def test_to_product_handles_amazon_style_record():
    rec = {"parent_asin": "A1", "title": "T", "categories": ["Clothing", "Shoes"],
           "price": "$19.99", "images": [{"large": "http://x/l.jpg"}]}
    p = to_product(rec)
    assert p == {"id": "A1", "title": "T", "category": "Shoes", "price": 19.99, "image_url": "http://x/l.jpg"}
    assert to_product({"title": "no id"}) is None


def test_index_loads_npy_ids(tmp_path):
    import faiss
    from backend.app.search_api.index_store import VectorIndex
    idx = faiss.IndexFlatIP(4)
    idx.add(np.eye(4, dtype="float32"))
    faiss.write_index(idx, str(tmp_path / "i.faiss"))
    np.save(tmp_path / "ids.npy", np.array(["a", "b", "c", "d"]))
    vi = VectorIndex.load(str(tmp_path / "i.faiss"), str(tmp_path / "ids.npy"))
    assert vi.ids == ["a", "b", "c", "d"]
    assert vi.search(np.eye(4, dtype="float32")[2:3], 1)[0][0] == "c"
