from fastapi import FastAPI
from pydantic import BaseModel
from env import FrontendCodeReviewEnv as FrontendEnv
from models import Action

app = FastAPI()

env = FrontendEnv()
obs = None

class StepRequest(BaseModel):
    code: str

@app.post("/reset")
def reset():
    global obs
    obs = env.reset()
    return {
        "task_id": env.current_task.task_id,
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
