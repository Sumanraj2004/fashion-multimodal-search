import numpy as np

from pipeline.vector_index import FaissCosineIndex


def test_faiss_index_returns_nearest_normalized_vector() -> None:
    index = FaissCosineIndex.build(np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))

    scores, rows = index.search(np.array([[0.9, 0.1]], dtype=np.float32), limit=1)

    assert rows.tolist() == [[0]]
    assert scores[0, 0] > 0.89
