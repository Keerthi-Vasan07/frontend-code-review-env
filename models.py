"""
Pydantic models for the frontend_code_review_env OpenEnv environment.
Defines the Observation, Action, TaskSpec, and GradeResult schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Difficulty(str, Enum):
    """Task difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------


class Observation(BaseModel):
    """
    Observation returned by the environment after reset() or step().

    Attributes
    ----------
    task_description:
        A human-readable description of the frontend task the agent must solve.
    requirements:
        An ordered list of concrete requirements the submitted code must satisfy.
    difficulty:
        The difficulty tier of the current task (easy / medium / hard).
    step_count:
        Number of steps taken in the current episode (0 after reset, 1 after
        the first – and only – step).
    last_reward:
        The reward received on the most recent step, or None before any step
        has been taken.
    done:
        Whether the episode has terminated.
    """

    task_description: str = Field(
        ...,
        description="Human-readable description of the frontend task.",
    )
    requirements: List[str] = Field(
        ...,
        description="Ordered list of concrete requirements the code must satisfy.",
        min_length=1,
    )
    difficulty: Difficulty = Field(
        ...,
        description="Difficulty tier of the task.",
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="Number of steps taken so far in the current episode.",
    )
    last_reward: Optional[float] = Field(
        default=None,
        description="Reward received on the last step, or None if no step taken yet.",
    )
    done: bool = Field(
        default=False,
        description="True once the episode has terminated.",
    )

    model_config = {"frozen": False}


class Action(BaseModel):
    """
    Action submitted by the agent.

    Attributes
    ----------
    code:
        The HTML/CSS/JS source code produced by the agent in response to the
        current task.  Must be a non-empty string.
    """

    code: str = Field(
        ...,
        description="HTML/CSS/JS source code produced by the agent.",
    )

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("code must not be blank or whitespace-only.")
        return v

    model_config = {"frozen": False}


# ---------------------------------------------------------------------------
# Task definition model (used internally by tasks.py)
# ---------------------------------------------------------------------------


class TaskSpec(BaseModel):
    """
    Full specification of a single evaluation task.

    Attributes
    ----------
    task_id:
        Unique identifier string, e.g. ``"easy_01"``.
    task_description:
        Text shown to the agent.
    requirements:
        Ordered list of requirements shown to the agent.
    difficulty:
        Difficulty tier.
    expected_elements:
        HTML tag substrings that must be present, e.g. ``["<button"]``.
    expected_css_properties:
        CSS property/value fragments that must appear in style blocks or
        inline styles, e.g. ``["color:red", "background-color:red"]``.
    expected_structure:
        Higher-level structural checks (arbitrary keyword / pattern strings
        inspected by the grader).
    responsiveness_keywords:
        Patterns indicating responsive design (``display:flex``, ``@media``,
        ``display:grid``, etc.).
    accessibility_keywords:
        Patterns indicating accessibility (``aria-``, ``role=``, ``alt=``,
        ``<label``).
    """

    task_id: str
    task_description: str
    requirements: List[str]
    difficulty: Difficulty
    expected_elements: List[str] = Field(default_factory=list)
    expected_css_properties: List[str] = Field(default_factory=list)
    expected_structure: List[str] = Field(default_factory=list)
    responsiveness_keywords: List[str] = Field(default_factory=list)
    accessibility_keywords: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# Grading result model (used internally by graders.py)
# ---------------------------------------------------------------------------


class GradeResult(BaseModel):
    """
    Grading result for a single action submission.
    All score fields are in range [-0.5, 1.0].
    """
    total_reward: float
    structure_score: float = 0.01
    style_score: float = 0.01
    responsiveness_score: float = 0.01
    accessibility_score: float = 0.01
    code_quality_score: float = 0.01
    penalties: float = 0.0

    model_config = {"frozen": True}
