from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cors_allows_development_frontend_with_credentials() -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:3000"
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_category_delete() -> None:
    response = client.options(
        "/api/boards/1/categories/1",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
