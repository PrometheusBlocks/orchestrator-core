from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Any, Dict

from orchestrator_core.catalog.index import load_specs

WEBUI_DIR = Path(__file__).resolve().parents[2] / "webui"

app = FastAPI()


def normalize_plan_for_scaffolding(raw_plan: Any) -> Dict[str, list]:
    """Convert various plan formats into a scaffolding-friendly dict.

    The scaffolder expects a ``{"resolved": [...], "missing": [...]}`` layout. This
    helper accepts execution plans returned by the planner or provided by the
    user and extracts the needed lists.
    """

    specs = load_specs()

    if isinstance(raw_plan, list):
        actions = [
            step.get("action")
            for step in raw_plan
            if isinstance(step, dict) and "action" in step
        ]
        resolved = [a for a in actions if a in specs]
        missing = [a for a in actions if a not in specs]
        return {"resolved": resolved, "missing": missing}

    if isinstance(raw_plan, dict):
        if "resolved" in raw_plan or "missing" in raw_plan:
            return {
                "resolved": list(raw_plan.get("resolved", [])),
                "missing": list(raw_plan.get("missing", [])),
            }

        if "proposed_utilities" in raw_plan:
            utilities = [
                item.get("name")
                for item in raw_plan.get("proposed_utilities", [])
                if isinstance(item, dict) and item.get("name")
            ]
            resolved = [u for u in utilities if u in specs]
            missing = [u for u in utilities if u not in specs]
            return {"resolved": resolved, "missing": missing}

        if "used_capabilities" in raw_plan or "missing_capabilities" in raw_plan:
            used = [
                cap.get("name") if isinstance(cap, dict) else cap
                for cap in raw_plan.get("used_capabilities", [])
                if isinstance(cap, (str, dict))
            ]
            miss = [
                cap.get("name") if isinstance(cap, dict) else cap
                for cap in raw_plan.get("missing_capabilities", [])
                if isinstance(cap, (str, dict))
            ]
            resolved = [u for u in used if u in specs]
            missing = [u for u in miss if u not in specs or u not in resolved]
            return {"resolved": resolved, "missing": missing}

    raise HTTPException(status_code=400, detail="Invalid plan format")


@app.get("/")
def serve_webui():
    """Serve the Web UI index page."""
    index_file = WEBUI_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web UI not found")
    return FileResponse(index_file)


@app.post("/plan")
def plan(payload: dict):
    """Create a plan based on the given prompt."""
    prompt = payload.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(
            status_code=400, detail="Missing or invalid 'prompt' in payload"
        )
    # Use LLM-based planner for structured execution plan
    from orchestrator_core.planner.parser import prompt_to_plan

    return prompt_to_plan(prompt)


@app.post("/scaffold_project")
def scaffold_project_endpoint(payload: dict):
    """Create or clone utilities based on a plan or prompt, scaffold a project."""
    # Determine plan: either provided or via prompt
    plan = None
    if payload.get("plan") is not None:
        plan = payload.get("plan")
        # plan may be any format; normalize below
    elif payload.get("prompt") is not None:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise HTTPException(
                status_code=400,
                detail="Invalid 'prompt' provided; must be a non-empty string.",
            )
        from orchestrator_core.planner.parser import prompt_to_plan

        plan = prompt_to_plan(prompt)
    else:
        raise HTTPException(
            status_code=400,
            detail="Request must include either 'plan' (dict) or 'prompt' (str).",
        )
    # Project name and output directory
    project_name = payload.get("project_name")
    if not project_name or not isinstance(project_name, str):
        project_name = "scaffolded_project"
    output_dir = payload.get("output_base_dir")
    if not output_dir or not isinstance(output_dir, str):
        output_dir = "."
    template_url = payload.get("template_url")
    if not template_url or not isinstance(template_url, str):
        template_url = "https://github.com/PrometheusBlocks/block-template.git"
    create_repos = bool(payload.get("create_github_repos"))
    github_org = payload.get("github_org")
    # Perform scaffolding
    from pathlib import Path
    from orchestrator_core.executor.scaffolder import scaffold_project

    try:
        base_path = Path(output_dir)
        if plan is None:
            raise ValueError("Plan not provided")
        normalized = normalize_plan_for_scaffolding(plan)
        project_path = scaffold_project(
            normalized,
            base_path,
            project_name,
            template_url,
            create_github_repos=create_repos,
            github_org=github_org,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scaffolding project: {e}")
    return {"project_path": str(project_path)}


@app.get("/utility/{name}")
def get_utility_contract(name: str):
    """Return the contract for a named utility.

    Parameters
    ----------
    name: str
        Name of the utility contract to retrieve.
    """
    from orchestrator_core.catalog.index import load_specs

    specs = load_specs()
    spec = specs.get(name)
    if spec is None:
        raise HTTPException(status_code=404, detail="Utility not found")
    return spec
