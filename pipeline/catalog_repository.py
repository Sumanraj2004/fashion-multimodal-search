"""Persistence boundary for the offline catalog pipeline."""

from collections.abc import Iterable
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.db.models import Product
from pipeline.schemas import ProductRecord


def upsert_products(session: Session, records: Iterable[ProductRecord]) -> int:
    """Persist cleaned products idempotently, then commit the batch."""

    count = 0
    for record in records:
        if record.image_path is None or record.image_sha256 is None:
            raise ValueError(f"Product {record.id} has not completed image processing")
        product = Product(
            id=record.id,
            title=record.title,
            category=record.category,
            price=Decimal(record.price) if record.price is not None else None,
            currency=record.currency,
            description=record.description,
            image_url=str(record.image_url),
            image_path=record.image_path,
            image_sha256=record.image_sha256,
        )
        session.merge(product)
        count += 1
    session.commit()
    return count
