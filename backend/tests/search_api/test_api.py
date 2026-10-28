from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from backend.app.search_api.app import Services, create_app
from backend.app.search_api.config import load_settings


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["index_vectors"] == 30


def test_categories_returns_sorted_product_counts(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == {
        "categories": [
            {"category": "Hoodies", "count": 15},
            {"category": "Shoes", "count": 15},
        ]
    }


def test_cors_allows_configured_frontend_origin(client):
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = client.options(
            "/search/text",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin

    denied = client.options(
        "/search/text",
        headers={
            "Origin": "https://unconfigured.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_runtime_settings_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://demo.example, https://www.example")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "12")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "30")
    settings = load_settings()
    assert settings.allowed_origins == ("https://demo.example", "https://www.example")
    assert settings.rate_limit_requests == 12
    assert settings.rate_limit_window_seconds == 30


@pytest.mark.parametrize(
    ("name", "value"),
    [("RATE_LIMIT_REQUESTS", "0"), ("RATE_LIMIT_WINDOW_SECONDS", "0")],
)
def test_rate_limit_settings_must_be_positive(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=f"{name} must be at least 1"):
        load_settings()


def test_search_rate_limit_is_configurable_and_per_endpoint(client, png_bytes):
    services = client.app.state.services
    limited_settings = replace(
        services.settings, rate_limit_requests=1, rate_limit_window_seconds=60
    )
    app = create_app(Services(services.search, services.catalog, limited_settings))
    with TestClient(app) as limited_client:
        origin_headers = {"Origin": "http://localhost:3000"}
        assert limited_client.post(
            "/search/text", json={"query": "item 3"}, headers=origin_headers
        ).status_code == 200
        limited = limited_client.post(
            "/search/text", json={"query": "item 4"}, headers=origin_headers
        )
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) >= 1
        assert limited.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert limited.headers["access-control-expose-headers"] == "Retry-After"
        assert limited_client.get("/health").status_code == 200
        image_response = limited_client.post(
            "/search/image",
            files={"file": ("a.png", png_bytes, "image/png")},
        )
        assert image_response.status_code == 200
        assert limited_client.post(
            "/search/image",
            files={"file": ("a.png", png_bytes, "image/png")},
        ).status_code == 429


def test_text_search_returns_expected_fields(client):
    r = client.post("/search/text", json={"query": "item 3", "top_k": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["id"] == "p3"
    for key in ("id", "title", "category", "price", "image_url", "score"):
        assert key in body["results"][0]
    assert body["took_ms"] >= 0 and len(body["results"]) == 5


def test_category_filter(client):
    r = client.post("/search/text", json={"query": "item 3", "top_k": 10, "category": "Shoes"})
    assert r.status_code == 200
    assert r.json()["results"] and all(x["category"] == "Shoes" for x in r.json()["results"])


def test_price_filter(client):
    r = client.post("/search/text", json={"query": "item 3", "top_k": 20, "min_price": 40, "max_price": 80})
    prices = [x["price"] for x in r.json()["results"]]
    assert prices and all(40 <= p <= 80 for p in prices)


def test_pagination_pages_do_not_overlap(client):
    p1 = client.post("/search/text", json={"query": "item 3", "top_k": 5, "page": 1}).json()
    p2 = client.post("/search/text", json={"query": "item 3", "top_k": 5, "page": 2}).json()
    ids1 = {x["id"] for x in p1["results"]}
    ids2 = {x["id"] for x in p2["results"]}
    assert ids2 and not ids1 & ids2 and p1["has_more"] is True


def test_empty_results(client):
    r = client.post("/search/text", json={"query": "x", "category": "Nonexistent"})
    assert r.status_code == 200 and r.json()["results"] == [] and r.json()["has_more"] is False


def test_cache_hit_on_repeat(client):
    body = {"query": "item 7", "top_k": 5}
    assert client.post("/search/text", json=body).json()["cached"] is False
    assert client.post("/search/text", json=body).json()["cached"] is True


def test_text_validation_errors(client):
    assert client.post("/search/text", json={"query": ""}).status_code == 422
    assert client.post("/search/text", json={"query": "x", "top_k": 0}).status_code == 422
    assert client.post("/search/text", json={"query": "x", "top_k": 51}).status_code == 422
    assert client.post("/search/text", json={"query": "x", "min_price": 9, "max_price": 1}).status_code == 422
    assert client.post("/search/text", json={"query": "a" * 201}).status_code == 422


def test_image_search_finds_matching_item(client, png_bytes):
    r = client.post("/search/image", files={"file": ("a.png", png_bytes, "image/png")}, data={"top_k": "3"})
    assert r.status_code == 200 and r.json()["results"][0]["id"] == "p5"


def test_image_wrong_type(client):
    r = client.post("/search/image", files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 415


def test_image_too_large(client):
    big = b"\x00" * (1024 * 1024 + 10)
    r = client.post("/search/image", files={"file": ("a.png", big, "image/png")})
    assert r.status_code == 413


def test_image_corrupt(client):
    r = client.post("/search/image", files={"file": ("a.png", b"not an image", "image/png")})
    assert r.status_code == 400


def test_image_bad_filters(client, png_bytes):
    r = client.post("/search/image", files={"file": ("a.png", png_bytes, "image/png")},
                    data={"min_price": "9", "max_price": "1"})
    assert r.status_code == 422


def test_get_product_and_404(client):
    assert client.get("/products/p1").json()["title"] == "item 1"
    assert client.get("/products/nope").status_code == 404
