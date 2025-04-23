import json

from orchestrator_core.catalog.index import load_specs


def test_load_specs(tmp_path, monkeypatch):
    # Set up a fake home directory with a .pb_registry
    fake_home = tmp_path / "home"
    registry_dir = fake_home / ".pb_registry"
    registry_dir.mkdir(parents=True)

    # Create fake spec files
    specs = [
        {"name": "foo", "version": "1.0.0"},
        {"name": "foo", "version": "1.2.0"},
        {"name": "bar", "version": "0.5.0"},
    ]
    for spec in specs:
        file_path = registry_dir / f"{spec['name']}-{spec['version']}.json"
        file_path.write_text(json.dumps(spec))

    # Override HOME to use the fake home directory
    monkeypatch.setenv("HOME", str(fake_home))

    result = load_specs()
    assert isinstance(result, dict)
    assert len(result) == 2
    assert "foo" in result
    assert result["foo"]["version"] == "1.2.0"
    assert "bar" in result
    assert result["bar"]["version"] == "0.5.0"
