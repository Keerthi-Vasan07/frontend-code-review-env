"""
Deterministic grading engine for frontend_code_review_env.

All scoring is rule-based (keyword / pattern matching on the submitted code).
No randomness, no external calls.

Scoring breakdown
-----------------
EASY  (max 1.0):
    element present     → up to +0.5
    style correct       → up to +0.5

MEDIUM (max 1.0):
    correct structure   → up to +0.4
    required elements   → up to +0.3
    styling             → up to +0.3

HARD (max 1.0):
    structure           → up to +0.3
    responsiveness      → up to +0.3
    accessibility       → up to +0.2
    code quality        → up to +0.2

Penalties (applied after sub-scores are summed):
    missing code        → -0.5
    empty response      → -0.5
    invalid format      → -0.5

Final reward is capped to [-0.5, 1.0].
"""

from __future__ import annotations

import re
from typing import List

from models import Difficulty, GradeResult, TaskSpec


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _normalise(code: str) -> str:
    """
    Normalise submitted code for keyword checks:
    * collapse all whitespace to single spaces
    * remove spaces around colons and semicolons (CSS)
    * lower-case everything
    This makes checks like ``"display:flex"`` robust against formatting
    variations such as ``display : flex`` or ``display:   flex``.
    """
    normalised = code.lower()
    normalised = re.sub(r"\s+", " ", normalised)
    normalised = re.sub(r"\s*:\s*", ":", normalised)
    normalised = re.sub(r"\s*;\s*", ";", normalised)
    return normalised


def _keyword_present(normalised_code: str, keyword: str) -> bool:
    """Return True if *keyword* (already lower-cased) appears in *normalised_code*."""
    return keyword.lower() in normalised_code


def _any_keyword_present(normalised_code: str, keywords: List[str]) -> bool:
    """Return True if ANY of the keywords is found in the normalised code."""
    return any(_keyword_present(normalised_code, kw) for kw in keywords)


def _fraction_keywords_present(
    normalised_code: str, keywords: List[str]
) -> float:
    """
    Return the fraction of keywords that are present (0.0 – 1.0).
    Returns 0.0 if *keywords* is empty.
    """
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if _keyword_present(normalised_code, kw))
    return hits / len(keywords)


def _count_inline_style_attributes(code: str) -> int:
    """Count the number of ``style="..."`` attribute occurrences."""
    return len(re.findall(r'\bstyle\s*=\s*["\']', code, re.IGNORECASE))


def _has_reasonable_code_quality(code: str) -> bool:
    """
    Heuristic code-quality check:
    * Not excessive inline styles (≤ 3 inline style attributes tolerated)
    * Has at least one <style> block OR external stylesheet link OR inline
      styles that are intentionally minimal
    * Has recognisable HTML structure (html/head/body or fragment with proper
      elements)
    """
    inline_count = _count_inline_style_attributes(code)
    has_style_block = bool(re.search(r"<style[\s>]", code, re.IGNORECASE))
    has_link_stylesheet = bool(
        re.search(r'<link[^>]+stylesheet', code, re.IGNORECASE)
    )
    # Penalise heavy inline-style usage only
    excessive_inline = inline_count > 5 and not has_style_block and not has_link_stylesheet
    return not excessive_inline


# ---------------------------------------------------------------------------
# Difficulty-specific graders
# ---------------------------------------------------------------------------


def _grade_easy(normalised: str, task: TaskSpec) -> GradeResult:
    """
    EASY grading:
        element present   → fraction of expected_elements found × 0.5
        style correct     → any expected_css_property found → +0.5
    """
    # Structure / element score (max 0.5)
    element_fraction = _fraction_keywords_present(
        normalised, task.expected_elements
    )
    structure_score = round(element_fraction * 0.5, 4)

    # Style score (max 0.5) – presence of ANY matching CSS property
    style_hit = _any_keyword_present(normalised, task.expected_css_properties)
    # Also give partial credit if expected_structure keywords are present
    struct_hit = _any_keyword_present(normalised, task.expected_structure)
    if style_hit:
        style_score = 0.5
    elif struct_hit:
        # Partial: structure text present but no explicit CSS found
        style_score = 0.2
    else:
        style_score = 0.0

    return GradeResult(
        structure_score=structure_score,
        style_score=style_score,
        responsiveness_score=0.0,
        accessibility_score=0.0,
        code_quality_score=0.0,
        penalties=0.0,
        total_reward=min(1.0, structure_score + style_score),
    )


