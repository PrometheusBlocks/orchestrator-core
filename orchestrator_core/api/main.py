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
