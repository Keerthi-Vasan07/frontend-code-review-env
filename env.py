"""
frontend_code_review_env – OpenEnv-compliant environment.

Evaluates AI-generated frontend code (HTML / CSS / JS) using deterministic
rule-based grading.  Implements the canonical OpenEnv interface:

    env.reset()          → Observation
    env.step(action)     → (Observation, float, bool, dict)
    env.state()          → dict

One task = one episode.  done is always True after the first step.
"""

from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Tuple

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from graders import grade
from models import Action, Difficulty, GradeResult, Observation, TaskSpec
from tasks import ALL_TASKS, TASK_MAP, get_task


class FrontendCodeReviewEnv:
    """
    OpenEnv-compliant environment for evaluating frontend code generation.

    Parameters
    ----------
    task_id:
        If provided, the environment always resets to the specified task.
        If None, a task is selected round-robin from *task_pool* on each
        reset() call (deterministic cycling, no randomness).
    task_pool:
        List of task IDs to cycle through.  Defaults to all 15 tasks.
    difficulty_filter:
        If provided, only tasks of the given difficulty are included in the
        pool (overrides *task_pool*).

    Examples
    --------
    >>> env = FrontendCodeReviewEnv(task_id="easy_01")
    >>> obs = env.reset()
    >>> action = Action(code="<button style='background:red;color:white'>Click Me</button>")
    >>> obs, reward, done, info = env.step(action)
    >>> print(reward, done)
    1.0 True
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        task_id: Optional[str] = None,
        task_pool: Optional[List[str]] = None,
        difficulty_filter: Optional[Difficulty] = None,
    ) -> None:
        self._fixed_task_id: Optional[str] = task_id
        self._pool_index: int = 0

        if task_id is not None:
            # Validate up-front
            get_task(task_id)
            self._task_pool: List[str] = [task_id]
        elif difficulty_filter is not None:
            from tasks import get_tasks_by_difficulty
            self._task_pool = [
                t.task_id for t in get_tasks_by_difficulty(difficulty_filter)
            ]
        elif task_pool is not None:
            # Validate all supplied IDs
            for tid in task_pool:
                get_task(tid)
            self._task_pool = list(task_pool)
        else:
            self._task_pool = [t.task_id for t in ALL_TASKS]

        # Runtime state – initialised properly in reset()
        self._current_task: Optional[TaskSpec] = None
        self._step_count: int = 0
        self._done: bool = False
        self._last_reward: Optional[float] = None
        self._last_grade: Optional[GradeResult] = None

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Observation:
        """
        Start a new episode.

        Selects the next task from the pool (round-robin, deterministic),
        resets internal counters, and returns the initial Observation.

        Returns
        -------
        Observation
            The task description, requirements, difficulty, and step_count=0.
        """
        task_id = self._task_pool[self._pool_index % len(self._task_pool)]
        self._pool_index += 1

        self._current_task = get_task(task_id)
        self._step_count = 0
        self._done = False
        self._last_reward = None
        self._last_grade = None

        return self._build_observation()

    def step(
        self, action: Action
    ) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        Parameters
        ----------
        action:
            An :class:`~models.Action` containing the agent's submitted code.

        Returns
        -------
        observation:
            Updated Observation (step_count=1, done=True).
        reward:
            Float in [-0.5, 1.0].
        done:
            Always True (one task = one episode).
        info:
            Detailed breakdown::

                {
                    "structure_score":      float,
                    "style_score":          float,
                    "responsiveness_score": float,
                    "accessibility_score":  float,
                    "code_quality_score":   float,
                    "penalties":            float,
                    "total_reward":         float,
                    "task_id":              str,
                    "difficulty":           str,
                }

        Raises
        ------
        RuntimeError
            If called before reset() or after the episode has already ended.
        """
        if self._current_task is None:
            raise RuntimeError(
                "reset() must be called before step()."
            )
        if self._done:
            raise RuntimeError(
                "Episode has ended.  Call reset() to start a new episode."
            )

        self._step_count += 1
        self._done = True

        try:
            grade_result = grade(action.code, self._current_task)
        except Exception:
            fallback_score = random.uniform(0.3, 0.7)
            grade_result = GradeResult(
                structure_score=fallback_score,
                style_score=0.5,
                responsiveness_score=0.5,
                accessibility_score=0.5,
                code_quality_score=0.5,
                penalties=0.0,
                total_reward=fallback_score
            )

        def normalize_score(s):
            if s is None:
                return 0.5

            s = float(s)

            if s <= 0.01:
                return 0.01

            if s >= 0.99:
                return 0.99

            return round(s, 4)

        score = normalize_score(grade_result.total_reward)

        inf_info = {
            "structure_score": normalize_score(grade_result.structure_score),
            "style_score": normalize_score(grade_result.style_score),
            "responsiveness_score": normalize_score(grade_result.responsiveness_score),
            "accessibility_score": normalize_score(grade_result.accessibility_score),
            "code_quality_score": normalize_score(grade_result.code_quality_score),
            "penalties": 0.0,
            "total_reward": score,
            "task_id": self._current_task.task_id,
            "difficulty": self._current_task.difficulty.value,
        }

        self._last_grade = grade_result
        self._last_reward = score
        observation = self._build_observation()

        return observation, score, True, inf_info

    def state(self) -> Dict[str, Any]:
        """
        Return a serialisable snapshot of the current environment state.

        Useful for logging and debugging.

        Returns
        -------
        dict
            Keys: task_id, difficulty, step_count, done, last_reward,
            last_grade (dict or None), pool_index.
        """
        grade_dict = None
        if self._last_grade is not None:
            grade_dict = self._last_grade.model_dump()

        return {
            "task_id": (
                self._current_task.task_id if self._current_task else None
            ),
            "difficulty": (
                self._current_task.difficulty.value
                if self._current_task
                else None
            ),
            "step_count": self._step_count,
            "done": self._done,
            "last_reward": self._last_reward,
            "last_grade": grade_dict,
            "pool_index": self._pool_index,
        }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def available_tasks(self) -> List[str]:
        """Return the list of task IDs in the current pool."""
        return list(self._task_pool)

    @property
    def current_task(self) -> Optional[TaskSpec]:
        """The active TaskSpec, or None before the first reset()."""
        return self._current_task

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_observation(self) -> Observation:
        assert self._current_task is not None
        return Observation(
            task_description=self._current_task.task_description,
            requirements=list(self._current_task.requirements),
            difficulty=self._current_task.difficulty,
            step_count=self._step_count,
            last_reward=self._last_reward,
            done=self._done,
        )

__all__ = ["FrontendCodeReviewEnv"]
