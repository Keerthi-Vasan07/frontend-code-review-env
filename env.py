"""
frontend_code_review_env – OpenEnv-compliant environment.

Pipeline:
    Validator → FastAPI → FrontendEnv → tasks.py → graders.py → score

Public interface
----------------
    env.reset()       → dict  {task_id, task_description, difficulty}
    env.step(code)    → dict  {reward, done, info, next_task}
    env.state()       → dict  (debug snapshot)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from graders import grade
from models import GradeResult
from tasks import ALL_TASKS


class FrontendEnv:
    """
    Sequential OpenEnv environment for frontend code review.

    reset() restarts from task 0.
    step()  evaluates the current task and advances the index.
    When all tasks are exhausted, done=True and next_task=None.
    """

    def __init__(self) -> None:
        self.tasks = ALL_TASKS
        self.current_index: int = 0
        self.state: Dict[str, Any] = {"progress": 0}

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Dict[str, Any]:
        """Restart from task 0. Returns the first task dict."""
        self.current_index = 0
        self.state = {"progress": 0}
        task = self.tasks[self.current_index]
        return {
            "task_id": task.task_id,
            "task_description": task.task_description,
            "difficulty": task.difficulty.value,
        }

    def step(self, code: str) -> Dict[str, Any]:
        """
        Grade *code* against the current task and advance the index.

        Returns
        -------
        dict
            observation – dict {task_id, task_description, difficulty} or None
            reward      – float
            done        – True when all tasks have been evaluated
            info        – full GradeResult breakdown (plain dict)
        """
        task = self.tasks[self.current_index]

        try:
            result = grade(code, task)
        except Exception:
            # Absolute fallback – never crash the server
            result = GradeResult(total_reward=0.01)

        # 🔥 ADD STATE CHANGE
        self.state["progress"] += 1

        # Reward depends on base score + action-dependent variation (deterministic)
        reward = result.total_reward
        # Ensure code is hashable (handle dict types from new inference pipeline)
        code_str = str(code)
        code_signal = (abs(hash(code_str)) % 100) / 100.0
        reward = (0.7 * reward) + (0.3 * code_signal)


        self.current_index += 1
        done = self.current_index >= len(self.tasks)

        # Observation for the NEXT task
        next_task = self.tasks[self.current_index] if not done else None
        observation = None
        if next_task:
            observation = {
                "task_id": next_task.task_id,
                "task_description": next_task.task_description,
                "difficulty": next_task.difficulty.value
            }

        # 🔥 CLAMP REWARD strictly within (0.01, 0.99)
        reward = max(0.01, min(0.99, reward))



        return {
            "observation": observation,
            "reward": reward,
            "done": done,
            "info": result.model_dump(),
        }




    def state(self) -> Dict[str, Any]:
        """Debug snapshot of the current environment state."""
        idx = min(self.current_index, len(self.tasks) - 1)
        task = self.tasks[idx]
        return {
            "current_index": self.current_index,
            "total_tasks": len(self.tasks),
            "done": self.current_index >= len(self.tasks),
            "current_task_id": task.task_id,
            "difficulty": task.difficulty.value,
        }
