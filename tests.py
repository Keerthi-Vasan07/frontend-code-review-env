"""
tests.py – Unit tests for frontend_code_review_env.

Run with:  pytest tests.py -v
No external API keys required.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Make sure we can import local modules regardless of cwd
# ---------------------------------------------------------------------------
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from env import FrontendCodeReviewEnv
from graders import grade, _normalise, _keyword_present, _any_keyword_present
from models import Action, Difficulty, GradeResult, Observation, TaskSpec
from tasks import ALL_TASKS, EASY_TASKS, HARD_TASKS, MEDIUM_TASKS, get_task


# ============================================================================
# models.py
# ============================================================================


class TestObservation:
    def test_valid_observation(self):
        obs = Observation(
            task_description="Do something",
            requirements=["req1"],
            difficulty=Difficulty.EASY,
        )
        assert obs.step_count == 0
        assert obs.last_reward is None
        assert obs.done is False

    def test_missing_requirements_raises(self):
        with pytest.raises(ValidationError):
            Observation(
                task_description="x",
                requirements=[],   # min_length=1
                difficulty=Difficulty.EASY,
            )


class TestAction:
    def test_valid_action(self):
        a = Action(code="<p>hello</p>")
        assert a.code == "<p>hello</p>"

    def test_blank_code_raises(self):
        with pytest.raises(ValidationError):
            Action(code="   ")

    def test_empty_code_raises(self):
        with pytest.raises(ValidationError):
            Action(code="")


# ============================================================================
# tasks.py
# ============================================================================


class TestTasks:
    def test_total_task_count(self):
        assert len(ALL_TASKS) == 15

    def test_easy_count(self):
        assert len(EASY_TASKS) == 5

    def test_medium_count(self):
        assert len(MEDIUM_TASKS) == 5

    def test_hard_count(self):
        assert len(HARD_TASKS) == 5

    def test_task_ids_unique(self):
        ids = [t.task_id for t in ALL_TASKS]
        assert len(ids) == len(set(ids))

    def test_get_task_known(self):
        t = get_task("easy_01")
        assert t.task_id == "easy_01"
        assert t.difficulty == Difficulty.EASY

    def test_get_task_unknown_raises(self):
        with pytest.raises(KeyError):
            get_task("nonexistent_99")

    def test_all_tasks_have_requirements(self):
        for t in ALL_TASKS:
            assert len(t.requirements) > 0, f"{t.task_id} has no requirements"

    def test_all_tasks_have_expected_elements(self):
        for t in ALL_TASKS:
            assert len(t.expected_elements) > 0, (
                f"{t.task_id} has no expected_elements"
            )


# ============================================================================
# graders.py – helper functions
# ============================================================================


class TestGraderHelpers:
    def test_normalise_collapses_whitespace(self):
        assert _normalise("display :   flex") == "display:flex"

    def test_normalise_lowercases(self):
        assert _normalise("<BUTTON>") == "<button>"

    def test_keyword_present_true(self):
        assert _keyword_present("display:flex", "display:flex")

    def test_keyword_present_false(self):
        assert not _keyword_present("display:block", "display:flex")

    def test_any_keyword_present_true(self):
        assert _any_keyword_present("display:flex", ["display:grid", "display:flex"])

    def test_any_keyword_present_false(self):
        assert not _any_keyword_present("display:block", ["display:grid", "display:flex"])


# ============================================================================
# graders.py – EASY grading
# ============================================================================


class TestEasyGrading:
    TASK = get_task("easy_01")

    def _grade(self, code: str) -> GradeResult:
        return grade(code, self.TASK)

    def test_perfect_score(self):
        code = (
            "<button style='background-color:red;color:white'>Click Me</button>"
        )
        result = self._grade(code)
        assert result.total_reward == pytest.approx(1.0)
        assert result.penalties == 0.0

    def test_element_only_partial_score(self):
        code = "<button>Click Me</button>"
        result = self._grade(code)
        assert result.structure_score == pytest.approx(0.5)
        # No CSS -> style_score is 0 or partial
        assert result.total_reward < 1.0

    def test_empty_code_penalty(self):
        result = grade("", self.TASK)
        assert result.total_reward == -0.5
        assert result.penalties == -0.5

    def test_whitespace_only_penalty(self):
        result = grade("   \n\t  ", self.TASK)
        assert result.total_reward == -0.5

    def test_no_html_penalty(self):
        result = grade("just some plain text no tags", self.TASK)
        assert result.total_reward == -0.5

    def test_reward_capped_at_1(self):
        # Even if code is excellent, reward must not exceed 1.0
        code = (
            "<html><body>"
            "<button style='background-color:red;color:white;font-size:16px;'>"
            "Click Me</button></body></html>"
        )
        result = self._grade(code)
        assert result.total_reward <= 1.0


class TestEasyTask02:
    """Test easy_02: centered div with 200x200."""

    TASK = get_task("easy_02")

    def test_good_submission(self):
        code = (
            "<div style='width:200px;height:200px;"
            "background-color:lightblue;margin:auto;'></div>"
        )
        result = grade(code, self.TASK)
        assert result.total_reward > 0.5

    def test_missing_size_partial(self):
        code = "<div style='margin:auto;background:lightblue;'></div>"
        result = grade(code, self.TASK)
        assert 0 < result.total_reward < 1.0


# ============================================================================
# graders.py – MEDIUM grading
# ============================================================================


class TestMediumGrading:
    TASK = get_task("medium_01")  # Login form

    def _grade(self, code: str) -> GradeResult:
        return grade(code, self.TASK)

    def test_full_login_form(self):
        code = """
        <html><head>
        <style>
          form { border: 1px solid #ccc; padding: 20px; margin: 0 auto; width: 300px; }
        </style></head>
        <body>
          <form>
            <input type="email" placeholder="Email">
            <input type="password" placeholder="Password">
            <button type="submit">Log In</button>
          </form>
        </body></html>
        """
        result = self._grade(code)
        assert result.total_reward >= 0.7

    def test_partial_form_missing_password(self):
        code = "<form><input type='email'><button>Log In</button></form>"
        result = self._grade(code)
        assert 0 < result.total_reward < 1.0

    def test_structure_score_positive(self):
        code = "<form><input type='email'><input type='password'><button>Log In</button></form>"
        result = self._grade(code)
        assert result.structure_score > 0


class TestMediumTask03:
    """medium_03: horizontal nav bar."""

    TASK = get_task("medium_03")

    def test_full_navbar(self):
        code = """
        <nav style="display:flex;background:#333;">
          <a style="color:white;" href="#">Home</a>
          <a style="color:white;" href="#">About</a>
          <a style="color:white;" href="#">Services</a>
          <a style="color:white;" href="#">Contact</a>
        </nav>
        """
        result = grade(code, self.TASK)
        assert result.total_reward >= 0.7


# ============================================================================
# graders.py – HARD grading
# ============================================================================


class TestHardGrading:
    TASK = get_task("hard_01")  # Responsive navbar

    def _grade(self, code: str) -> GradeResult:
        return grade(code, self.TASK)

    def test_responsive_accessible_navbar(self):
        code = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <style>
          nav { display:flex; background:#222; }
          nav ul { display:flex; list-style:none; margin:0; padding:0; }
          @media (max-width:768px) {
            nav ul { flex-direction:column; }
          }
        </style>
        </head>
        <body>
          <nav role="navigation" aria-label="Main navigation">
            <span class="brand">Logo</span>
            <ul>
              <li><a href="#">Home</a></li>
              <li><a href="#">About</a></li>
              <li><a href="#">Services</a></li>
              <li><a href="#">Contact</a></li>
            </ul>
          </nav>
        </body>
        </html>
        """
        result = self._grade(code)
        assert result.responsiveness_score > 0
        assert result.accessibility_score > 0
        assert result.total_reward >= 0.7

    def test_no_responsiveness_zero_score(self):
        code = "<nav><a href='#'>Home</a></nav>"
        result = self._grade(code)
        assert result.responsiveness_score == 0.0

    def test_code_quality_penalised_excessive_inline(self):
        # More than 5 inline style attributes, no <style> block
        inline_styles = " ".join(
            f"<div style='color:red;'>item{i}</div>" for i in range(10)
        )
        code = f"<nav>{inline_styles}</nav>"
        result = self._grade(code)
        assert result.code_quality_score < 0.2


class TestHardTask02:
    """hard_02: CSS Grid photo gallery."""

    TASK = get_task("hard_02")

    def test_grid_gallery(self):
        code = """
        <!DOCTYPE html>
        <html><head>
        <style>
          .gallery { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
          @media(max-width:900px){ .gallery{ grid-template-columns:repeat(2,1fr); }}
          @media(max-width:600px){ .gallery{ grid-template-columns:1fr; }}
        </style></head>
        <body>
          <div class="gallery">
            <figure>
              <img src="photo1.jpg" alt="A mountain at sunset">
              <figcaption>Mountain</figcaption>
            </figure>
            <figure>
              <img src="photo2.jpg" alt="Ocean waves">
              <figcaption>Ocean</figcaption>
            </figure>
          </div>
        </body></html>
        """
        result = grade(code, self.TASK)
        assert result.responsiveness_score > 0.2
        assert result.accessibility_score > 0


# ============================================================================
# env.py
# ============================================================================


class TestEnvLifecycle:
    def test_reset_returns_observation(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        obs = env.reset()
        assert isinstance(obs, Observation)
        assert obs.step_count == 0
        assert not obs.done

    def test_step_returns_tuple(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        action = Action(code="<button style='background:red'>Click Me</button>")
        obs, reward, done, info = env.step(action)
        assert isinstance(obs, Observation)
        assert isinstance(reward, float)
        assert done is True
        assert isinstance(info, dict)

    def test_step_count_increments(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        action = Action(code="<button>x</button>")
        obs, _, _, _ = env.step(action)
        assert obs.step_count == 1

    def test_done_after_step(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        _, _, done, _ = env.step(Action(code="<p>x</p>"))
        assert done is True

    def test_step_before_reset_raises(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        with pytest.raises(RuntimeError, match="reset()"):
            env.step(Action(code="<p>x</p>"))

    def test_double_step_raises(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        env.step(Action(code="<p>x</p>"))
        with pytest.raises(RuntimeError, match="reset()"):
            env.step(Action(code="<p>x</p>"))

    def test_state_before_step(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        s = env.state()
        assert s["task_id"] == "easy_01"
        assert s["step_count"] == 0
        assert s["done"] is False
        assert s["last_reward"] is None

    def test_state_after_step(self):
        env = FrontendCodeReviewEnv(task_id="easy_01")
        env.reset()
        env.step(Action(code="<button style='background:red'>x</button>"))
        s = env.state()
        assert s["step_count"] == 1
        assert s["done"] is True
        assert s["last_reward"] is not None

    def test_info_keys(self):
        env = FrontendCodeReviewEnv(task_id="medium_01")
        env.reset()
        _, _, _, info = env.step(Action(code="<form><input type='email'></form>"))
        required_keys = {
            "structure_score",
            "style_score",
            "responsiveness_score",
            "accessibility_score",
            "code_quality_score",
            "penalties",
            "total_reward",
            "task_id",
            "difficulty",
        }
        assert required_keys.issubset(info.keys())

    def test_reward_range(self):
        env = FrontendCodeReviewEnv()
        for _ in range(15):
            env.reset()
            _, reward, _, _ = env.step(Action(code="<p>x</p>"))
            assert -0.5 <= reward <= 1.0

    def test_determinism(self):
        """Same code on same task always produces same reward."""
        code = "<button style='background:red;color:white'>Click Me</button>"
        rewards = []
        for _ in range(3):
            env = FrontendCodeReviewEnv(task_id="easy_01")
            env.reset()
            _, reward, _, _ = env.step(Action(code=code))
            rewards.append(reward)
        assert len(set(rewards)) == 1, "Grading is not deterministic!"

    def test_round_robin_cycling(self):
        """Pool cycles correctly across multiple resets."""
        env = FrontendCodeReviewEnv(task_pool=["easy_01", "easy_02", "easy_03"])
        first_ids = []
        for _ in range(6):
            obs = env.reset()
            # Retrieve task_id through state
            first_ids.append(env.current_task.task_id)
            env.step(Action(code="<p>x</p>"))
        assert first_ids == [
            "easy_01", "easy_02", "easy_03",
            "easy_01", "easy_02", "easy_03",
        ]

    def test_difficulty_filter(self):
        env = FrontendCodeReviewEnv(difficulty_filter=Difficulty.HARD)
        assert len(env.available_tasks()) == 5
        for tid in env.available_tasks():
            assert get_task(tid).difficulty == Difficulty.HARD


# ============================================================================
# End-to-end smoke test
# ============================================================================


class TestEndToEnd:
    def test_easy_perfect_cycle(self):
        """Verify all 5 easy tasks give reward > 0 with reasonable code."""
        code_map = {
            "easy_01": "<button style='background-color:red;color:white'>Click Me</button>",
            "easy_02": "<div style='width:200px;height:200px;background:lightblue;margin:auto'></div>",
            "easy_03": "<h1 style='color:navy'>Hello World</h1>",
            "easy_04": "<ul style='list-style:none'><li>Apple</li><li>Banana</li><li>Cherry</li></ul>",
            "easy_05": "<p style='font-size:18px;font-family:Arial,sans-serif'>Welcome to my website.</p>",
        }
        env = FrontendCodeReviewEnv(task_pool=list(code_map.keys()))
        for task_id, code in code_map.items():
            env_single = FrontendCodeReviewEnv(task_id=task_id)
            env_single.reset()
            _, reward, done, info = env_single.step(Action(code=code))
            assert reward > 0.5, f"Task {task_id} scored only {reward}"
            assert done is True

    def test_hard_partial_score(self):
        """Hard tasks with minimal code should yield partial (not zero) reward."""
        env = FrontendCodeReviewEnv(task_id="hard_01")
        env.reset()
        code = """
        <nav role="navigation" aria-label="Main nav">
          <div style="display:flex;">
            <a href="#">Home</a>
            <a href="#">About</a>
          </div>
        </nav>
        <style>@media(max-width:768px){nav div{flex-direction:column;}}</style>
        """
        _, reward, _, info = env.step(Action(code=code))
        assert reward > 0
        assert reward <= 1.0
