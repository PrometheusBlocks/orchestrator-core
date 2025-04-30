import json
from pathlib import Path
from typing import Dict

from packaging.version import InvalidVersion, Version


def load_specs() -> Dict[str, dict]:
    """
    Load all specs from ~/.pb_registry/*.json and return a mapping of name to spec dict,
    keeping only the highest semver version for each name.
    """
    registry_dir = Path.home() / ".pb_registry"
    specs: Dict[str, dict] = {}
    for file in registry_dir.glob("*.json"):
        stem = file.stem
        if "-" not in stem:
            continue
        name, version_str = stem.rsplit("-", 1)
        try:
            version = Version(version_str)
        except InvalidVersion:
            continue
        try:
            data = json.loads(file.read_text())
        except json.JSONDecodeError:
            continue
        # Ensure the spec dict has a version field
        if "version" not in data:
            data["version"] = version_str
        if name in specs:
            try:
                current_version = Version(specs[name]["version"])
            except InvalidVersion:
                current_version = None
            if current_version is not None and version <= current_version:
                continue
        specs[name] = data
    # Attempt to fetch additional specs from GitHub and merge, keeping highest versions
    try:
        from .github_client import fetch_github_specs

        remote_specs = fetch_github_specs()
        for name, spec in remote_specs.items():
            # Ensure spec has a version
            ver_str = spec.get("version")
            if not ver_str:
                continue
            try:
                remote_ver = Version(ver_str)
            except InvalidVersion:
                continue
            # Compare with local spec
            if name in specs:
                try:
                    local_ver = Version(specs[name].get("version", ""))
                except InvalidVersion:
                    local_ver = None
                if local_ver is not None and remote_ver <= local_ver:
                    continue
            specs[name] = spec
    except Exception:
        # If GitHub integration fails, proceed with local specs only
        pass
    return specs
