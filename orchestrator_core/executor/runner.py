import io
import importlib
import logging
import subprocess
import sys
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result from executing a utility entrypoint."""

    return_value: Any
    stdout: str
    stderr: str


def _venv_bin(venv_dir: Path, name: str) -> Path:
    """Return the path to an executable inside a venv."""
    subdir = "Scripts" if sys.platform.startswith("win") else "bin"
    return venv_dir / subdir / name


def create_virtualenv(venv_dir: Path) -> None:
    """Create a virtual environment at the given path."""
    logger.info("Creating virtual environment at %s", venv_dir)
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)


def install_requirements(venv_dir: Path, requirements: Path) -> None:
    """Install requirements from a file into the provided venv."""
    pip = _venv_bin(venv_dir, "pip")
    logger.info("Installing requirements from %s", requirements)
    subprocess.run([str(pip), "install", "-r", str(requirements)], check=True)


def prepare_environment(project_dir: Path) -> Path:
    """Ensure a virtual environment exists and install utility requirements."""
    venv_dir = project_dir / "venv"
    if not venv_dir.exists():
        create_virtualenv(venv_dir)
    for util_dir in project_dir.iterdir():
        if not util_dir.is_dir() or util_dir.name == "venv":
            continue
        req_file = util_dir / "requirements.txt"
        if req_file.exists():
            install_requirements(venv_dir, req_file)
    return venv_dir


def execute_utility(
    project_dir: Path, utility: str, entrypoint: str, params: Dict[str, Any]
) -> ExecutionResult:
    """Execute an entrypoint for a single utility within a project."""
    prepare_environment(project_dir)
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    try:
        module = importlib.import_module(utility)
        func = getattr(module, entrypoint)
    except Exception as exc:  # pragma: no cover - import errors handled
        raise RuntimeError(
            f"Failed to load entrypoint '{entrypoint}' from utility '{utility}': {exc}"
        ) from exc
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        result = func(**params)
    return ExecutionResult(
        return_value=result, stdout=stdout_buf.getvalue(), stderr=stderr_buf.getvalue()
    )
