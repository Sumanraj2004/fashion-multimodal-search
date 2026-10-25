"""Command-line entry points for every reproducible Phase 1 stage."""

import argparse
import json
from pathlib import Path

import numpy as np

from backend.app.db.base import Base
from backend.app.db.session import build_session_factory
from pipeline.catalog_repository import upsert_products
from pipeline.cleaning import clean_records
from pipeline.dataset_loader import load_amazon_jsonl, read_jsonl, write_jsonl
from pipeline.embeddings import ClipEmbedder, generate_catalog_embeddings, save_embeddings
from pipeline.evaluate_retrieval import evaluate, save_report
from pipeline.evaluation_set import create_evaluation_set, load_evaluation_set, save_evaluation_set
from pipeline.image_store import download_images
from pipeline.vector_index import FaissCosineIndex, build_and_save


def _write_records(records: list, path: Path) -> None:
    write_jsonl(iter(records), path)


def normalize(args: argparse.Namespace) -> None:
    """Normalize Amazon metadata and eliminate pre-download duplicates."""

    records, report = clean_records(load_amazon_jsonl(args.metadata, args.limit))
    _write_records(records, args.output)
    print(json.dumps({"accepted": len(records), **report}, indent=2))


def download(args: argparse.Namespace) -> None:
    """Download verified product images and write the enriched manifest."""

    records, report = download_images(read_jsonl(args.input), args.image_dir, args.timeout_seconds)
    _write_records(records, args.output)
    print(json.dumps({"accepted": len(records), **report}, indent=2))


def init_db(args: argparse.Namespace) -> None:
    """Create tables for local development; production should use Alembic."""

    factory = build_session_factory(args.database_url)
    Base.metadata.create_all(factory.kw["bind"])
    print("Database tables created.")


def persist(args: argparse.Namespace) -> None:
    """Upsert the image-verified catalog manifest into PostgreSQL."""

    factory = build_session_factory(args.database_url)
    with factory() as session:
        count = upsert_products(session, read_jsonl(args.input))
    print(f"Persisted {count} products.")


def embed(args: argparse.Namespace) -> None:
    """Generate and persist image, text, and fused catalog embeddings."""

    embedder = ClipEmbedder(args.model, args.pretrained, args.device)
    embeddings = generate_catalog_embeddings(read_jsonl(args.input), embedder, args.batch_size)
    save_embeddings(embeddings, args.output_dir)
    print(f"Embedded {len(embeddings.product_ids)} products on {embedder.device}.")


def index(args: argparse.Namespace) -> None:
    """Build the exact FAISS baseline index from fused catalog vectors."""

    vectors = np.load(args.embedding_dir / "catalog_embeddings.npy")
    product_ids = np.load(args.embedding_dir / "product_ids.npy").tolist()
    build_and_save(vectors, product_ids, args.output_dir)
    print(f"Indexed {len(product_ids)} products.")


def make_evaluation_set(args: argparse.Namespace) -> None:
    """Create a deterministic, inspectable text evaluation dataset."""

    queries = create_evaluation_set(read_jsonl(args.input), size=args.size, seed=args.seed)
    save_evaluation_set(queries, args.output)
    print(f"Wrote {len(queries)} evaluation queries to {args.output}.")


def evaluate_index(args: argparse.Namespace) -> None:
    """Measure retrieval recall and mean end-to-end query embedding/index latency."""

    embedder = ClipEmbedder(args.model, args.pretrained, args.device)
    report = evaluate(
        load_evaluation_set(args.queries),
        lambda texts: embedder.encode_text(texts, args.batch_size),
        FaissCosineIndex.load(args.index),
        np.load(args.product_ids).tolist(),
    )
    save_report(report, args.output)
    print(json.dumps(report.__dict__, indent=2))


def _add_model_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", choices=("cpu", "cuda"), default=None)


def build_parser() -> argparse.ArgumentParser:
    """Build the stage-oriented command-line interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser("normalize")
    command.add_argument("--metadata", type=Path, required=True)
    command.add_argument("--output", type=Path, default=Path("data/raw/catalog.jsonl"))
    command.add_argument("--limit", type=int, default=10_000)
    command.set_defaults(handler=normalize)

    command = commands.add_parser("download-images")
    command.add_argument("--input", type=Path, default=Path("data/raw/catalog.jsonl"))
    command.add_argument("--output", type=Path, default=Path("data/processed/catalog.jsonl"))
    command.add_argument("--image-dir", type=Path, default=Path("data/processed/images"))
    command.add_argument("--timeout-seconds", type=float, default=20.0)
    command.set_defaults(handler=download)

    command = commands.add_parser("init-db")
    command.add_argument("--database-url", default=None)
    command.set_defaults(handler=init_db)

    command = commands.add_parser("persist")
    command.add_argument("--input", type=Path, default=Path("data/processed/catalog.jsonl"))
    command.add_argument("--database-url", default=None)
    command.set_defaults(handler=persist)

    command = commands.add_parser("embed")
    command.add_argument("--input", type=Path, default=Path("data/processed/catalog.jsonl"))
    command.add_argument("--output-dir", type=Path, default=Path("data/artifacts"))
    _add_model_options(command)
    command.set_defaults(handler=embed)

    command = commands.add_parser("index")
    command.add_argument("--embedding-dir", type=Path, default=Path("data/artifacts"))
    command.add_argument("--output-dir", type=Path, default=Path("data/artifacts"))
    command.set_defaults(handler=index)

    command = commands.add_parser("make-eval-set")
    command.add_argument("--input", type=Path, default=Path("data/processed/catalog.jsonl"))
    command.add_argument(
        "--output", type=Path, default=Path("data/artifacts/evaluation_queries.json")
    )
    command.add_argument("--size", type=int, default=200)
    command.add_argument("--seed", type=int, default=42)
    command.set_defaults(handler=make_evaluation_set)

    command = commands.add_parser("evaluate")
    command.add_argument(
        "--queries", type=Path, default=Path("data/artifacts/evaluation_queries.json")
    )
    command.add_argument("--index", type=Path, default=Path("data/artifacts/catalog.faiss"))
    command.add_argument(
        "--product-ids", type=Path, default=Path("data/artifacts/index_product_ids.npy")
    )
    command.add_argument(
        "--output", type=Path, default=Path("data/artifacts/baseline_metrics.json")
    )
    _add_model_options(command)
    command.set_defaults(handler=evaluate_index)
    return parser


def main() -> None:
    """Execute the selected pipeline stage."""

    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
