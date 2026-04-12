"""
frontend_code_review_env – OpenEnv-compliant environment (simplified).

Pipeline:
    Validator → FastAPI → FrontendEnv → tasks.py → graders.py → score

Public interface
----------------
    env.reset()         → dict  (task info)
    env.step(code)      → dict  (reward, done, info, next_task)
    env.state()         → dict  (debug snapshot)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from graders import grade
from tasks import ALL_TASKS


class FrontendEnv:
    """
    Minimal OpenEnv environment for frontend code review.

    Tasks are served sequentially from ALL_TASKS.  Each call to reset()
    restarts from the first task.  Each call to step() advances to the next.
    """

    def __init__(self) -> None:
        self.tasks = ALL_TASKS
        self.current_index: int = 0

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Dict[str, Any]:
        """
        Restart the episode from task 0.

        Returns
        -------
        dict
            task_id, task_description, difficulty
        """
        self.current_index = 0
        task = self.tasks[self.current_index]
        return {
            "task_id": task.task_id,
            "task_description": task.task_description,
            "difficulty": task.difficulty.value,
        }

    def step(self, code: str) -> Dict[str, Any]:
        """
        Evaluate *code* against the current task and advance to the next one.

        Parameters
        ----------
        code:
            Raw HTML/CSS/JS string submitted by the agent.

        Returns
        -------
        dict
            reward, done, info (score breakdown), next_task (or None if done)
        """
        task = self.tasks[self.current_index]

        # Grade the submission – always returns a GradeResult (no crash)
        try:
            result = grade(code, task)
        except Exception:
            # Absolute last-resort fallback so the server never 500s
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

        next_task_info: Optional[Dict[str, Any]] = None
        if not done:
            nxt = self.tasks[self.current_index]
            next_task_info = {
                "task_id": nxt.task_id,
                "task_description": nxt.task_description,
                "difficulty": nxt.difficulty.value,
            }

        return {
            "reward": result.total_reward,
            "done": done,
            "info": result.model_dump(),
            "next_task": next_task_info,
        }

    def state(self) -> Dict[str, Any]:
        """Return a debug snapshot of the current environment state."""
        idx = min(self.current_index, len(self.tasks) - 1)
        task = self.tasks[idx]
        return {
            "current_index": self.current_index,
            "total_tasks": len(self.tasks),
            "done": self.current_index >= len(self.tasks),
            "current_task_id": task.task_id,
            "difficulty": task.difficulty.value,
        }
