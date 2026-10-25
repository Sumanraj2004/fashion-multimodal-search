"""Harder evaluation: text query -> IMAGE embeddings only.

Why: the Phase 1 eval used "AMAZON FASHION <full product title>" as the query
against an index that appears to include text information, so it was nearly a
lookup of the product's own title (recall ~1.0). Here the query is the cleaned
title text and the database contains ONLY image embeddings, so the model must
match words to pictures. That is real CLIP retrieval, and the numbers will be
much lower and much more meaningful.

Run from the project root (server not needed):
    python eval_text_to_image.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

PREFIX = "AMAZON FASHION "


def clean_query(text: str, keep_prefix: bool = False) -> str:
    if not keep_prefix and text.startswith(PREFIX):
        return text[len(PREFIX):]
    return text


def retrieval_metrics(scores: np.ndarray, ids: list[str], relevant: list[set[str]], ks=(1, 5, 10)) -> dict:
    """scores: (n_queries, n_items). relevant[i] = set of correct product ids for query i."""
    index_of = {pid: i for i, pid in enumerate(ids)}
    order = np.argsort(-scores, axis=1)
    ranks = []
    for i, rel in enumerate(relevant):
        rel_idx = [index_of[p] for p in rel if p in index_of]
        if not rel_idx:
            continue
        positions = np.where(np.isin(order[i], rel_idx))[0]
        ranks.append(int(positions[0]) + 1)
    ranks_arr = np.array(ranks)
    out = {"query_count": int(len(ranks_arr)), "catalog_size": len(ids)}
    for k in ks:
        out[f"recall_at_{k}"] = round(float((ranks_arr <= k).mean()), 4)
        out[f"random_chance_at_{k}"] = round(k / len(ids), 4)
    out["mrr"] = round(float((1.0 / ranks_arr).mean()), 4)
    out["median_rank"] = float(np.median(ranks_arr))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--embeddings", default="data/artifacts/image_embeddings.npy")
    ap.add_argument("--ids", default="data/artifacts/product_ids.npy")
    ap.add_argument("--queries", default="data/artifacts/evaluation_queries.json")
    ap.add_argument("--output", default="data/artifacts/text_to_image_metrics.json")
    ap.add_argument("--model", default="ViT-B-32")
    ap.add_argument("--pretrained", default="laion2b_s34b_b79k")
    ap.add_argument("--keep-prefix", action="store_true", help="keep the 'AMAZON FASHION' prefix in queries")
    args = ap.parse_args()

    from backend.app.search_api.embedder import ClipEmbedder, l2_normalize

    img = l2_normalize(np.load(args.embeddings))
    ids = [str(x) for x in np.load(args.ids, allow_pickle=True).tolist()]
    if len(ids) != len(img):
        raise SystemExit(f"{args.embeddings} has {len(img)} rows but {args.ids} has {len(ids)} ids; they must align.")
    queries = json.loads(Path(args.queries).read_text(encoding="utf-8"))

    embedder = ClipEmbedder(args.model, args.pretrained)
    q_vecs = np.vstack([embedder.embed_text(clean_query(q["text"], args.keep_prefix)) for q in queries])
    scores = q_vecs @ img.T
    metrics = retrieval_metrics(scores, ids, [set(q["relevant_product_ids"]) for q in queries])
    metrics["setup"] = "text query -> image-only embeddings"
    print(json.dumps(metrics, indent=2))
    Path(args.output).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Saved to", args.output)


if __name__ == "__main__":
    main()