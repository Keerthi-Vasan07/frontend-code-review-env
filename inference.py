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
        print("[WARN] No API key found. Using fallback.")
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

        except Exception as e:
            wait_time = 2 ** attempt
            print(f"[WARN] API error: {e}, retrying in {wait_time}s...")
            time.sleep(wait_time)

    print("[ERROR] API failed. Using fallback.")
    return "<div>Fallback response</div>"

# ─────────────────────────────────────────────────────────────
# RUN EVALUATION
# ─────────────────────────────────────────────────────────────

def run_all_tasks():
    results = []

    print("\n================= EVALUATION START =================\n")

    for task in ALL_TASKS:
        print(f"Task: {task.task_id} ({task.difficulty})")

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

        print(f"Reward: {reward:.3f}")
        print("-" * 40)

    return results

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_all_tasks()

    print("\n================= FINAL RESULTS =================\n")

    for r in results:
        print(f"{r['task_id']} | {r['difficulty']} | {r['reward']:.3f}")
