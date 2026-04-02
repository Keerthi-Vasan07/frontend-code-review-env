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
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# ─────────────────────────────────────────────────────────────
# CLIENT SETUP
# ─────────────────────────────────────────────────────────────

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY or "dummy_key",
)

# ─────────────────────────────────────────────────────────────
# SAFE GENERATION FUNCTION
# ─────────────────────────────────────────────────────────────

def generate_code(prompt: str, max_retries: int = 3) -> str:
    if not API_KEY:
        return "<div>Fallback response</div>"

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Generate ONLY HTML/CSS code. No explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=300
            )

            output = response.choices[0].message.content.strip()

            if "<" not in output:
                return "<div>Invalid output</div>"

            return output

        except Exception:
            wait_time = 2 ** attempt
            time.sleep(wait_time)

    return "<div>Fallback response</div>"

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

        code = generate_code(obs.task_description)

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
