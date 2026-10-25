"""Catalog validation and deterministic record-level deduplication."""

from collections.abc import Iterable

from pipeline.schemas import ProductRecord


def clean_records(records: Iterable[ProductRecord]) -> tuple[list[ProductRecord], dict[str, int]]:
    """Remove duplicate IDs and URLs before any network or model work occurs."""

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    cleaned: list[ProductRecord] = []
    rejected = {"duplicate_id": 0, "duplicate_image_url": 0}
    for record in records:
        if record.id in seen_ids:
            rejected["duplicate_id"] += 1
            continue
        url = str(record.image_url)
        if url in seen_urls:
            rejected["duplicate_image_url"] += 1
            continue
        seen_ids.add(record.id)
        seen_urls.add(url)
        cleaned.append(record)
    return cleaned, rejected
