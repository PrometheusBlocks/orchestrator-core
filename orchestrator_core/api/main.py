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
    from orchestrator_core.planner import make_plan

    return make_plan(prompt)
