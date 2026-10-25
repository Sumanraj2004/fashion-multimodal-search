"""Download, verify, hash, and deduplicate catalog images."""

import hashlib
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

from pipeline.schemas import ProductRecord


def _verify_image(content: bytes) -> None:
    """Reject malformed, truncated, or decompression-bomb image payloads."""

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("Response is not a valid image") from error


def download_images(
    records: Iterable[ProductRecord], image_dir: Path, timeout_seconds: float
) -> tuple[list[ProductRecord], dict[str, int]]:
    """Return only products whose images download and verify successfully.

    Content hashes identify byte-for-byte duplicate images. Only the first product is
    retained because a vector index should not contain duplicate catalog entries.
    """

    image_dir.mkdir(parents=True, exist_ok=True)
    accepted: list[ProductRecord] = []
    seen_hashes: set[str] = set()
    report = {"download_failed": 0, "invalid_image": 0, "duplicate_image_bytes": 0}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        for record in records:
            try:
                response = client.get(str(record.image_url))
                response.raise_for_status()
                content = response.content
            except httpx.HTTPError:
                report["download_failed"] += 1
                continue
            try:
                _verify_image(content)
            except ValueError:
                report["invalid_image"] += 1
                continue
            digest = hashlib.sha256(content).hexdigest()
            if digest in seen_hashes:
                report["duplicate_image_bytes"] += 1
                continue
            image_path = image_dir / f"{record.id}.jpg"
            image_path.write_bytes(content)
            seen_hashes.add(digest)
            accepted.append(
                record.model_copy(update={"image_path": str(image_path), "image_sha256": digest})
            )
    return accepted, report
