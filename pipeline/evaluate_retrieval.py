"""Measured text-to-catalog retrieval evaluation."""

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from pipeline.schemas import EvaluationQuery
from pipeline.vector_index import VectorSearcher


@dataclass(frozen=True)
class EvaluationReport:
    """Metrics recorded for an immutable index/model combination."""

    query_count: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mean_latency_ms: float


def recall_at_k(
    retrieved_ids: Sequence[Sequence[str]], queries: Sequence[EvaluationQuery], k: int
) -> float:
    """Compute fraction of queries with at least one relevant hit in the first k."""

    if not queries:
        raise ValueError("At least one evaluation query is required")
    if len(retrieved_ids) != len(queries):
        raise ValueError("Results and queries must have identical lengths")
    hits = sum(
        bool(set(result[:k]).intersection(query.relevant_product_ids))
        for result, query in zip(retrieved_ids, queries, strict=True)
    )
    return hits / len(queries)


def evaluate(
    queries: Sequence[EvaluationQuery],
    encode_query: Callable[[Sequence[str]], np.ndarray],
    index: VectorSearcher,
    product_ids: Sequence[str],
) -> EvaluationReport:
    """Execute each query individually to capture user-visible search latency."""

    results: list[list[str]] = []
    latencies_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        _, rows = index.search(encode_query([query.text]), limit=10)
        latencies_ms.append((time.perf_counter() - started) * 1000)
        results.append([product_ids[row] for row in rows[0] if row >= 0])
    return EvaluationReport(
        query_count=len(queries),
        recall_at_1=recall_at_k(results, queries, 1),
        recall_at_5=recall_at_k(results, queries, 5),
        recall_at_10=recall_at_k(results, queries, 10),
        mean_latency_ms=float(np.mean(latencies_ms)),
    )


def save_report(report: EvaluationReport, output_path: Path) -> None:
    """Write a machine-readable baseline report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
