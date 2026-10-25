"""Single-load OpenCLIP embedder for batched image and text encoding."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from pipeline.schemas import ProductRecord


@dataclass
class CatalogEmbeddings:
    """Aligned catalog IDs and normalized image/text/fused vectors."""

    product_ids: list[str]
    image_vectors: np.ndarray
    text_vectors: np.ndarray
    fused_vectors: np.ndarray


def _normalize(vectors: Any) -> Any:
    """L2 normalize vectors so dot product equals cosine similarity."""

    return vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-12)


class ClipEmbedder:
    """OpenCLIP wrapper that loads weights once per pipeline process."""

    def __init__(self, model_name: str, pretrained: str, device: str | None = None) -> None:
        # Import lazily so lightweight pipeline utilities and tests do not require model extras.
        import open_clip
        import torch

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.eval()

    def encode_text(self, texts: Sequence[str], batch_size: int) -> np.ndarray:
        """Encode text in batches as float32 normalized vectors."""

        batches = []
        with self.torch.inference_mode():
            for start in range(0, len(texts), batch_size):
                tokens = self.tokenizer(list(texts[start : start + batch_size])).to(self.device)
                batches.append(_normalize(self.model.encode_text(tokens)).cpu())
        return self.torch.cat(batches).numpy().astype(np.float32, copy=False)

    def encode_images(self, paths: Sequence[str], batch_size: int) -> np.ndarray:
        """Encode validated local images in batches as float32 normalized vectors."""

        batches = []
        with self.torch.inference_mode():
            for start in range(0, len(paths), batch_size):
                images = []
                for path in paths[start : start + batch_size]:
                    with Image.open(path) as image:
                        images.append(self.preprocess(image.convert("RGB")))
                input_batch = self.torch.stack(images).to(self.device)
                batches.append(_normalize(self.model.encode_image(input_batch)).cpu())
        return self.torch.cat(batches).numpy().astype(np.float32, copy=False)


def product_text(record: ProductRecord) -> str:
    """Build concise text used for catalog-side CLIP alignment."""

    fields = [record.title, record.category or "", record.description or ""]
    return ". ".join(value for value in fields if value)


def generate_catalog_embeddings(
    records: Sequence[ProductRecord], embedder: ClipEmbedder, batch_size: int
) -> CatalogEmbeddings:
    """Generate separate image/text vectors and a normalized equal-weight fusion."""

    if not records:
        raise ValueError("Cannot embed an empty catalog")
    image_paths = [record.image_path for record in records]
    if any(path is None for path in image_paths):
        raise ValueError("Every product must have a downloaded image_path")
    image_vectors = embedder.encode_images([str(path) for path in image_paths], batch_size)
    text_vectors = embedder.encode_text([product_text(record) for record in records], batch_size)
    fused = image_vectors + text_vectors
    fused /= np.linalg.norm(fused, axis=1, keepdims=True).clip(min=1e-12)
    return CatalogEmbeddings([record.id for record in records], image_vectors, text_vectors, fused)


def save_embeddings(embeddings: CatalogEmbeddings, output_dir: Path) -> None:
    """Persist aligned NumPy artifacts without pickle serialization."""

    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "product_ids.npy", np.asarray(embeddings.product_ids, dtype="U128"))
    np.save(output_dir / "image_embeddings.npy", embeddings.image_vectors)
    np.save(output_dir / "text_embeddings.npy", embeddings.text_vectors)
    np.save(output_dir / "catalog_embeddings.npy", embeddings.fused_vectors)
