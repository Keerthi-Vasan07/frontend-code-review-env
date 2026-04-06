from fastapi import FastAPI
from pydantic import BaseModel
from env import FrontendEnv
from models import Action

app = FastAPI()

env = FrontendEnv()
obs = None

class StepRequest(BaseModel):
    code: str

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/reset")
def reset():
    global obs
    obs = env.reset()
    return {
        "task_id": obs.task_id,
        "task_description": obs.task_description
    }

@app.post("/step")
def step(req: StepRequest):
    global obs
    action = Action(code=req.code)
    obs, reward, done, info = env.step(action)

    return {
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    return {"status": "running"}
