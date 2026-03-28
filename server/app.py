from fastapi import FastAPI
from env import FrontendCodeReviewEnv
from models import Action
import uvicorn

app = FastAPI()
env = FrontendCodeReviewEnv()

@app.get("/")
def root():
    return {"message": "Frontend Code Review Environment Running"}

@app.post("/run")
def run_env(code: str):
    obs = env.reset()
    action = Action(code=code)
    obs, reward, done, info = env.step(action)

    return {
        "reward": reward,
        "info": info,
        "done": done
    }

# REQUIRED: entrypoint for OpenEnv
def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

# REQUIRED: callable check
if __name__ == "__main__":
    main()
