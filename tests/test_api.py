from fastapi.testclient import TestClient

from orchestrator_core.api.main import app, normalize_plan_for_scaffolding


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


def test_normalize_plan_list(monkeypatch):
    monkeypatch.setattr(
        "orchestrator_core.api.main.load_specs", lambda: {"foo": {}, "bar": {}}
    )
    raw = [
        {"step_id": 1, "action": "foo"},
        {"step_id": 2, "action": "baz"},
    ]
    norm = normalize_plan_for_scaffolding(raw)
    assert norm == {"resolved": ["foo"], "missing": ["baz"]}


def test_normalize_plan_proposed(monkeypatch):
    monkeypatch.setattr(
        "orchestrator_core.api.main.load_specs", lambda: {"foo": {}, "bar": {}}
    )
    raw = {"proposed_utilities": [{"name": "foo"}, {"name": "qux"}]}
    norm = normalize_plan_for_scaffolding(raw)
    assert norm == {"resolved": ["foo"], "missing": ["qux"]}


def test_normalize_plan_caps(monkeypatch):
    monkeypatch.setattr(
        "orchestrator_core.api.main.load_specs", lambda: {"cap_a": {}}
    )
    raw = {
        "used_capabilities": ["cap_a"],
        "missing_capabilities": ["cap_b"],
    }
    norm = normalize_plan_for_scaffolding(raw)
    assert norm == {"resolved": ["cap_a"], "missing": ["cap_b"]}
