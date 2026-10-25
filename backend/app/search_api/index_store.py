"""FAISS index + row->product-id mapping produced by Phase 1."""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np


class VectorIndex:
    def __init__(self, index, ids: list[str]):
        if index.ntotal != len(ids):
            raise ValueError(
                f"Index has {index.ntotal} vectors but ids file has {len(ids)} entries; "
                "they must be aligned row-for-row."
            )
        self.index = index
        self.ids = [str(i) for i in ids]

    @classmethod
    def load(cls, index_path: str, ids_path: str) -> "VectorIndex":
        for p in (index_path, ids_path):
            if not Path(p).exists():
                raise FileNotFoundError(
                    f"{p} not found. Run Phase 1 (`index` stage) or set INDEX_PATH / IDS_PATH."
                )
        index = faiss.read_index(index_path)
        if ids_path.endswith(".npy"):
            try:
                arr = np.load(ids_path)
            except ValueError:  # object-dtype arrays need pickle (your own Phase 1 file)
                arr = np.load(ids_path, allow_pickle=True)
            ids = [str(x) for x in arr.tolist()]
        else:
            text = Path(ids_path).read_text(encoding="utf-8")
            if ids_path.endswith(".json"):
                ids = json.loads(text)
            else:
                ids = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return cls(index, ids)

    @property
    def size(self) -> int:
        return int(self.index.ntotal)

    def search(self, vec: np.ndarray, k: int) -> list[tuple[str, float]]:
        k = max(1, min(k, self.size))
        scores, idx = self.index.search(np.ascontiguousarray(vec, dtype="float32"), k)
        return [(self.ids[i], float(s)) for i, s in zip(idx[0], scores[0]) if i >= 0]
