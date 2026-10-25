"""Database entities for the catalog."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Product(Base):
    """Cleaned catalog item; embeddings are stored as immutable pipeline artifacts."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str | None] = mapped_column(String(256))
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
