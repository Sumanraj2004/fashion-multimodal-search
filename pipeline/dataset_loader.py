"""Load Amazon Fashion 2023-style JSONL metadata into a stable schema."""

import json
import re
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pipeline.schemas import ProductRecord


def _image_url(raw: dict[str, Any]) -> str | None:
    """Return the highest-resolution image URL available in Amazon metadata."""

    images = raw.get("images") or raw.get("imageURLHighRes") or raw.get("imageURL") or []
    if isinstance(images, str):
        return images
    for image in images:
        if isinstance(image, str):
            return image
        if isinstance(image, dict):
            for key in ("high_res", "large", "url", "image_url"):
                if image.get(key):
                    return str(image[key])
    return None


def _price(value: Any) -> Decimal | None:
    """Parse currency-formatted prices without inventing a price when it is missing."""

    if value is None:
        return None
    match = re.search(r"\d+(?:[,.]\d{1,2})?", str(value).replace(",", ""))
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def normalize_amazon_record(raw: dict[str, Any]) -> ProductRecord | None:
    """Map an Amazon Reviews 2023 product record to the application schema."""

    product_id = raw.get("parent_asin") or raw.get("asin")
    title = raw.get("title")
    image_url = _image_url(raw)
    if not product_id or not title or not image_url:
        return None
    categories = raw.get("categories") or []
    category = raw.get("main_category") or (categories[-1] if categories else None)
    if isinstance(category, list):
        category = category[-1] if category else None
    description = raw.get("description")
    if isinstance(description, list):
        description = " ".join(str(item) for item in description)
    return ProductRecord(
        id=str(product_id),
        title=str(title),
        category=str(category) if category else None,
        price=_price(raw.get("price")),
        description=str(description) if description else None,
        image_url=image_url,
    )


def load_amazon_jsonl(metadata_path: Path, limit: int) -> Iterator[ProductRecord]:
    """Yield up to ``limit`` valid normalized products from a JSONL export."""

    produced = 0
    with metadata_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = normalize_amazon_record(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {metadata_path}:{line_number}") from error
            if record is None:
                continue
            yield record
            produced += 1
            if produced >= limit:
                return


def write_jsonl(records: Iterator[ProductRecord], output_path: Path) -> int:
    """Write Pydantic records to JSONL and return the number written."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[ProductRecord]:
    """Read a normalized catalog JSONL artifact."""

    with path.open(encoding="utf-8") as handle:
        return [ProductRecord.model_validate_json(line) for line in handle if line.strip()]
