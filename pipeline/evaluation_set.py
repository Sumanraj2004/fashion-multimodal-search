"""Create a deterministic, versioned text-retrieval evaluation set."""

import json
import random
from collections.abc import Sequence
from pathlib import Path

from pipeline.schemas import EvaluationQuery, ProductRecord


def _query_for(record: ProductRecord) -> str:
    """Create a natural catalog query without including opaque source identifiers."""

    return f"{record.category} {record.title}" if record.category else record.title


def create_evaluation_set(
    records: Sequence[ProductRecord], size: int = 200, seed: int = 42
) -> list[EvaluationQuery]:
    """Sample a reproducible maximum of 200 products with exact relevance labels."""

    if size < 1:
        raise ValueError("size must be positive")
    sampled = random.Random(seed).sample(list(records), k=min(size, len(records)))
    return [
        EvaluationQuery(
            query_id=f"text-{index:03d}", text=_query_for(record), relevant_product_ids=[record.id]
        )
        for index, record in enumerate(sampled, start=1)
    ]


def save_evaluation_set(queries: Sequence[EvaluationQuery], path: Path) -> None:
    """Save evaluation labels in an inspectable JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([query.model_dump() for query in queries], indent=2), encoding="utf-8"
    )


def load_evaluation_set(path: Path) -> list[EvaluationQuery]:
    """Load the versioned evaluation labels."""

    return [
        EvaluationQuery.model_validate(item)
        for item in json.loads(path.read_text(encoding="utf-8"))
    ]
