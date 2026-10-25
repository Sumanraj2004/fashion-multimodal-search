import numpy as np
import pytest

from pipeline.evaluate_retrieval import evaluate, recall_at_k
from pipeline.schemas import EvaluationQuery


class FixedIndex:
    def search(self, queries: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
        return np.array([[0.9, 0.8]], dtype=np.float32), np.array([[1, 0]], dtype=np.int64)


def test_recall_at_k_counts_a_relevant_hit() -> None:
    queries = [EvaluationQuery(query_id="q1", text="dress", relevant_product_ids=["product-b"])]

    assert recall_at_k([["product-a", "product-b"]], queries, k=1) == 0.0
    assert recall_at_k([["product-a", "product-b"]], queries, k=2) == 1.0


def test_evaluate_reports_recall_and_latency() -> None:
    queries = [EvaluationQuery(query_id="q1", text="dress", relevant_product_ids=["b"])]
    report = evaluate(
        queries, lambda _: np.array([[1.0, 0.0]], dtype=np.float32), FixedIndex(), ["a", "b"]
    )

    assert report.recall_at_1 == 1.0
    assert report.recall_at_5 == 1.0
    assert report.mean_latency_ms >= 0


def test_recall_at_k_rejects_misaligned_results() -> None:
    with pytest.raises(ValueError, match="identical lengths"):
        recall_at_k([], [EvaluationQuery(query_id="q", text="x", relevant_product_ids=["1"])], 1)
