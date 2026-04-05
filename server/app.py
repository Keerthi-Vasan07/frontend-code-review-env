from fastapi import FastAPI
from pydantic import BaseModel
from env import FrontendCodeReviewEnv
from models import Action
import uvicorn

app = FastAPI()

env = FrontendCodeReviewEnv()
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
    return {
        "status": "running"
    }

@app.get("/")
def root():
    return {"status": "running", "message": "Frontend Code Review Env is live"}

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
