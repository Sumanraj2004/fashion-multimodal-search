"""Pydantic request/response models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Filters(BaseModel):
    """Optional metadata filters shared by text and image search."""

    category: Optional[str] = Field(None, max_length=100)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def _check_range(self):
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price must be <= max_price")
        return self


class TextSearchRequest(Filters):
    query: str = Field(..., min_length=1, max_length=200)
    top_k: int = Field(10, ge=1, le=50, description="Results per page")
    page: int = Field(1, ge=1)

    @field_validator("query")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query must not be blank")
        return v


class Product(BaseModel):
    id: str
    title: str
    category: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None


class SearchHit(Product):
    score: float


class SearchResponse(BaseModel):
    results: list[SearchHit]
    page: int
    top_k: int
    total_matches: int = Field(
        ..., description="Matches found among the retrieved candidates (not the whole catalog)"
    )
    has_more: bool
    took_ms: float
    cached: bool = False
