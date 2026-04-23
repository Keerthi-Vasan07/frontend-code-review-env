"""
Task catalogue for frontend_code_review_env.

Contains 15 tasks (5 easy, 5 medium, 5 hard) with full grading specifications.
All task data is static and deterministic – no randomness is used.
"""

from __future__ import annotations

from typing import Dict, List

from models import Difficulty, TaskSpec

# ---------------------------------------------------------------------------
# EASY TASKS  (max reward 1.0 per task)
# ---------------------------------------------------------------------------
# Grading strategy: element present → +0.5 | style correct → +0.5

EASY_TASKS: List[TaskSpec] = [
    TaskSpec(
        task_id="easy_01",
        task_description=(
            "Create a simple red button with the label 'Click Me'. "
            "The button background must be red and the text must be white."
        ),
        requirements=[
            "Include a <button> element.",
            "Set the background color to red (background-color: red or background: red).",
            "Set the text color to white.",
            "Button label must be 'Click Me'.",
        ],
        difficulty=Difficulty.EASY,
        expected_elements=["<button"],
        expected_css_properties=[
            "background-color:red",
            "background:red",
            "background-color:#ff0000",
            "background:#ff0000",
            "background-color:rgb(255,0,0)",
        ],
        expected_structure=["click me"],
        responsiveness_keywords=[],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="easy_02",
        task_description=(
            "Create a <div> that is horizontally and vertically centered on the page. "
            "The div must have a fixed width of 200px, a height of 200px, and a "
            "light-blue background color."
        ),
        requirements=[
            "Include a <div> element.",
            "Center it using CSS (margin:auto, flexbox, or grid).",
            "Set width to 200px and height to 200px.",
            "Apply a light-blue background color.",
        ],
        difficulty=Difficulty.EASY,
        expected_elements=["<div"],
        expected_css_properties=[
            "margin:auto",
            "margin:0auto",
            "display:flex",
            "display:grid",
            "width:200px",
            "height:200px",
        ],
        expected_structure=["200px"],
        responsiveness_keywords=[],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="easy_03",
        task_description=(
            "Add an <h1> heading with the text 'Hello World' and style it with a "
            "font color of navy blue (#001f5b or navy)."
        ),
        requirements=[
            "Include an <h1> element.",
            "The text content must be 'Hello World'.",
            "Set the text color to navy / #001f5b / #00008b or similar dark blue.",
        ],
        difficulty=Difficulty.EASY,
        expected_elements=["<h1"],
        expected_css_properties=[
            "color:navy",
            "color:#001f5b",
            "color:#00008b",
            "color:#000080",
        ],
        expected_structure=["hello world"],
        responsiveness_keywords=[],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="easy_04",
        task_description=(
            "Create an unordered list (<ul>) with exactly three list items: "
            "'Apple', 'Banana', and 'Cherry'. Remove the default bullet points "
            "using CSS (list-style: none)."
        ),
        requirements=[
            "Include a <ul> element.",
            "Include exactly three <li> items: Apple, Banana, Cherry.",
            "Apply list-style: none to remove bullets.",
        ],
        difficulty=Difficulty.EASY,
        expected_elements=["<ul", "<li"],
        expected_css_properties=[
            "list-style:none",
            "list-style-type:none",
        ],
        expected_structure=["apple", "banana", "cherry"],
        responsiveness_keywords=[],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="easy_05",
        task_description=(
            "Create a paragraph <p> element that contains the text "
            "'Welcome to my website.' and styles it with font-size: 18px "
            "and font-family: Arial, sans-serif."
        ),
        requirements=[
            "Include a <p> element.",
            "Text content: 'Welcome to my website.'",
            "Set font-size to 18px.",
            "Set font-family to Arial or sans-serif.",
        ],
        difficulty=Difficulty.EASY,
        expected_elements=["<p"],
        expected_css_properties=[
            "font-size:18px",
            "font-family:arial",
            "font-family:sans-serif",
        ],
        expected_structure=["welcome to my website"],
        responsiveness_keywords=[],
        accessibility_keywords=[],
    ),
]

