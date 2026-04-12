from fastapi import FastAPI
from pydantic import BaseModel

from env import FrontendEnv

app = FastAPI(title="frontend_code_review_env")

# Single shared environment instance — state persists across requests
env = FrontendEnv()


class StepInput(BaseModel):
    action: dict


# ── Required endpoints ──────────────────────────────────────────────────────

@app.post("/reset")
def reset():
    """Restart the episode. Response is the first task."""
    return env.reset()


@app.post("/step")
def step(data: StepInput):
    """Evaluate submitted action and advance the simulation."""
    return env.step(data.action)



# ── Diagnostic endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/state")
def state():
    return env.state()
