"""Tiny fixture index + fake embedder so tests are fast and need no Phase 1 data."""
import hashlib
import io

import faiss
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.search_api.app import Services, create_app
from backend.app.search_api.cache import MemoryCache
from backend.app.search_api.catalog import Catalog
from backend.app.search_api.config import Settings
from backend.app.search_api.embedder import l2_normalize
from backend.app.search_api.index_store import VectorIndex
from backend.app.search_api.service import SearchService

DIM = 16


def _seeded(text: bytes) -> np.ndarray:
    seed = int(hashlib.sha256(text).hexdigest()[:8], 16)
    return l2_normalize(np.random.default_rng(seed).normal(size=(1, DIM)))


class FakeEmbedder:
    dim = DIM

    def embed_text(self, text: str) -> np.ndarray:
        return _seeded(text.encode())

    def embed_image(self, data: bytes) -> np.ndarray:
        return _seeded(data)


def make_png(color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def png_bytes():
    return make_png()


@pytest.fixture
def client(png_bytes):
    emb = FakeEmbedder()
    products = {}
    vecs = []
    for i in range(30):
        pid = f"p{i}"
        products[pid] = {
            "id": pid,
            "title": f"item {i}",
            "category": "Shoes" if i % 2 == 0 else "Hoodies",
            "price": float(10 + i * 5),
            "image_url": f"http://img/{i}.jpg",
        }
        vecs.append(emb.embed_image(png_bytes) if i == 5 else emb.embed_text(f"item {i}"))
    index = faiss.IndexFlatIP(DIM)
    index.add(np.vstack(vecs).astype("float32"))
    settings = Settings(max_upload_mb=1, candidate_multiplier=5, candidate_cap=500)
    service = SearchService(emb, VectorIndex(index, list(products)), Catalog(products), MemoryCache(60), settings)
    with TestClient(create_app(Services(service, service.catalog, settings))) as c:
        yield c
