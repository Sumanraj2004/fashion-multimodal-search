FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TORCH_HOME=/opt/torch

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu \
        "torch==2.5.1+cpu" "torchvision==0.20.1+cpu"

COPY pyproject.toml /tmp/build/pyproject.toml
COPY backend/__init__.py /tmp/build/backend/__init__.py
COPY backend/app/ /tmp/build/backend/app/
RUN cd /tmp/build \
    && python -m pip install . \
    && rm -rf /tmp/build

RUN python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device='cpu')"

COPY data/artifacts_v2/catalog.faiss /app/data/artifacts_v2/catalog.faiss
COPY data/artifacts_v2/index_product_ids.npy /app/data/artifacts_v2/index_product_ids.npy
COPY data/raw/catalog.jsonl /app/data/raw/catalog.jsonl

RUN useradd --system --create-home --uid 10001 app
USER app

EXPOSE 8000

CMD ["uvicorn", "backend.app.search_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
