"""Legacy fallback planner: keyword-based plan maker.
Superseded by LLM-based planning via parser.prompt_to_plan."""

import json
import datetime
import yaml
from pathlib import Path

from .parser import prompt_to_capabilities
from orchestrator_core.catalog.index import load_specs


def make_plan(prompt: str) -> dict:
    """
    Build a plan dict with:
      - prompt: original prompt
      - resolved: list of core capabilities that exist
      - missing: list of domain-specific capabilities that are not yet implemented
    Writes the plan to ~/plans/<timestamp>-plan.json.
    """
    # Extract capabilities from prompt
    capabilities = prompt_to_capabilities(prompt)
    # Load core capabilities from keywords.yml
    base_dir = Path(__file__).parent
    keywords_file = base_dir / "keywords.yml"
    core_caps: set[str] = set()
    try:
        data = yaml.safe_load(keywords_file.read_text())
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    core_caps.update(v)
    except Exception:
        pass
    # Load existing specs
    try:
        specs = load_specs()
    except Exception:
        specs = {}
    # Classify capabilities
    resolved: list[str] = []
    missing: list[str] = []
    for cap in capabilities:
        if cap in specs or cap in core_caps:
            resolved.append(cap)
        else:
            missing.append(cap)
    plan = {"prompt": prompt, "resolved": resolved, "missing": missing}
    # Write plan to ~/plans/<timestamp>-plan.json
    plans_dir = Path.home() / "plans"
    # Attempt to write plan file under user's home; skip on permission errors
    try:
        plans_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        plan_file = plans_dir / f"{timestamp}-plan.json"
        plan_file.write_text(json.dumps(plan, indent=2))
    except Exception:
        pass
    return plan
