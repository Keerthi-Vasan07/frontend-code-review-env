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

from server.graders import grade
from server.models import GradeResult
from server.tasks import ALL_TASKS


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

    def step(self, action: Any) -> Dict[str, Any]:
        """
        Grade the submitted action and advance the index.
        """
        task = self.tasks[self.current_index]

        try:
            result = grade(action, task)
        except Exception:
            # Absolute fallback
            result = GradeResult(total_reward=0.01)

        # Strictly clamp reward within (0.01, 0.99)
        reward = max(0.01, min(0.99, result.total_reward))

        self.current_index += 1
        done = self.current_index >= len(self.tasks)

        return {
            "reward": reward,
            "done": done
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
