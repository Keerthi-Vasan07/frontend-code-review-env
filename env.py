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

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Dict[str, Any]:
        """Restart from task 0. Returns the first task dict."""
        self.current_index = 0
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
            reward      – float in (0.02, 0.98)
            done        – True when all tasks have been evaluated
            info        – full GradeResult breakdown (plain dict)
            next_task   – next task dict, or None when done
        """
        task = self.tasks[self.current_index]

        try:
            result = grade(code, task)
        except Exception:
            # Absolute fallback – never crash the server
            from models import GradeResult
            result = GradeResult(
                structure_score=0.02,
                style_score=0.02,
                responsiveness_score=0.02,
                accessibility_score=0.02,
                code_quality_score=0.02,
                penalties=0.0,
                total_reward=0.02,
            )

        self.current_index += 1
        done = self.current_index >= len(self.tasks)

        next_task: Optional[Dict[str, Any]] = None
        if not done:
            nxt = self.tasks[self.current_index]
            next_task = {
                "task_id": nxt.task_id,
                "task_description": nxt.task_description,
                "difficulty": nxt.difficulty.value,
            }

        return {
            "reward": result.total_reward,
            "done": done,
            "info": result.model_dump(),
            "next_task": next_task,
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
