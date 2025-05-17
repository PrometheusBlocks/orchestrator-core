from fastapi.testclient import TestClient

from orchestrator_core.api.main import app


def test_get_utility_found(monkeypatch):
    mock_specs = {"foo": {"name": "foo", "version": "1.0.0"}}
    monkeypatch.setattr(
        "orchestrator_core.catalog.index.load_specs", lambda: mock_specs
    )
    client = TestClient(app)
    response = client.get("/utility/foo")
    assert response.status_code == 200
    assert response.json() == {"name": "foo", "version": "1.0.0"}


def test_get_utility_not_found(monkeypatch):
    monkeypatch.setattr("orchestrator_core.catalog.index.load_specs", lambda: {})
    client = TestClient(app)
    response = client.get("/utility/bar")
    assert response.status_code == 404


def test_root_serves_webui(tmp_path):
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "PrometheusBlocks WebUI" in response.text
