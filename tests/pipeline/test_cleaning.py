from pipeline.cleaning import clean_records
from pipeline.schemas import ProductRecord


def product(product_id: str, image_url: str) -> ProductRecord:
    return ProductRecord(id=product_id, title="Black Hoodie", image_url=image_url)


def test_clean_records_rejects_duplicate_ids_and_image_urls() -> None:
    cleaned, report = clean_records(
        [
            product("one", "https://example.com/one.jpg"),
            product("one", "https://example.com/two.jpg"),
            product("three", "https://example.com/one.jpg"),
        ]
    )

    assert [record.id for record in cleaned] == ["one"]
    assert report == {"duplicate_id": 1, "duplicate_image_url": 1}
