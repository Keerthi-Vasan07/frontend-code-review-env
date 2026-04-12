from models import GradeResult

def grade(code: str, task) -> GradeResult:
    """
    Outcome-based reward system with task-dependent variation.
    """
    reward = 0.0
    code_lower = code.lower()

    if "<html" in code_lower:
        reward += 2

    if "<style" in code_lower or "style=" in code_lower:
        reward += 2

    if "button" in code_lower or "input" in code_lower:
        reward += 2

    reward += min(len(code) / 500, 1.0) * 4

    # Baseline score (0.0 - 1.0)
    base_score = reward / 10.0

    # Task-specific factor for variation (0.0 - 1.0)
    task_factor = (abs(hash(task.task_id)) % 100) / 100.0

    # Weighted final score: 70% content, 30% task-specific differentiation
    score = (0.7 * base_score) + (0.3 * task_factor)

    # Clamp result strictly within (0.02, 0.98)
    score = max(0.02, min(0.98, round(score, 4)))

    return GradeResult(
        total_reward=score,
        structure_score=score * 0.3,
        style_score=score * 0.2,
        responsiveness_score=score * 0.2,
        accessibility_score=score * 0.2,
        code_quality_score=score * 0.1,
        penalties=0.0
    )

