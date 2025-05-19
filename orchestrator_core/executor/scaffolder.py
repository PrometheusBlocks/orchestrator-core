"""
Scaffolder module: provides functions to clone repositories, customize templates for new utilities,
and scaffold entire projects based on a plan.json.
"""

import logging
import subprocess
import shutil
import json
import os
from pathlib import Path
from typing import Optional
import requests

from orchestrator_core.catalog.index import load_specs

logger = logging.getLogger(__name__)


def clone_repository(
    repo_url: str, target_dir: Path, branch: Optional[str] = None
) -> bool:
    """
    Clone the given repository URL into target_dir. Optionally specify a branch.
    Removes the .git directory after cloning. Returns True on success, False otherwise.
    """
    try:
        args = ["git", "clone"]
        if branch:
            args += ["--branch", branch]
        args += [repo_url, str(target_dir)]
        logger.info(f"Cloning repository {repo_url} into {target_dir}")
        subprocess.run(args, check=True)
        git_dir = target_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository {repo_url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during cloning {repo_url}: {e}")
        return False


def init_git_repo(repo_dir: Path) -> bool:
    """Initialize a git repository in the given directory."""
    try:
        subprocess.run(["git", "init"], cwd=repo_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize git repo in {repo_dir}: {e}")
        return False
    except Exception as e:  # pragma: no cover - unexpected errors
        logger.error(f"Unexpected error during git init in {repo_dir}: {e}")
        return False


def create_github_repository(
    name: str, private: bool = False, org: Optional[str] = None, token: Optional[str] = None
) -> Optional[str]:
    """Create a GitHub repository and return its clone URL if successful."""

    if token is None:
        token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning(
            "GITHUB_TOKEN not provided; skipping creation of GitHub repo '%s'", name
        )
        return None

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {"name": name, "private": private}
    if org:
        url = f"https://api.github.com/orgs/{org}/repos"
    else:
        url = "https://api.github.com/user/repos"

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code not in (201, 200):
            logger.error(
                "Failed to create GitHub repo '%s': %s %s",
                name,
                resp.status_code,
                resp.text,
            )
            return None
        data = resp.json()
        return data.get("clone_url")
    except Exception as e:  # pragma: no cover - network errors
        logger.error("Error creating GitHub repo '%s': %s", name, e)
        return None


def push_repo_to_remote(repo_dir: Path, remote_url: str) -> bool:
    """Push the given git repo to the specified remote URL."""

    try:
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=repo_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial scaffold"], cwd=repo_dir, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=repo_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            "Failed to push repository '%s' to %s: %s", repo_dir, remote_url, e
        )
        return False
    except Exception as e:  # pragma: no cover - unexpected errors
        logger.error(
            "Unexpected error pushing repository '%s' to %s: %s",
            repo_dir,
            remote_url,
            e,
        )
        return False


def customize_new_utility_from_template(
    template_dir: Path, new_utility_name: str, contract_data: Optional[dict] = None
):
    """
    Customize a generic block template in ``template_dir`` for a new utility named
    ``new_utility_name``.

    If ``contract_data`` is provided, it is written as ``utility_contract.json``;
    otherwise a minimal placeholder contract is created. All ``{{UTILITY_NAME}}``
    placeholders in the template files are replaced with ``new_utility_name``.
    """
    logger.info(
        f"Customizing template in {template_dir} for utility '{new_utility_name}'"
    )
    # Replace placeholders in all files
    for path in template_dir.rglob("*"):
        if path.is_file():
            try:
                content = path.read_text()
            except Exception:
                continue
            new_content = content.replace("{{UTILITY_NAME}}", new_utility_name)
            if new_content != content:
                try:
                    path.write_text(new_content)
                except Exception as e:
                    logger.warning(f"Could not write to {path}: {e}")
    # Generate utility_contract.json
    contract = (
        contract_data
        if contract_data is not None
        else {
            "name": new_utility_name,
            "version": "0.1.0-dev",
            "language": "python",
            "description": f"Scaffolded utility: {new_utility_name}",
            "entrypoints": [
                {
                    "name": "run",
                    "description": "Default entry point",
                    "parameters_schema": {},
                    "return_schema": {},
                }
            ],
            "deps": [],
            "tests": [],
        }
    )
    contract_path = template_dir / "utility_contract.json"
    try:
        with contract_path.open("w") as f:
            json.dump(contract, f, indent=2)
        logger.info(f"Created placeholder utility_contract.json at {contract_path}")
    except Exception as e:
        logger.error(
            f"Failed to write placeholder utility_contract.json at {contract_path}: {e}"
        )


def scaffold_project(
    plan: dict,
    project_base_dir: Path,
    project_name: str,
    generic_block_template_url: str,
    *,
    create_github_repos: bool = False,
    github_org: Optional[str] = None,
    github_private: bool = False,
    github_token: Optional[str] = None,
) -> Path:
    """Scaffold a project directory based on the given plan.

    Resolved utilities are cloned from their source repositories. Missing
    utilities are created from the generic block template. If
    ``create_github_repos`` is ``True``, newly scaffolded utilities will also be
    pushed to freshly created GitHub repositories using ``github_token``.

    Returns the path to the main project directory.
    """
    logger.info(f"Starting scaffolding project '{project_name}' at {project_base_dir}")
    project_base_dir.mkdir(parents=True, exist_ok=True)
    main_project_path = project_base_dir / project_name
    if not main_project_path.exists():
        main_project_path.mkdir(parents=True)
    # Load all known specs
    all_specs = load_specs()
    # Map proposed utilities by name for easy lookup
    proposed_map = {
        u.get("name"): u
        for u in plan.get("proposed_utilities", [])
        if isinstance(u, dict) and u.get("name")
    }

    # Handle resolved utilities (clone existing repos)
    for util in plan.get("resolved", []):
        util_dir = main_project_path / util
        util_dir.mkdir(parents=True, exist_ok=True)
        spec_data = all_specs.get(util)
        if not spec_data:
            logger.error(
                f"Spec data not found for resolved utility '{util}'. Skipping."
            )
            continue
        repo_url = spec_data.get("_source_repository_url_discovered")
        branch = spec_data.get("_source_repository_branch_discovered")
        if not repo_url:
            logger.warning(
                f"Source repository URL not found for resolved utility '{util}'. Cannot clone. Skipping."
            )
            continue
        success = clone_repository(repo_url, util_dir, branch=branch)
        if not success:
            logger.error(f"Failed to clone resolved utility '{util}' from {repo_url}")
        else:
            logger.info(f"Successfully cloned resolved utility '{util}'")
            init_git_repo(util_dir)
    # Handle missing utilities (scaffold new)
    for util in plan.get("missing", []):
        util_dir = main_project_path / util
        util_dir.mkdir(parents=True, exist_ok=True)
        success = clone_repository(generic_block_template_url, util_dir)
        if not success:
            logger.error(
                f"Failed to scaffold missing utility '{util}' from template {generic_block_template_url}"
            )
            continue
        contract_data = proposed_map.get(util)
        customize_new_utility_from_template(util_dir, util, contract_data=contract_data)
        logger.info(f"Successfully scaffolded missing utility '{util}'")
        init_git_repo(util_dir)
        if create_github_repos:
            remote = create_github_repository(
                util, private=github_private, org=github_org, token=github_token
            )
            if remote:
                push_repo_to_remote(util_dir, remote)
    return main_project_path
