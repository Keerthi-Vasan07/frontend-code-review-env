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
    # Strict OpenEnv validator format output
    print(f"[START] task=frontend env=custom model={MODEL_NAME}")

    env = FrontendEnv()
    obs = env.reset()
    
    rewards = []
    step = 0
    final_done = False

    for _ in range(len(ALL_TASKS)):
        step += 1
        
        task_dict = {
            "task_id": obs["task_id"],
            "task_description": obs["task_description"],
        }

        code = generate_code(task_dict)
        step_result = env.step(code)

        reward = step_result["reward"]
        done = step_result["done"]
        final_done = done
        
        rewards.append(reward)

        # Strict STEP line
        print(f"[STEP] step={step} action=generate_code reward={reward:.2f} done={str(done).lower()} error=null")

        if done:
            break

        # Advance obs to the next task returned by the environment contract
        obs = step_result["observation"]

    # Strict END line
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={str(final_done).lower()} steps={len(rewards)} rewards={rewards_str}")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_all_tasks()
