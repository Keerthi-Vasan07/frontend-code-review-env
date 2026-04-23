"""
graders.py – Deterministic, keyword-based grader for frontend_code_review_env.

Scoring uses dynamic weights: components with no task requirements (empty
keyword lists) are excluded from the weighted average, and their weight is
redistributed proportionally to the active components.

Component weights (before redistribution):
  structure_score      – 0.30
  style_score          – 0.25
  responsiveness_score – 0.20  (excluded if no responsiveness_keywords)
  accessibility_score  – 0.15  (excluded if no accessibility_keywords)
  code_quality_score   – 0.10

Structure scoring:
  - element present                → 0.5 base
  - element + all structure kws   → 1.0
  - no element (when required)    → 0.0

Style scoring:
  - fraction of expected_css_properties found

Penalties:
  -0.5 if code is empty, whitespace-only, or contains no HTML tags at all.
"""

from __future__ import annotations

import re
from typing import List

from models import GradeResult, TaskSpec


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """Lowercase and collapse all whitespace in *text*."""
    return re.sub(r"\s+", "", text.lower())


def _keyword_present(normalised_code: str, keyword: str) -> bool:
    """True if *keyword* (after normalisation) appears in *normalised_code*."""
    return _normalise(keyword) in normalised_code


def _any_keyword_present(normalised_code: str, keywords: List[str]) -> bool:
    """True if ANY keyword in *keywords* appears in *normalised_code*."""
    return any(_keyword_present(normalised_code, kw) for kw in keywords)


def _fraction_present(normalised_code: str, keywords: List[str]) -> float:
    """Fraction of *keywords* found in *normalised_code* (0.0 – 1.0)."""
    if not keywords:
        return 1.0
    hits = sum(1 for kw in keywords if _keyword_present(normalised_code, kw))
    return hits / len(keywords)


# ---------------------------------------------------------------------------
# Public grading entry-point
# ---------------------------------------------------------------------------


def grade(code: str, task: TaskSpec) -> GradeResult:
    """
    Evaluate *code* against *task* and return a :class:`GradeResult`.

    Raw component scores may be 0.0 or 1.0.
    env.py applies normalize_score() before exposing results to the validator.

    Parameters
    ----------
    code:
        Raw HTML/CSS/JS string submitted by the agent.
    task:
        The :class:`~models.TaskSpec` defining requirements for this episode.

    Returns
    -------
    GradeResult
        All fields populated with raw scores and weighted total.
    """
    # ── Empty / no-HTML penalty ──────────────────────────────────────────────
    if not code or not code.strip():
        return GradeResult(
            total_reward=-0.5,
            structure_score=0.0,
            style_score=0.0,
            responsiveness_score=0.0,
            accessibility_score=0.0,
            code_quality_score=0.0,
            penalties=-0.5,
        )

    if "<" not in code:
        return GradeResult(
            total_reward=-0.5,
            structure_score=0.0,
            style_score=0.0,
            responsiveness_score=0.0,
            accessibility_score=0.0,
            code_quality_score=0.0,
            penalties=-0.5,
        )

    norm = _normalise(code)

    # ── 1. Structure score ─────────────────────────────────────────────────────
    # element present  → 0.5 base
    # element + all structure patterns → 1.0
    has_element = bool(task.expected_elements) and _any_keyword_present(
        norm, task.expected_elements
    )
    struct_frac = (
        _fraction_present(norm, task.expected_structure)
        if task.expected_structure else 1.0
    )
    # CSS presence determines whether we go beyond the 0.5 element-present base
    has_any_css = bool(task.expected_css_properties) and _any_keyword_present(
        norm, task.expected_css_properties
    )

    if has_element and has_any_css:
        # Element present AND some CSS matched → bonus credit from structure patterns
        structure_score = 0.5 + 0.5 * struct_frac
    elif has_element:
        # Element present, no CSS → base credit only
        structure_score = 0.5
    elif task.expected_elements:
        # Required element missing entirely
        structure_score = 0.0
    else:
        structure_score = struct_frac

    # ── 2. Style score ─────────────────────────────────────────────────────────
    if task.expected_css_properties:
        # ANY match in the list counts as full credit (alternative representations)
        style_score = _fraction_present(norm, task.expected_css_properties)
        # Boost: if any ONE of the expected CSS alternatives is found, treat as full match
        # (expected_css_properties lists alternatives, not all-required properties)
        if style_score > 0:
            style_score = 1.0
    else:
        style_score = 0.5 if ("style=" in norm or "<style" in norm) else 0.0

    # ── 3. Responsiveness score ─────────────────────────────────────────────────
    if task.responsiveness_keywords:
        responsiveness_score = _fraction_present(norm, task.responsiveness_keywords)
    else:
        responsiveness_score = 0.0  # Not required → 0.0, excluded from average

    # ── 4. Accessibility score ─────────────────────────────────────────────────
    if task.accessibility_keywords:
        accessibility_score = _fraction_present(norm, task.accessibility_keywords)
    else:
        generic_a11y = ["aria-", "role=", "alt=", "<label", "tabindex"]
        accessibility_score = 0.3 if _any_keyword_present(norm, generic_a11y) else 0.0

    # ── 5. Code quality score ──────────────────────────────────────────────────
    inline_style_count = len(re.findall(r'style\s*=', code, re.IGNORECASE))
    has_style_block = bool(re.search(r'<style[\s>]', code, re.IGNORECASE))

    if inline_style_count > 5 and not has_style_block:
        code_quality_score = 0.1  # poor: excessive inline, no <style>
    elif has_style_block:
        code_quality_score = 1.0  # good: <style> block
    elif inline_style_count > 0:
        code_quality_score = 1.0  # acceptable inline styles (1-5): normal usage
    else:
        code_quality_score = 0.3  # minimal: no styling at all

    # ── Dynamic weighted total ─────────────────────────────────────────────────
    # Base weights
    base_weights = {
        "structure":      (structure_score,      0.30),
        "style":          (style_score,           0.25),
        "responsiveness": (responsiveness_score,  0.20),
        "accessibility":  (accessibility_score,   0.15),
        "code_quality":   (code_quality_score,    0.10),
    }

    # Exclude components that have no requirements AND scored 0.0
    # (responsiveness and accessibility with empty keyword lists)
    active = {}
    excluded_weight = 0.0

    for key, (score, weight) in base_weights.items():
        if key == "responsiveness" and not task.responsiveness_keywords:
            excluded_weight += weight
        elif key == "accessibility" and not task.accessibility_keywords:
            excluded_weight += weight
        else:
            active[key] = (score, weight)

    # Redistribute excluded weight proportionally to active components
    if active and excluded_weight > 0:
        total_active_weight = sum(w for _, w in active.values())
        active = {
            k: (s, w + excluded_weight * w / total_active_weight)
            for k, (s, w) in active.items()
        }

    total_reward = round(
        sum(s * w for s, w in active.values()),
        4,
    )
    # Cap at 1.0
    total_reward = min(total_reward, 1.0)

    return GradeResult(
        total_reward=total_reward,
        structure_score=structure_score,
        style_score=style_score,
        responsiveness_score=responsiveness_score,
        accessibility_score=accessibility_score,
        code_quality_score=code_quality_score,
        penalties=0.0,
    )
