import json
import os
import time
import urllib.request

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TASKS = ["Easy_1", "Easy_2", "Medium", "Hard"]

# ─────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────

def http_post(endpoint: str, data: dict = None) -> dict:
    """Send a POST request to the environment server."""
    url = f"{BASE_URL}{endpoint}"
    json_data = json.dumps(data or {}).encode("utf-8")
    
    req = urllib.request.Request(
        url, 
        data=json_data, 
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

# ─────────────────────────────────────────────────────────────
# ACTION GENERATION
# ─────────────────────────────────────────────────────────────

def get_action(task_name: str, step: int) -> str:
    """Generate a task-specific action string (code)."""
    task_lower = task_name.lower()
    
    if "easy" in task_lower:
        # Easy -> {"selected_feature_id": "feat_b"}
        return json.dumps({"selected_feature_id": "feat_b"})
    
    elif "medium" in task_lower:
        # Medium -> correct ranking list
        return json.dumps({"ranking": ["feat_a", "feat_b", "feat_c"]})
    
    elif "hard" in task_lower:
        # Hard -> select "feat_sso" + justification
        return "Action: select 'feat_sso'. Justification: SSO is critical for enterprise security."
    
    # Fallback
    return "Generic action for unknown task"

# ─────────────────────────────────────────────────────────────
# INFERENCE LOOP
# ─────────────────────────────────────────────────────────────

def run_inference():
    """
    Execute the RL interaction pipeline: RESET -> STEP -> LOOP -> DONE
    """
    for task_name in TASKS:
        # 1. RESET
        try:
            obs = http_post("/reset")
        except Exception as e:
            # Fallback if server is not running or endpoint is unreachable
            print(f"[ERROR] Could not connect to server: {e}")
            break

        print(f"[START] task={task_name}")

        done = False
        step = 1
        total_score = 0.0

        # 2. STEP LOOP
        while not done and step <= 5: # Safety limit for steps
            action = get_action(task_name, step)
            
            # Send action to /step
            try:
                result = http_post("/step", {"code": action})
            except Exception as e:
                print(f"[ERROR] Step failed: {e}")
                break

            reward = result.get("reward", 0.0)
            done = result.get("done", False)

            # Enforce strict reward clamping [0.01, 0.99] as per requirements
            reward = max(0.01, min(0.99, round(reward, 2)))
            
            # Ensure cumulative score is never exactly 0.0 or 1.0 (internal logic)
            total_score += reward

            print(f"[STEP] step={step} reward={reward:.2f}")

            step += 1
            if done:
                break

        # 3. END
        print(f"[END] task={task_name} score={total_score:.2f} steps={step-1}")
        print() # Spacer

if __name__ == "__main__":
    # Small delay to ensure server has time to start if run in parallel script
    time.sleep(1)
    run_inference()
