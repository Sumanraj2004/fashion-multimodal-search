"""FastAPI app. Run with:

    uvicorn backend.app.search_api.app:create_app --factory --port 8000
"""
from __future__ import annotations

import io
import logging
import math
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from .cache import build_cache
from .catalog import Catalog
from .config import Settings, load_settings
from .index_store import VectorIndex
from .schemas import Filters, Product, SearchResponse, TextSearchRequest
from .service import SearchService
from .tagging import assign_categories

logger = logging.getLogger("search_api")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
SEARCH_PATHS = {"/search/text", "/search/image"}


@dataclass
class Services:
    search: SearchService
    catalog: Catalog
    settings: Settings


class FixedWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[tuple[str, str], tuple[float, int]] = {}
        self._lock = threading.Lock()

    def retry_after(self, client_ip: str, path: str) -> int | None:
        now = time.monotonic()
        key = (client_ip, path)
        with self._lock:
            expired = [
                window_key
                for window_key, (started, _) in self._windows.items()
                if now - started >= self.window_seconds
            ]
            for window_key in expired:
                del self._windows[window_key]

            started, count = self._windows.get(key, (now, 0))
            if now - started >= self.window_seconds:
                started, count = now, 0
            if count >= self.max_requests:
                return max(1, math.ceil(self.window_seconds - (now - started)))
            self._windows[key] = (started, count + 1)
        return None


def build_services(settings: Settings) -> Services:
    """Load heavy objects ONCE (model, index, catalog, cache)."""
    from .embedder import ClipEmbedder

    embedder = ClipEmbedder(settings.clip_model, settings.clip_pretrained)
    index = VectorIndex.load(settings.index_path, settings.ids_path)
    catalog = Catalog.from_jsonl(settings.catalog_path)
    if settings.zero_shot_categories:
        assign_categories(index, embedder, catalog)
    cache = build_cache(settings.redis_url, settings.cache_ttl_seconds)
    return Services(SearchService(embedder, index, catalog, cache, settings), catalog, settings)


def create_app(services: Optional[Services] = None) -> FastAPI:
    settings = services.settings if services else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.services = services or build_services(settings)
        yield

    app = FastAPI(title="Multimodal Fashion Search API", lifespan=lifespan)
    app.state.rate_limiter = FixedWindowRateLimiter(
        settings.rate_limit_requests, settings.rate_limit_window_seconds
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        if request.method == "POST" and request.url.path in SEARCH_PATHS:
            client_ip = request.client.host if request.client else "unknown"
            retry_after = request.app.state.rate_limiter.retry_after(
                client_ip, request.url.path
            )
            if retry_after is not None:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again shortly."},
                    headers={"Retry-After": str(retry_after)},
                )
                logger.info(
                    "%s %s -> %s in %.1f ms",
                    request.method,
                    request.url.path,
                    response.status_code,
                    (time.perf_counter() - start) * 1000,
                )
                return response
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s in %.1f ms", request.method, request.url.path, response.status_code, ms)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Retry-After"],
    )

    def svc(request: Request) -> Services:
        return request.app.state.services

    @app.get("/health")
    def health(request: Request):
        s = svc(request)
        return {
            "status": "ok",
            "model_loaded": s.search.embedder is not None,
            "index_vectors": s.search.index.size,
            "catalog_products": len(s.catalog),
            "cache": type(s.search.cache).__name__,
        }

    @app.get("/categories")
    def categories(request: Request):
        counts = svc(request).catalog.category_counts()
        return {
            "categories": [
                {"category": category, "count": count}
                for category, count in counts.items()
            ]
        }

    @app.post("/search/text", response_model=SearchResponse)
    def search_text(req: TextSearchRequest, request: Request):
        start = time.perf_counter()
        data, cached = svc(request).search.search_text(req)
        return SearchResponse(**data, took_ms=round((time.perf_counter() - start) * 1000, 2), cached=cached)

    @app.post("/search/image", response_model=SearchResponse)
    def search_image(
        request: Request,
        file: UploadFile = File(...),
        top_k: int = Form(10, ge=1, le=50),
        page: int = Form(1, ge=1),
        category: Optional[str] = Form(None),
        min_price: Optional[float] = Form(None, ge=0),
        max_price: Optional[float] = Form(None, ge=0),
    ):
        s = svc(request)
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(415, "Only JPEG, PNG or WebP images are accepted")
        limit = s.settings.max_upload_mb * 1024 * 1024
        data = file.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"Image larger than {s.settings.max_upload_mb} MB")
        try:
            filters = Filters(category=category, min_price=min_price, max_price=max_price)
        except ValidationError as exc:
            raise HTTPException(422, exc.errors(include_url=False, include_context=False))
        try:
            from PIL import Image

            Image.open(io.BytesIO(data)).verify()
        except Exception:
            raise HTTPException(400, "File is not a valid image")

        start = time.perf_counter()
        result = s.search.search_image(data, top_k, page, filters)
        return SearchResponse(**result, took_ms=round((time.perf_counter() - start) * 1000, 2))

    @app.get("/products/{product_id}", response_model=Product)
    def get_product(product_id: str, request: Request):
        prod = svc(request).catalog.get(product_id)
        if prod is None:
            raise HTTPException(404, f"Product {product_id} not found")
        return prod

    return app
