from pipeline.embeddings import product_text
from pipeline.schemas import ProductRecord


def test_product_text_includes_available_searchable_fields() -> None:
    record = ProductRecord(
        id="1",
        title="Oversized Hoodie",
        category="Hoodies",
        description="Heavyweight cotton",
        image_url="https://example.com/hoodie.jpg",
    )

    assert product_text(record) == "Oversized Hoodie. Hoodies. Heavyweight cotton"