# ---------------------------------------------------------------------------
# MEDIUM TASKS  (max reward 1.0 per task)
# ---------------------------------------------------------------------------
# Grading strategy: structure → +0.4 | required elements → +0.3 | styling → +0.3

MEDIUM_TASKS: List[TaskSpec] = [
    TaskSpec(
        task_id="medium_01",
        task_description=(
            "Create a login form with an email input, a password input, and a "
            "submit button labeled 'Log In'. The form should be centered on the "
            "page and have a visible border and padding."
        ),
        requirements=[
            "Include a <form> element.",
            "Include an <input type='email'> field.",
            "Include an <input type='password'> field.",
            "Include a <button type='submit'> or <input type='submit'>.",
            "Center the form on the page.",
            "Apply border and padding to the form.",
        ],
        difficulty=Difficulty.MEDIUM,
        expected_elements=["<form", "<input", "<button"],
        expected_css_properties=[
            "border",
            "padding",
            "margin:auto",
            "margin:0auto",
            "display:flex",
        ],
        expected_structure=[
            'type="email"',
            "type='email'",
            'type="password"',
            "type='password'",
            "log in",
        ],
        responsiveness_keywords=[],
        accessibility_keywords=["<label", "for=", "placeholder"],
    ),
    TaskSpec(
        task_id="medium_02",
        task_description=(
            "Build a card component that displays a product image (use a "
            "placeholder <img>), a product title in <h2>, a short description "
            "in <p>, and a 'Buy Now' button. The card should have a box-shadow "
            "and rounded corners."
        ),
        requirements=[
            "Include an <img> element (placeholder src is acceptable).",
            "Include an <h2> for the product title.",
            "Include a <p> for the description.",
            "Include a <button> labeled 'Buy Now'.",
            "Apply box-shadow to the card.",
            "Apply border-radius for rounded corners.",
        ],
        difficulty=Difficulty.MEDIUM,
        expected_elements=["<img", "<h2", "<p", "<button"],
        expected_css_properties=[
            "box-shadow",
            "border-radius",
        ],
        expected_structure=["buy now"],
        responsiveness_keywords=[],
        accessibility_keywords=["alt="],
    ),
    TaskSpec(
        task_id="medium_03",
        task_description=(
            "Create a horizontal navigation bar with four links: Home, About, "
            "Services, and Contact. The navbar should have a dark background "
            "color and white link text. Links must be displayed inline/flex."
        ),
        requirements=[
            "Include a <nav> element.",
            "Include four <a> links: Home, About, Services, Contact.",
            "Display links horizontally using display:flex or display:inline-block.",
            "Apply a dark background color to the navbar.",
            "Style link text to white.",
        ],
        difficulty=Difficulty.MEDIUM,
        expected_elements=["<nav", "<a"],
        expected_css_properties=[
            "display:flex",
            "display:inline-block",
            "display:inline",
            "background-color:#",
            "background:#",
            "color:white",
            "color:#fff",
            "color:#ffffff",
        ],
        expected_structure=["home", "about", "services", "contact"],
        responsiveness_keywords=["display:flex"],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="medium_04",
        task_description=(
            "Create a two-column layout: a sidebar on the left (width 25%) and "
            "main content area on the right (width 75%). Use CSS flexbox. "
            "Both columns should have distinct background colors and padding."
        ),
        requirements=[
            "Use a flex container with two child elements.",
            "Sidebar must have width: 25%.",
            "Main content must have width: 75%.",
            "Both sections must have distinct background colors.",
            "Apply padding to both sections.",
        ],
        difficulty=Difficulty.MEDIUM,
        expected_elements=["<div"],
        expected_css_properties=[
            "display:flex",
            "width:25%",
            "width:75%",
            "padding",
        ],
        expected_structure=["25%", "75%"],
        responsiveness_keywords=["display:flex"],
        accessibility_keywords=[],
    ),
    TaskSpec(
        task_id="medium_05",
        task_description=(
            "Build a user profile card that contains a circular avatar image, "
            "the user's name in <h3>, a role/title in <p>, and three social "
            "media icon links. The avatar must be circular using border-radius: 50%."
        ),
        requirements=[
            "Include an <img> for the avatar with border-radius: 50%.",
            "Include an <h3> for the user name.",
            "Include a <p> for the role/title.",
            "Include at least three <a> links for social media.",
            "Apply border-radius: 50% to make the avatar circular.",
        ],
        difficulty=Difficulty.MEDIUM,
        expected_elements=["<img", "<h3", "<p", "<a"],
        expected_css_properties=[
            "border-radius:50%",
        ],
        expected_structure=["50%"],
        responsiveness_keywords=[],
        accessibility_keywords=["alt="],
    ),
]

