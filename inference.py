import os

from huggingface_hub import InferenceClient

from env import FrontendEnv
from tasks import ALL_TASKS

# ─────────────────────────────────────────────────────────────
# ENV VARIABLES
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
# CODE GENERATION
# ─────────────────────────────────────────────────────────────

def generate_code(task: dict) -> str:
    """
    Generate HTML/CSS for the given task dict.
    Falls back to a task-specific stub on any error.
    """
    task_id = task.get("task_id", "unknown")
    task_description = task.get("task_description", "")

    prompt = f"""
    Generate HTML/CSS code for the following task:

    Task: {task_description}

    Requirements:
    - Code must be valid HTML/CSS
    - Include relevant elements
    - Make output different for different tasks
    """

    try:
        return client.text_generation(
            prompt,
            max_new_tokens=300,
            temperature=0.7,
        )
    except Exception:
        return f"<div>Fallback content for {task_id}</div>"

# ─────────────────────────────────────────────────────────────
# EVALUATION LOOP
# ─────────────────────────────────────────────────────────────

def run_all_tasks():
    results = []

    print("[START]")
    print(f"total_tasks={len(ALL_TASKS)}")
    print(f"model={MODEL_NAME}")

    # Single env instance — tasks progress sequentially via internal index
    env = FrontendEnv()
    obs = env.reset()

    for _ in range(len(ALL_TASKS)):
        task_dict = {
            "task_id": obs["task_id"],
            "task_description": obs["task_description"],
        }

        code = generate_code(task_dict)
        step_result = env.step(code)

        reward = step_result["reward"]
        done = step_result["done"]
        info = step_result["info"]

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

        results.append({
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            "reward": reward,
            "details": info,
        })

        if done:
            break

        # Advance obs to the next task using internal environment index
        if not done:
            nxt = ALL_TASKS[env.current_index]
            obs = {
                "task_id": nxt.task_id,
                "task_description": nxt.task_description,
                "difficulty": nxt.difficulty.value,
            }
        else:
            obs = None


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
