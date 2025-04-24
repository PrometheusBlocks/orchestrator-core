from fastapi import FastAPI

app = FastAPI()


@app.post("/plan")
def plan(payload: dict):
    return {"plan": "stub"}
