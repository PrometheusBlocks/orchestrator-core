import json

# Import the module containing the function to be tested and potentially mocked
from orchestrator_core.catalog import index, github_client
from pathlib import Path


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
            "name": "qux-1.0.0",
            "version": "1.0.0",
            "description": "qux v1",
        },  # Test filename parsing
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
        file_path = registry_dir / f"{spec['name']}-{spec['version']}.json"
        # Only write files for specs that have valid version strings in this test setup
        # (or specifically test invalid versions)
        if spec["name"] != "corge":  # Skip corge as it's handled separately above
            file_path.write_text(json.dumps(spec))

    # Override HOME to use the fake home directory
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Mock the GitHub fetch function to prevent network calls and interference
    # Ensure it returns an empty dict so only local specs are considered
    monkeypatch.setattr(index, "fetch_github_specs", lambda: {})

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
    assert result["qux"]["version"] == "1.0.0"
    assert "baz" not in result  # Should be skipped due to invalid version in filename
    assert "invalid_json" not in result  # Should be skipped due to JSONDecodeError
    assert (
        "corge" not in result
    )  # Should be skipped due to missing hyphen in filename stem
