"""
Scaffolder module: provides functions to clone repositories, customize templates for new utilities,
and scaffold entire projects based on a plan.json.
"""

import logging
import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional

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


def customize_new_utility_from_template(template_dir: Path, new_utility_name: str):
    """
    Customize a generic block template in template_dir for a new utility named new_utility_name.
    Replaces placeholders and generates a placeholder utility_contract.json.
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
    # Generate placeholder utility_contract.json
    placeholder_contract = {
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
    contract_path = template_dir / "utility_contract.json"
    try:
        with contract_path.open("w") as f:
            json.dump(placeholder_contract, f, indent=2)
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
) -> Path:
    """
    Scaffold a project directory based on the given plan.
    Resolved utilities are cloned from their source repos; missing utilities are scaffolded
    from the generic block template URL.

    Returns the path to the main project directory.
    """
    logger.info(f"Starting scaffolding project '{project_name}' at {project_base_dir}")
    project_base_dir.mkdir(parents=True, exist_ok=True)
    main_project_path = project_base_dir / project_name
    if not main_project_path.exists():
        main_project_path.mkdir(parents=True)
    # Load all known specs
    all_specs = load_specs()
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
        customize_new_utility_from_template(util_dir, util)
        logger.info(f"Successfully scaffolded missing utility '{util}'")
    return main_project_path
