"""Swappable vector-search boundary with a FAISS cosine-similarity implementation."""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import faiss
import numpy as np


class VectorSearcher(Protocol):
    """Minimal interface that a future Qdrant adapter can implement."""

    def search(self, queries: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
        """Return cosine scores and row indexes for normalized query vectors."""


class FaissCosineIndex:
    """Exact FAISS inner-product index for L2-normalized vectors."""

    def __init__(self, index: faiss.Index) -> None:
        self.index = index

    @classmethod
    def build(cls, vectors: np.ndarray) -> "FaissCosineIndex":
        """Build an exact index and verify input normalization assumptions."""

        if vectors.ndim != 2 or vectors.shape[0] == 0:
            raise ValueError("vectors must be a non-empty two-dimensional array")
        vectors = np.ascontiguousarray(vectors.astype(np.float32, copy=False))
        norms = np.linalg.norm(vectors, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-3):
            raise ValueError("FAISS cosine index requires L2-normalized vectors")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index)

    def search(self, queries: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
        """Search for the top ``limit`` nearest catalog rows."""

        if limit < 1:
            raise ValueError("limit must be positive")
        queries = np.ascontiguousarray(queries.astype(np.float32, copy=False))
        return self.index.search(queries, limit)

    def save(self, path: Path) -> None:
        """Write an interoperable FAISS index file."""

        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path))

    @classmethod
    def load(cls, path: Path) -> "FaissCosineIndex":
        """Load a persisted FAISS index."""

        return cls(faiss.read_index(str(path)))


def build_and_save(
    vectors: np.ndarray, product_ids: Sequence[str], output_dir: Path
) -> FaissCosineIndex:
    """Build the index and persist the exact row-to-product-ID mapping."""

    if len(product_ids) != len(vectors):
        raise ValueError("product_ids and vectors must have identical lengths")
    index = FaissCosineIndex.build(vectors)
    index.save(output_dir / "catalog.faiss")
    np.save(output_dir / "index_product_ids.npy", np.asarray(product_ids, dtype="U128"))
    return index
