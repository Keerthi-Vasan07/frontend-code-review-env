import os
from typing import List

from huggingface_hub import InferenceClient

from env import FrontendEnv
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
    if isinstance(task, dict):
        task_id = task.get("task_id", "unknown")
        task_description = task.get("task_description", "")
    else:
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
        # Create a fresh env per task, reset to get the first task
        env = FrontendEnv()
        obs = env.reset()

        # obs is a plain dict: {task_id, task_description, difficulty}
        task_dict = {
            "task_id": obs["task_id"],
            "task_description": obs["task_description"],
        }
        code = generate_code(task_dict)

        # step() accepts a plain code string and returns a plain dict
        step_result = env.step(code)
        reward = step_result["reward"]
        done = step_result["done"]
        info = step_result["info"]

        result = {
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            "reward": reward,
            "details": info,
        }

        results.append(result)

        print("[STEP]")
        print(f"task_id={obs['task_id']}")
        print(f"difficulty={obs['difficulty']}")
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
