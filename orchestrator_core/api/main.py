from fastapi import FastAPI, HTTPException

app = FastAPI()


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
        if not isinstance(plan, dict):
            raise HTTPException(
                status_code=400, detail="Invalid 'plan' provided; must be a dict."
            )
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
    # Perform scaffolding
    from pathlib import Path
    from orchestrator_core.executor.scaffolder import scaffold_project

    try:
        base_path = Path(output_dir)
        project_path = scaffold_project(plan, base_path, project_name, template_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scaffolding project: {e}")
    return {"project_path": str(project_path)}
