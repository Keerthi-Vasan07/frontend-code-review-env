from models import GradeResult

def grade(code: str, task) -> GradeResult:
    """
    Simple outcome-based reward system returned as structured GradeResult.
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

    score = reward / 10.0
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
