import os
import time
from typing import List

from huggingface_hub import InferenceClient

from env import FrontendCodeReviewEnv
from models import Action
from tasks import ALL_TASKS

# ─────────────────────────────────────────────────────────────
# ENV VARIABLES (MANDATORY)
# ─────────────────────────────────────────────────────────────

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# ─────────────────────────────────────────────────────────────
# CLIENT SETUP (Hugging Face)
# ─────────────────────────────────────────────────────────────

client = InferenceClient(
    model=MODEL_NAME,
    token=os.getenv("HF_TOKEN")
)

# ─────────────────────────────────────────────────────────────
# GENERATE CODE USING HF INFERENCE CLIENT
# ─────────────────────────────────────────────────────────────

def generate_code(task) -> str:
    """Generate HTML/CSS code for the given task dict using HF InferenceClient.

    Accepts either a task dict (with keys 'task_id' and 'task_description')
    or a plain prompt string for backwards compatibility.
    Always returns some output — falls back gracefully on any error.
    """
    # Support both a task dict and a raw prompt string
    if isinstance(task, dict):
        task_id = task.get("task_id", "unknown")
        task_description = task.get("task_description", "")
    else:
        # Plain prompt string passed in (e.g. from run_all_tasks legacy path)
        task_id = "unknown"
        task_description = str(task)

    prompt = f"""
    Generate HTML/CSS code for the following task:

    Task: {task_description}

    Requirements:
    - Code must be valid HTML/CSS
    - Include relevant elements
    - Make output different for different tasks
    """

    try:
        response = client.text_generation(
            prompt,
            max_new_tokens=300,
            temperature=0.7
        )
        return response
    except Exception:
        return f"<div>Fallback content for {task_id}</div>"

# ─────────────────────────────────────────────────────────────
# RUN EVALUATION
# ─────────────────────────────────────────────────────────────

def run_all_tasks():
    results = []

    print("[START]")
    print(f"total_tasks={len(ALL_TASKS)}")
    print(f"model={MODEL_NAME}")

    for task in ALL_TASKS:
        env = FrontendCodeReviewEnv(task_id=task.task_id)
        obs = env.reset()

        task_dict = {
            "task_id": task.task_id,
            "task_description": obs.task_description,
        }
        code = generate_code(task_dict)

        action = Action(code=code)
        _, reward, done, info = env.step(action)

        # Single retry on zero-score to recover from bad generation
        if reward == 0:
            env.reset()  # episode is single-step; must reset before retrying
            code = generate_code(task_dict)
            action = Action(code=code)
            _, reward, done, info = env.step(action)

        result = {
            "task_id": task.task_id,
            "difficulty": task.difficulty.value,
            "reward": reward,
            "details": info
        }

        results.append(result)

        print("[STEP]")
        print(f"task_id={task.task_id}")
        print(f"difficulty={task.difficulty.value}")
        print(f"reward={reward}")
        print(f"structure_score={info.get('structure_score', 0.0)}")
        print(f"style_score={info.get('style_score', 0.0)}")
        print(f"responsiveness_score={info.get('responsiveness_score', 0.0)}")
        print(f"accessibility_score={info.get('accessibility_score', 0.0)}")
        print(f"code_quality_score={info.get('code_quality_score', 0.0)}")
        print(f"penalties={info.get('penalties', 0.0)}")
        print(f"done={str(done).lower()}")

    return results

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_all_tasks()

    avg_reward = sum(r["reward"] for r in results) / len(results) if results else 0.0

    print("[END]")
    print(f"total_tasks={len(results)}")
    print(f"average_reward={avg_reward}")
