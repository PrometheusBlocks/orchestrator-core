import json
from pathlib import Path

# Import the module containing the function to be tested
from orchestrator_core.catalog import index

# We don't need to import github_client directly,
# but we need its full path for monkeypatching


def test_load_specs(tmp_path, monkeypatch):
    # Set up a fake home directory with a .pb_registry
    fake_home = tmp_path / "home"
    registry_dir = fake_home / ".pb_registry"
    registry_dir.mkdir(parents=True)

    # Create fake spec files
    specs_data = [
        {"name": "foo", "version": "1.0.0", "description": "foo v1"},
        {"name": "foo", "version": "1.2.0", "description": "foo v1.2"},
        {"name": "bar", "version": "0.5.0", "description": "bar v0.5"},
        {
            "name": "baz",
            "version": "invalid-version",
            "description": "baz invalid",
        },  # Should be skipped
        {
            "name": "qux",  # Corrected name to match expected key
            "version": "1.0.0",
            "description": "qux v1",
        },  # Test filename parsing (filename will be qux-1.0.0.json)
        {
            "name": "corge",
            "version": "1.0",
        },  # No hyphen in filename stem, should be skipped if named corge.json
    ]
    # Create a file with invalid JSON
    (registry_dir / "invalid_json-1.0.0.json").write_text("{invalid json")
    # Create a file with missing version in filename stem (will be skipped)
    (registry_dir / "corge.json").write_text(
        json.dumps({"name": "corge", "version": "1.0"})
    )

    for spec in specs_data:
        # Use the name and version from the spec dict for the filename
        # For qux, this will now create qux-1.0.0.json
        file_path = registry_dir / f"{spec['name']}-{spec['version']}.json"
        # Only write files for specs that have valid version strings in this test setup
        # (or specifically test invalid versions)
        if spec["name"] != "corge":  # Skip corge as it's handled separately above
            file_path.write_text(json.dumps(spec))

    # Override HOME to use the fake home directory
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Mock the GitHub fetch function where it's defined/imported from
    # The 'load_specs' function imports 'fetch_github_specs' from '.github_client',
    # so we need to patch it in the 'github_client' module.
    monkeypatch.setattr(
        "orchestrator_core.catalog.github_client.fetch_github_specs", lambda: {}
    )

    result = index.load_specs()

    # Debugging output (optional)
    # print("Result:", result)

    assert isinstance(result, dict)
    # Expected: foo (highest version), bar, qux
    assert len(result) == 3, f"Expected 3 specs, got {len(result)}: {result.keys()}"
    assert "foo" in result
    assert result["foo"]["version"] == "1.2.0"
    assert "bar" in result
    assert result["bar"]["version"] == "0.5.0"
    assert "qux" in result  # Check if qux-1.0.0.json was parsed correctly
    assert result["qux"]["version"] == "1.0.0"  # Check the version loaded for qux
    assert "baz" not in result  # Should be skipped due to invalid version in filename
    assert "invalid_json" not in result  # Should be skipped due to JSONDecodeError
    assert (
        "corge" not in result
    )  # Should be skipped due to missing hyphen in filename stem


def test_load_specs_preserves_source_url(tmp_path, monkeypatch):
    # No local specs, remote spec includes source URL
    fake_home = tmp_path / "home2"
    registry_dir = fake_home / ".pb_registry"
    registry_dir.mkdir(parents=True)
    # Override HOME
    from pathlib import Path as _Path

    monkeypatch.setattr(_Path, "home", lambda: fake_home)
    url = "https://github.com/org/utilx"
    # Mock fetch_github_specs to return a spec with source URL
    remote_spec = {
        "utilx": {
            "name": "utilx",
            "version": "1.0.0",
            "description": "x",
            "_source_repository_url_discovered": url,
        }
    }
    monkeypatch.setattr(
        "orchestrator_core.catalog.github_client.fetch_github_specs",
        lambda: remote_spec,
    )
    # Now load specs
    from orchestrator_core.catalog import index

    result = index.load_specs()
    assert "utilx" in result
    spec = result["utilx"]
    assert spec.get("version") == "1.0.0"
    # Source URL preserved
    assert spec.get("_source_repository_url_discovered") == url