def _grade_medium(normalised: str, task: TaskSpec) -> GradeResult:
    """
    MEDIUM grading:
        correct structure   → fraction of expected_structure × 0.4
        required elements   → fraction of expected_elements × 0.3
        styling             → any expected_css_properties found → 0.3
    """
    # Structure score (max 0.4)
    structure_fraction = _fraction_keywords_present(
        normalised, task.expected_structure
    )
    structure_score = round(structure_fraction * 0.4, 4)

    # Element score (max 0.3)
    element_fraction = _fraction_keywords_present(
        normalised, task.expected_elements
    )
    element_score = round(element_fraction * 0.3, 4)

    # Style score (max 0.3)
    style_fraction = _fraction_keywords_present(
        normalised, task.expected_css_properties
    )
    # Generous: any 1 property gives partial credit; ≥2 gives full credit
    if len(task.expected_css_properties) == 0:
        style_score = 0.0
    elif style_fraction == 0.0:
        style_score = 0.0
    elif style_fraction < 0.5:
        style_score = 0.15
    else:
        style_score = 0.3

    return GradeResult(
        structure_score=structure_score,
        style_score=style_score,
        responsiveness_score=0.0,
        accessibility_score=0.0,
        code_quality_score=0.0,
        penalties=0.0,
        total_reward=min(1.0, structure_score + element_score + style_score),
    )


def _grade_hard(normalised: str, original_code: str, task: TaskSpec) -> GradeResult:
    """
    HARD grading:
        structure         → fraction of expected_structure × 0.3
        responsiveness    → fraction of responsiveness_keywords × 0.3
        accessibility     → fraction of accessibility_keywords × 0.2
        code quality      → heuristic check → up to 0.2
    """
    # Structure (max 0.3)
    structure_fraction = _fraction_keywords_present(
        normalised, task.expected_structure
    )
    structure_score = round(structure_fraction * 0.3, 4)

    # Responsiveness (max 0.3)
    resp_fraction = _fraction_keywords_present(
        normalised, task.responsiveness_keywords
    )
    responsiveness_score = round(resp_fraction * 0.3, 4)

    # Accessibility (max 0.2)
    a11y_fraction = _fraction_keywords_present(
        normalised, task.accessibility_keywords
    )
    accessibility_score = round(a11y_fraction * 0.2, 4)

    # Code quality (max 0.2)
    quality_ok = _has_reasonable_code_quality(original_code)
    code_quality_score = 0.2 if quality_ok else 0.05

    raw = (
        structure_score
        + responsiveness_score
        + accessibility_score
        + code_quality_score
    )
    return GradeResult(
        structure_score=structure_score,
        style_score=0.0,
        responsiveness_score=responsiveness_score,
        accessibility_score=accessibility_score,
        code_quality_score=code_quality_score,
        penalties=0.0,
        total_reward=min(1.0, raw),
    )


# ---------------------------------------------------------------------------
# Penalty checks
# ---------------------------------------------------------------------------


def _compute_penalties(code: str) -> float:
    """
    Return a negative penalty value based on submission quality.

    Rules:
    * code is None / empty string      → -0.5
    * code is whitespace only          → -0.5
    * code has no HTML-like content    → -0.5   (invalid format)
    """
    if not code:
        return -0.5
    if not code.strip():
        return -0.5
    # Rudimentary HTML presence check
    if not re.search(r"<[a-zA-Z]", code):
        return -0.5
    return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def grade(code: str, task: TaskSpec) -> GradeResult:
    """
    Grade *code* against *task* deterministically.

    Parameters
    ----------
    code:
        The raw HTML/CSS/JS string submitted by the agent.
    task:
        The TaskSpec defining expected elements, CSS, structure, etc.

    Returns
    -------
    GradeResult
        Sub-scores + final total_reward ∈ [-0.5, 1.0].
    """
    penalty = _compute_penalties(code)
    if penalty < 0.0:
        # Short-circuit: penalise immediately, no point scoring further
        return GradeResult(
            structure_score=0.0,
            style_score=0.0,
            responsiveness_score=0.0,
            accessibility_score=0.0,
            code_quality_score=0.0,
            penalties=penalty,
            total_reward=penalty,
        )

    normalised = _normalise(code)

    if task.difficulty == Difficulty.EASY:
        result = _grade_easy(normalised, task)
    elif task.difficulty == Difficulty.MEDIUM:
        result = _grade_medium(normalised, task)
    else:  # HARD
        result = _grade_hard(normalised, code, task)

    # Apply penalties on top of positive scores
    final_reward = result.total_reward + penalty

    # Semantic HTML boost: reward use of meaningful structural elements
    if "<button" in code or "<header" in code or "<section" in code:
        final_reward += 0.05

    # Accessibility bonus: reward ARIA attributes and alt text
    if "aria-" in code or "alt=" in code:
        final_reward += 0.05

    final_reward = round(max(-0.5, min(1.0, final_reward)), 4)

    return GradeResult(
        structure_score=result.structure_score,
        style_score=result.style_score,
        responsiveness_score=result.responsiveness_score,
        accessibility_score=result.accessibility_score,
        code_quality_score=result.code_quality_score,
        penalties=penalty,
        total_reward=final_reward,
    )
