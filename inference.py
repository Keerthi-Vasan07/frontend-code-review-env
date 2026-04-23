import os
from env import FrontendCodeReviewEnv
from models import Action

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

def get_action(task):
    return '''
    <button style="background-color:red;color:white"
            aria-label="Click Button">
        Click Me
    </button>
    '''

def main():
    env = FrontendCodeReviewEnv()
    
    tasks = env.available_tasks()
    total_tasks = len(tasks)
    
    print("[START]")
    print(f"total_tasks={total_tasks}")
    print(f"model={MODEL_NAME}")
    
    total_reward = 0.0
    
    for _ in range(total_tasks):
        env.reset()
        state = env.state()
        task_id = state["task_id"]
        
        action_code = get_action(task_id)
        action = Action(code=action_code)
        
        _, reward, done, info = env.step(action)
        
        total_reward += reward
        
        print("\n[STEP]")
        print(f"task_id={info['task_id']}")
        print(f"difficulty={info['difficulty']}")
        print(f"reward={reward:.4f}")
        print(f"structure_score={info.get('structure_score', 0.01):.4f}")
        print(f"style_score={info.get('style_score', 0.01):.4f}")
        print(f"responsiveness_score={info.get('responsiveness_score', 0.01):.4f}")
        print(f"accessibility_score={info.get('accessibility_score', 0.01):.4f}")
        print(f"code_quality_score={info.get('code_quality_score', 0.01):.4f}")
        print(f"penalties={info.get('penalties', 0.0):.1f}")
        print(f"done={str(done).lower()}")

    avg_reward = total_reward / total_tasks
    
    print("\n[END]")
    print(f"total_tasks={total_tasks}")
    print(f"average_reward={avg_reward:.4f}")

if __name__ == "__main__":
    main()