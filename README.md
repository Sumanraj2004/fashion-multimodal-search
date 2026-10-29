# Multimodal AI Search and Recommendation Platform

[![CI](https://github.com/Sumanraj2004/fashion-multimodal-search/actions/workflows/ci.yml/badge.svg)](https://github.com/Sumanraj2004/fashion-multimodal-search/actions/workflows/ci.yml)

Phase 1 provides a reproducible fashion-catalog ingestion pipeline, OpenCLIP embeddings, an exact FAISS
cosine-similarity baseline, PostgreSQL metadata storage, and a labeled text-retrieval evaluation.

## Baseline architecture

```text
Amazon Fashion metadata -> validation/deduplication -> verified local images -> PostgreSQL
                                                          |
                                                          v
                              OpenCLIP ViT-B/32 image + text embeddings -> fused vectors -> FAISS
                                                                                              |
                                              labeled evaluation queries -> recall@1/5/10 + latency
```

The index is isolated behind `VectorSearcher`; Phase 2 can add a Qdrant adapter without changing evaluation
or application callers. FAISS is the recommended baseline because it is local, fast, and easy to measure.

## Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL)
- NVIDIA CUDA is optional. The embedder selects CUDA automatically when PyTorch can use it; otherwise it runs on CPU.

## Setup (PowerShell)

```powershell
Set-Location "C:\path\to\project"
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
docker compose up -d postgres
alembic upgrade head
```

Follow [data/README.md](data/README.md) to obtain `data/raw/meta_Fashion.jsonl`. The dataset downloader is
deliberately not automated: its license and distribution URL can change, while the pipeline accepts the stable JSONL export.

## Run the search application with Docker

The Docker build uses the tracked runtime inputs `data/artifacts_v2/catalog.faiss`,
`data/artifacts_v2/index_product_ids.npy`, and `data/raw/catalog.jsonl`, and downloads the
`ViT-B-32 / laion2b_s34b_b79k` model weights while building the backend image. Build from the repository
root so these paths are available in the Docker build context:

```powershell
Set-Location "C:\path\to\project"
docker compose up --build
```

The frontend is available at `http://localhost:3000` and the API at `http://localhost:8000`.
If the browser reaches the API at a different URL, set `NEXT_PUBLIC_API_URL` before building. Compose binds
the API to host loopback and trusts forwarded headers from the Docker network; keep the API behind the trusted
host reverse proxy, and set `FORWARDED_ALLOW_IPS` to its exact source IP(s) when known. This lets Uvicorn's
proxy middleware set the request client address used by the rate limiter. The backend healthcheck probes
`/health`; the frontend waits for it before starting.

The non-Docker workflow remains available. In a PowerShell window from the repository root:

```powershell
Set-Location "C:\path\to\project"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e .
py -m uvicorn backend.app.search_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
Set-Location "C:\path\to\project\frontend"
npm ci
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

## Run Phase 1

```powershell
py -m pipeline.run_phase1 normalize --metadata data/raw/meta_Fashion.jsonl --limit 10000
py -m pipeline.run_phase1 download-images
py -m pipeline.run_phase1 persist
py -m pipeline.run_phase1 embed --batch-size 32
py -m pipeline.run_phase1 index
py -m pipeline.run_phase1 make-eval-set --size 200
py -m pipeline.run_phase1 evaluate
```

For CPU-only systems, begin with `--batch-size 8`. For a CUDA system, use the largest stable batch size; record it with the results.
The first embedding command downloads the approved `ViT-B-32 / laion2b_s34b_b79k` weights once into the local model cache.

Artifacts are written to `data/artifacts/`:

- `image_embeddings.npy`, `text_embeddings.npy`, `catalog_embeddings.npy`
- `catalog.faiss` and `index_product_ids.npy`
- `evaluation_queries.json` (up to 200 query/product relevance labels)
- `baseline_metrics.json`

## Test and quality checks

```powershell
pytest
ruff check .
```

## Resume metrics to record

After a complete run, copy the measured values from `data/artifacts/baseline_metrics.json`:

- catalog size after broken and duplicate image removal
- `recall_at_1`, `recall_at_5`, and `recall_at_10` on the fixed evaluation set
- `mean_latency_ms`, model name, device, and embedding batch size

Do not claim a metric until that report has been generated on your hardware. Phase 6 will reuse the same labels for the before/after fine-tuning comparison.