# ---------------------------------------------------------------------------
# HARD TASKS  (max reward 1.0 per task)
# ---------------------------------------------------------------------------
# Grading: structure → +0.3 | responsiveness → +0.3 | accessibility → +0.2 | quality → +0.2

HARD_TASKS: List[TaskSpec] = [
    TaskSpec(
        task_id="hard_01",
        task_description=(
            "Create a fully responsive navigation bar using CSS Flexbox. "
            "On desktop (≥768px) links display horizontally. On mobile (<768px) "
            "links stack vertically via a media query. The navbar must include "
            "a logo/brand name and at least four navigation links. "
            "Use proper ARIA roles (role='navigation') and aria-label attributes."
        ),
        requirements=[
            "Use a <nav> element with role='navigation' and aria-label.",
            "Display links horizontally using display:flex on desktop.",
            "Use @media query to stack links vertically on mobile (<768px).",
            "Include a logo/brand text element.",
            "Include at least four <a> navigation links.",
            "Use semantic HTML – no excessive inline styles.",
        ],
        difficulty=Difficulty.HARD,
        expected_elements=["<nav", "<a", "<ul", "<li"],
        expected_css_properties=[
            "display:flex",
            "flex-direction:column",
            "flex-wrap:wrap",
        ],
        expected_structure=["<nav", "logo", "brand"],
        responsiveness_keywords=["@media", "display:flex", "flex-direction:column"],
        accessibility_keywords=["aria-label", "role=", "aria-"],
    ),
    TaskSpec(
        task_id="hard_02",
        task_description=(
            "Build a responsive CSS Grid photo gallery with three columns on "
            "desktop, two columns on tablet (≤900px), and one column on mobile "
            "(≤600px). Each gallery item must contain an <img> with an "
            "appropriate alt attribute and a caption in a <figcaption>. "
            "Wrap each item in a <figure> element."
        ),
        requirements=[
            "Use display:grid on the gallery container.",
            "Three columns on desktop using grid-template-columns.",
            "Two columns at ≤900px via @media query.",
            "One column at ≤600px via @media query.",
            "Use <figure> and <figcaption> for each item.",
            "All <img> elements must have a non-empty alt attribute.",
        ],
        difficulty=Difficulty.HARD,
        expected_elements=["<figure", "<figcaption", "<img"],
        expected_css_properties=[
            "display:grid",
            "grid-template-columns",
        ],
        expected_structure=["<figure", "<figcaption", "grid-template-columns"],
        responsiveness_keywords=["display:grid", "@media", "grid-template-columns"],
        accessibility_keywords=['alt="', "alt='"],
    ),
    TaskSpec(
        task_id="hard_03",
        task_description=(
            "Create an accessible modal dialog. The modal must be toggleable "
            "(open/close) with a trigger button. It must include role='dialog', "
            "aria-modal='true', aria-labelledby pointing to the modal title, "
            "and a visible close button. Trap focus inside the modal when open "
            "using tabindex. Use flexbox to center the modal overlay."
        ),
        requirements=[
            "Trigger button to open the modal.",
            "Modal overlay centered with display:flex.",
            "role='dialog' and aria-modal='true' on the modal container.",
            "aria-labelledby attribute referencing the modal title's id.",
            "A close button inside the modal.",
            "tabindex attributes for focus management.",
        ],
        difficulty=Difficulty.HARD,
        expected_elements=["<button", "<div"],
        expected_css_properties=[
            "display:flex",
            "position:fixed",
            "position:absolute",
        ],
        expected_structure=["role=\"dialog\"", "role='dialog'", "aria-modal"],
        responsiveness_keywords=["display:flex"],
        accessibility_keywords=[
            "aria-modal",
            "role=\"dialog\"",
            "role='dialog'",
            "aria-labelledby",
            "tabindex",
        ],
    ),
    TaskSpec(
        task_id="hard_04",
        task_description=(
            "Build a fully accessible HTML form for user registration. "
            "Fields: Full Name, Email, Password, Confirm Password, and a "
            "Terms checkbox. Every input must have an associated <label> "
            "(using for/id pairing). Show inline validation error messages "
            "using aria-describedby. The layout must use CSS Grid. "
            "The submit button must be disabled via aria-disabled until the "
            "terms checkbox is checked (JS toggle)."
        ),
        requirements=[
            "Use display:grid for form layout.",
            "Include <label> for every input using for/id pairing.",
            "Include fields: name, email, password, confirm-password, terms.",
            "Use aria-describedby for error message association.",
            "Use aria-disabled on the submit button.",
            "Terms checkbox that controls submit button state via JS.",
        ],
        difficulty=Difficulty.HARD,
        expected_elements=["<form", "<input", "<label", "<button"],
        expected_css_properties=[
            "display:grid",
        ],
        expected_structure=[
            "<label",
            "for=",
            "aria-describedby",
        ],
        responsiveness_keywords=["display:grid", "@media"],
        accessibility_keywords=[
            "aria-describedby",
            "aria-disabled",
            "<label",
            "for=",
        ],
    ),
    TaskSpec(
        task_id="hard_05",
        task_description=(
            "Create a responsive pricing table with three tiers: Basic, Pro, "
            "and Enterprise. Use CSS Grid for the three-column layout on desktop "
            "and a single-column stacked layout on mobile (≤640px) via @media. "
            "The Pro tier card must be visually highlighted (different background "
            "and a 'Most Popular' badge). Each tier must list exactly four "
            "features using a <ul>. Include a CTA <button> per tier. "
            "Use aria-label on each CTA button to distinguish them."
        ),
        requirements=[
            "Use display:grid with three columns on desktop.",
            "Stack to single column at ≤640px using @media.",
            "Include three pricing cards: Basic, Pro, Enterprise.",
            "Pro card has distinct styling (highlighted background / border).",
            "Each card has a <ul> with feature list items.",
            "Each card has a <button> with aria-label.",
        ],
        difficulty=Difficulty.HARD,
        expected_elements=["<ul", "<li", "<button"],
        expected_css_properties=[
            "display:grid",
            "grid-template-columns",
        ],
        expected_structure=["basic", "pro", "enterprise"],
        responsiveness_keywords=["display:grid", "@media", "grid-template-columns"],
        accessibility_keywords=["aria-label"],
    ),
]

# ---------------------------------------------------------------------------
# Public catalogue
# ---------------------------------------------------------------------------

ALL_TASKS: List[TaskSpec] = EASY_TASKS + MEDIUM_TASKS + HARD_TASKS

TASK_MAP: Dict[str, TaskSpec] = {t.task_id: t for t in ALL_TASKS}

TASKS_BY_DIFFICULTY: Dict[Difficulty, List[TaskSpec]] = {
    Difficulty.EASY: EASY_TASKS,
    Difficulty.MEDIUM: MEDIUM_TASKS,
    Difficulty.HARD: HARD_TASKS,
}


def get_task(task_id: str) -> TaskSpec:
    """Return a TaskSpec by task_id, raising KeyError if not found."""
    if task_id not in TASK_MAP:
        raise KeyError(
            f"Unknown task_id '{task_id}'. "
            f"Available: {sorted(TASK_MAP.keys())}"
        )
    return TASK_MAP[task_id]


def get_tasks_by_difficulty(difficulty: Difficulty) -> List[TaskSpec]:
    """Return all tasks for a given difficulty level."""
    return TASKS_BY_DIFFICULTY[difficulty]
