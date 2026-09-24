"""Health endpoint tests."""


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_content_type(client):
    response = client.get("/health")
    assert response.headers["content-type"].startswith("application/json")
