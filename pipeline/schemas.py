"""Validated interchange models for pipeline files."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ProductRecord(BaseModel):
    """Normalized item before image download and database persistence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    category: str | None = Field(default=None, max_length=256)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str | None = None
    image_url: HttpUrl
    image_path: str | None = None
    image_sha256: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Keep currency codes comparable across data sources."""

        return value.upper()


class EvaluationQuery(BaseModel):
    """A text query with one or more acceptable catalog product IDs."""

    query_id: str
    text: str = Field(min_length=1)
    relevant_product_ids: list[str] = Field(min_length=1)
