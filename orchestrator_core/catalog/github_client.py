"""
GitHub client for fetching utility specs from the PrometheusBlocks organization.
"""

import os
import json
import base64
import urllib.parse
import logging
import requests
from typing import Dict, Optional

from packaging.version import Version, InvalidVersion
from contracts.utility_contract import UtilityContract, MAX_UTILITY_TOKENS

# Module logger; application should configure handlers/levels as desired
logger = logging.getLogger(__name__)
# HTTP session for GitHub API requests
session = requests.Session()


def fetch_github_specs(
    org: str = "PrometheusBlocks", token: Optional[str] = None
) -> Dict[str, dict]:
    """
    Discover and return utility specs from public GitHub repos in the given org.
    Looks for files named 'utility_contract.json' in any path; falls back to checking each repo root.
    Returns a mapping of utility name to spec dict, keeping only the highest semver per utility.
    """
    # Prepare authentication and headers
    if token is None:
        token = os.getenv("GITHUB_TOKEN")
    headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    def _get_json(url: str):  # -> (data, headers)
        # Perform GET request and return parsed JSON and response headers
        resp = session.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data, resp.headers

    specs: Dict[str, dict] = {}

    # 1) Try GitHub Search API to find any utility_contract.json files
    query = f"filename:utility_contract.json org:{org}"
    search_url = (
        f"https://api.github.com/search/code?q={urllib.parse.quote(query)}&per_page=100"
    )
    try:
        search_data, _ = _get_json(search_url)
        items = search_data.get("items", []) if isinstance(search_data, dict) else []
    except Exception:
        items = []
    # Fetch and validate each search hit
    for item in items:
        content_url = item.get("url")
        if not content_url:
            continue
        try:
            file_data, _ = _get_json(content_url)
        except Exception:
            continue
        # Expect base64-encoded JSON content
        if file_data.get("encoding") != "base64" or not file_data.get("content"):
            continue
        try:
            raw = base64.b64decode(file_data["content"]).decode("utf-8")
            spec_json = json.loads(raw)
            spec = UtilityContract(**spec_json)
        except Exception:
            continue
        if spec.size_budget > MAX_UTILITY_TOKENS:
            continue
        try:
            ver = Version(spec.version)
        except InvalidVersion:
            continue
        existing = specs.get(spec.name)
        if existing:
            try:
                curr_ver = Version(existing.get("version", ""))
            except InvalidVersion:
                curr_ver = None
            if curr_ver is not None and ver <= curr_ver:
                continue
        specs[spec.name] = spec.model_dump()

    # 2) Fallback: attempt to fetch utility_contract.json from each repo root
    if not specs:
        repos: list = []
        repos_url = f"https://api.github.com/orgs/{org}/repos?per_page=100&type=public"
        while repos_url:
            try:
                page, headers = _get_json(repos_url)
                if isinstance(page, list):
                    repos.extend(page)
                # parse pagination
                link = headers.get("Link", "")
                repos_url = None
                for part in link.split(","):
                    if 'rel="next"' in part:
                        repos_url = part.split(";")[0].strip().strip("<>")
                        break
            except Exception:
                break
        for repo in repos:
            name = repo.get("name")
            if not name:
                continue
            content_url = f"https://api.github.com/repos/{org}/{name}/contents/utility_contract.json"
            try:
                file_data, _ = _get_json(content_url)
            except Exception:
                continue
            if file_data.get("encoding") != "base64" or not file_data.get("content"):
                continue
            try:
                raw = base64.b64decode(file_data["content"]).decode("utf-8")
                spec_json = json.loads(raw)
                spec = UtilityContract(**spec_json)
            except Exception:
                continue
            if spec.size_budget > MAX_UTILITY_TOKENS:
                continue
            try:
                ver = Version(spec.version)
            except InvalidVersion:
                continue
            existing = specs.get(spec.name)
            if existing:
                try:
                    curr_ver = Version(existing.get("version", ""))
                except InvalidVersion:
                    curr_ver = None
                if curr_ver is not None and ver <= curr_ver:
                    continue
            specs[spec.name] = spec.model_dump()

    return specs
