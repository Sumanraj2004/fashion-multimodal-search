"""Query embedding. Must use the SAME model/preprocessing as Phase 1's `embed` stage."""
from __future__ import annotations

import io
from typing import Protocol

import numpy as np


def l2_normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype="float32")
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.clip(norms, 1e-12, None)


class Embedder(Protocol):
    dim: int

    def embed_text(self, text: str) -> np.ndarray: ...
    def embed_image(self, data: bytes) -> np.ndarray: ...


class ClipEmbedder:
    """open_clip implementation. Loaded once at startup.

    If Phase 1 used HuggingFace `transformers` CLIP instead of open_clip,
    replace this class (keep the same two methods) - nothing else changes.
    """

    def __init__(self, model_name: str, pretrained: str, device: str | None = None):
        import open_clip
        import torch

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.model = model.eval()
        self.preprocess = preprocess
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.dim = int(self.model.text_projection.shape[1])

    def embed_text(self, text: str) -> np.ndarray:
        tokens = self.tokenizer([text]).to(self.device)
        with self.torch.no_grad():
            feats = self.model.encode_text(tokens)
        return l2_normalize(feats.cpu().numpy())

    def embed_image(self, data: bytes) -> np.ndarray:
        from PIL import Image

        img = Image.open(io.BytesIO(data)).convert("RGB")
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        with self.torch.no_grad():
            feats = self.model.encode_image(tensor)
        return l2_normalize(feats.cpu().numpy())
