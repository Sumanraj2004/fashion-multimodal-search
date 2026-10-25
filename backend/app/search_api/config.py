"""Settings for the Phase 2 search API, read from environment variables.

Every path/model name here must match what Phase 1 produced. Change them in
`.env` (or the environment), not in code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # --- Phase 1 outputs (ADJUST to your real paths) ---
    index_path: str = "data/artifacts_v2/catalog.faiss"
    ids_path: str = "data/artifacts_v2/index_product_ids.npy"  # .json list OR one id per line
    catalog_path: str = "data/raw/catalog.jsonl"
    # --- CLIP model: MUST be the same one used by the `embed` stage ---
    clip_model: str = "ViT-B-32"
    clip_pretrained: str = "laion2b_s34b_b79k"
    # --- Search behaviour ---
    candidate_multiplier: int = 5   # fetch top_k*page*multiplier before filtering
    candidate_cap: int = 500        # hard upper bound on candidates per query
    max_upload_mb: int = 5
    # --- Cache ---
    redis_url: str = ""             # empty -> in-memory cache
    cache_ttl_seconds: int = 300
    # --- Category tagging (fixes the all-"AMAZON FASHION" category problem) ---
    zero_shot_categories: bool = True
    # --- Public demo request protection ---
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60


def load_settings() -> Settings:
    d = Settings()
    g = os.getenv
    allowed_origins = tuple(
        origin.strip()
        for origin in g("ALLOWED_ORIGINS", ",".join(d.allowed_origins)).split(",")
        if origin.strip()
    )
    rate_limit_requests = int(g("RATE_LIMIT_REQUESTS", d.rate_limit_requests))
    rate_limit_window_seconds = int(
        g("RATE_LIMIT_WINDOW_SECONDS", d.rate_limit_window_seconds)
    )
    if rate_limit_requests < 1:
        raise ValueError("RATE_LIMIT_REQUESTS must be at least 1")
    if rate_limit_window_seconds < 1:
        raise ValueError("RATE_LIMIT_WINDOW_SECONDS must be at least 1")

    return Settings(
        index_path=g("INDEX_PATH", d.index_path),
        ids_path=g("IDS_PATH", d.ids_path),
        catalog_path=g("CATALOG_PATH", d.catalog_path),
        clip_model=g("CLIP_MODEL", d.clip_model),
        clip_pretrained=g("CLIP_PRETRAINED", d.clip_pretrained),
        candidate_multiplier=int(g("CANDIDATE_MULTIPLIER", d.candidate_multiplier)),
        candidate_cap=int(g("CANDIDATE_CAP", d.candidate_cap)),
        max_upload_mb=int(g("MAX_UPLOAD_MB", d.max_upload_mb)),
        redis_url=g("REDIS_URL", d.redis_url),
        cache_ttl_seconds=int(g("CACHE_TTL_SECONDS", d.cache_ttl_seconds)),
        zero_shot_categories=g("ZERO_SHOT_CATEGORIES", "1").lower() not in ("0", "false", "no"),
        allowed_origins=allowed_origins,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window_seconds=rate_limit_window_seconds,
    )
