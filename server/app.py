from fastapi import FastAPI
from pydantic import BaseModel

from env import FrontendEnv

app = FastAPI(title="frontend_code_review_env")

# Single shared environment instance
env = FrontendEnv()


class StepInput(BaseModel):
    code: str


# ── Required endpoints ──────────────────────────────────────────────────────

@app.get("/reset")
def reset():
    """Start (or restart) the episode from task 0."""
    return env.reset()


@app.post("/step")
def step(data: StepInput):
    """Evaluate submitted code and advance to the next task."""
    return env.step(data.code)


# ── Optional / diagnostic endpoints ─────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/state")
def state():
    return env.state()
