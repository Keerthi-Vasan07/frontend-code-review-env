import os
import time
from typing import List

from openai import OpenAI

from env import FrontendCodeReviewEnv
from models import Action
from tasks import ALL_TASKS

# ─────────────────────────────────────────────────────────────
# ENV VARIABLES (MANDATORY)
# ─────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
HF_TOKEN = os.getenv("HF_TOKEN")

# ─────────────────────────────────────────────────────────────
# CLIENT SETUP
# ─────────────────────────────────────────────────────────────

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# ─────────────────────────────────────────────────────────────
# GENERATE CODE USING OPENAI CLIENT
# ─────────────────────────────────────────────────────────────

def generate_code(prompt: str) -> str:
    if not HF_TOKEN:
        return "<div>Fallback</div>"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are an expert frontend developer. Generate accurate HTML/CSS code that satisfies the given task requirements exactly. Return only code."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

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

        prompt = f"""
Task:
{obs.task_description}

Instructions:
- Solve the task exactly as described
- Include all required HTML elements
- Add CSS only if needed
- Do not skip required components
- Do not add unnecessary features
- Ensure correctness over styling

Return only HTML/CSS.
"""
        code = generate_code(prompt)

        action = Action(code=code)
        _, reward, done, info = env.step(action)

        # Single retry on zero-score to recover from bad generation
        if reward == 0:
            env.reset()  # episode is single-step; must reset before retrying
            code = generate_code(prompt)
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
