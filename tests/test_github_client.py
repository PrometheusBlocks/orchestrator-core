import base64
import json
import pytest
import requests

from orchestrator_core.catalog.github_client import fetch_github_specs, session


class DummyResponse:
    def __init__(self, data, headers=None, status_code=200):
        self._data = data
        self.headers = headers or {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")

    def json(self):
        return self._data


def test_fetch_github_specs_via_search(monkeypatch):
    # Prepare a valid utility contract spec
    spec = {
        "name": "foo",
        "version": "1.0.0",
        "language": "python",
        "description": "Foo utility",
        "entrypoints": [
            {
                "name": "run",
                "description": "Run foo",
                "parameters_schema": {},
                "return_schema": {},
            }
        ],
    }
    # Base64-encoded content for the utility_contract.json
    encoded_content = base64.b64encode(json.dumps(spec).encode()).decode()

    def fake_get(url, headers=None):
        # Simulate search API response
        if url.startswith("https://api.github.com/search/code"):
            return DummyResponse(
                {
                    "items": [
                        {
                            "url": "https://api.github.com/repos/org/repo/contents/utility_contract.json"
                        }
                    ]
                },
                {},
            )
        # Simulate fetching the file content
        if url.endswith("utility_contract.json"):
            return DummyResponse({"encoding": "base64", "content": encoded_content}, {})
        pytest.skip(f"Unexpected URL called: {url}")

    # Monkey-patch the session.get method
    monkeypatch.setattr(session, "get", fake_get)

    specs = fetch_github_specs(org="org", token="token")
    assert isinstance(specs, dict)
    assert "foo" in specs
    assert specs["foo"]["version"] == "1.0.0"


def test_fetch_github_specs_fallback_on_search_error(monkeypatch):
    # Prepare a valid utility contract spec for fallback
    spec = {
        "name": "bar",
        "version": "2.0.0",
        "language": "python",
        "description": "Bar utility",
        "entrypoints": [
            {
                "name": "execute",
                "description": "Execute bar",
                "parameters_schema": {},
                "return_schema": {},
            }
        ],
    }
    encoded_content = base64.b64encode(json.dumps(spec).encode()).decode()

    def fake_get(url, headers=None):
        # Simulate search API failure
        if url.startswith("https://api.github.com/search/code"):
            raise requests.exceptions.RequestException("Search failed")
        # Simulate listing repos
        if url.startswith("https://api.github.com/orgs/org/repos"):
            # No pagination link
            return DummyResponse([{"name": "repo1"}], {"Link": ""})
        # Simulate fetching utility_contract.json from repo contents
        if url.endswith("repo1/contents/utility_contract.json"):
            return DummyResponse({"encoding": "base64", "content": encoded_content}, {})
        pytest.skip(f"Unexpected URL called: {url}")

    monkeypatch.setattr(session, "get", fake_get)
    specs = fetch_github_specs(org="org", token=None)
    assert isinstance(specs, dict)
    assert "bar" in specs
    assert specs["bar"]["version"] == "2.0.0"


def test_fetch_github_specs_skips_large_size_budget(monkeypatch):
    # Prepare a spec exceeding MAX_UTILITY_TOKENS
    from contracts.utility_contract import MAX_UTILITY_TOKENS

    spec = {
        "name": "big",
        "version": "1.0.0",
        "language": "python",
        "description": "Big utility",
        "size_budget": MAX_UTILITY_TOKENS + 1,
        "entrypoints": [
            {
                "name": "run",
                "description": "Run big",
                "parameters_schema": {},
                "return_schema": {},
            }
        ],
    }
    encoded_content = base64.b64encode(json.dumps(spec).encode()).decode()

    def fake_get(url, headers=None):
        if url.startswith("https://api.github.com/search/code"):
            return DummyResponse(
                {
                    "items": [
                        {
                            "url": "https://api.github.com/repos/org/repo/contents/utility_contract.json"
                        }
                    ]
                },
                {},
            )
        if url.endswith("utility_contract.json"):
            return DummyResponse({"encoding": "base64", "content": encoded_content}, {})
        pytest.skip(f"Unexpected URL called: {url}")

    monkeypatch.setattr(session, "get", fake_get)
    specs = fetch_github_specs(org="org", token="token")
    # The spec should be skipped due to size_budget
    assert "big" not in specs
