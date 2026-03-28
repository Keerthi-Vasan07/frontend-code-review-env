---
title: Frontend Code Review Env
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_file: server/app.py
pinned: false
---

# frontend_code_review_env

> An **OpenEnv-compliant** environment that evaluates AI-generated frontend code  
> (HTML / CSS / JS) using **deterministic, rule-based grading**.

---

## Table of Contents

1. [Project Description](#project-description)  
2. [How It Works](#how-it-works)  
3. [Project Structure](#project-structure)  
4. [Observation / Action Format](#observation--action-format)  
5. [Task Catalogue](#task-catalogue)  
6. [Reward System](#reward-system)  
7. [Setup Instructions](#setup-instructions)  
8. [Running the Baseline](#running-the-baseline)  
9. [Using the Environment Programmatically](#using-the-environment-programmatically)  
10. [Docker](#docker)  
11. [Testing](#testing)  

---

## Project Description

`frontend_code_review_env` simulates the real-world activity of a senior
developer reviewing AI-generated frontend code.  An agent receives a task
(e.g., *"Build a responsive navbar"*) and must produce valid HTML/CSS/JS.
The environment scores the submission across four axes:

| Axis | What is measured |
|---|---|
| **Structure** | Correct semantic elements and document structure |
| **Styling** | Required CSS properties present |
| **Responsiveness** | Flexbox, CSS Grid, media queries |
| **Accessibility** | ARIA attributes, alt text, label/for pairing |

All grading is **fully deterministic** – no LLM judge, no randomness.

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                 FrontendCodeReviewEnv                   │
│                                                         │
│  reset() ──► Observation (task_description,             │
│              requirements, difficulty, step_count=0)    │
│                                                         │
│  step(Action(code="…")) ──► (Observation,               │
│                               reward ∈ [-0.5, 1.0],     │
│                               done=True,                │
│                               info{…})                  │
│                                                         │
│  state() ──► dict snapshot (logging/debugging)          │
└─────────────────────────────────────────────────────────┘
```

1. **reset()** selects the next task from the pool (round-robin) and returns
   an `Observation` with the task brief.
2. The **agent** reads the observation and produces HTML/CSS/JS code.
3. **step(action)** passes the code to `graders.grade()`, which applies
   keyword/pattern checks against the task's expected elements, CSS
   properties, responsiveness keywords, and accessibility attributes.
4. A `GradeResult` is computed and returned as `(obs, reward, done=True, info)`.
5. The episode ends; call **reset()** to start the next task.

---

## Project Structure

```
frontend_code_review_env/
├── env.py          # FrontendCodeReviewEnv – OpenEnv interface
├── models.py       # Pydantic models: Observation, Action, TaskSpec, GradeResult
├── tasks.py        # 15 task definitions (5 easy, 5 medium, 5 hard)
├── graders.py      # Deterministic grading engine
├── baseline.py     # Baseline agent using OpenAI API
├── openenv.yaml    # OpenEnv specification
├── Dockerfile      # Container definition
├── requirements.txt
└── README.md
```

---

## Observation / Action Format

### Observation

```json
{
  "task_description": "Create a simple red button with the label 'Click Me'...",
  "requirements": [
    "Include a <button> element.",
    "Set the background color to red.",
    "Set the text color to white.",
    "Button label must be 'Click Me'."
  ],
  "difficulty": "easy",
  "step_count": 0,
  "last_reward": null,
  "done": false
}
```

| Field | Type | Description |
|---|---|---|
| `task_description` | `str` | Human-readable task brief |
| `requirements` | `list[str]` | Ordered list of requirements |
| `difficulty` | `"easy"` \| `"medium"` \| `"hard"` | Task difficulty tier |
| `step_count` | `int` | 0 after reset, 1 after step |
| `last_reward` | `float \| null` | Reward from last step |
| `done` | `bool` | True after the first step |

### Action

```json
{
  "code": "<!DOCTYPE html><html>…</html>"
}
```

| Field | Type | Description |
|---|---|---|
| `code` | `str` | Complete HTML/CSS/JS source code |

### Info dict (returned by step)

```json
{
  "structure_score":      0.3,
  "style_score":          0.5,
  "responsiveness_score": 0.0,
  "accessibility_score":  0.0,
  "code_quality_score":   0.0,
  "penalties":            0.0,
  "total_reward":         0.8,
  "task_id":              "easy_01",
  "difficulty":           "easy"
}
```

---

## Task Catalogue

### Easy Tasks (5)

| ID | Description |
|---|---|
| `easy_01` | Red button labeled "Click Me" |
| `easy_02` | Centered 200×200px div with light-blue background |
| `easy_03` | `<h1>` "Hello World" in navy blue |
| `easy_04` | `<ul>` with Apple / Banana / Cherry, no bullets |
| `easy_05` | `<p>` "Welcome to my website." – 18px Arial |

### Medium Tasks (5)

| ID | Description |
|---|---|
| `medium_01` | Login form (email + password + submit), centered with border |
| `medium_02` | Product card with image, h2, description, "Buy Now" button, box-shadow |
| `medium_03` | Horizontal nav bar with 4 links, dark background, white text |
| `medium_04` | Two-column flexbox layout: 25% sidebar + 75% main |
| `medium_05` | User profile card with circular avatar, name, role, social links |

### Hard Tasks (5)

| ID | Description |
|---|---|
| `hard_01` | Responsive flexbox navbar with ARIA, collapses on mobile via @media |
| `hard_02` | CSS Grid photo gallery (3→2→1 columns), `<figure>`/`<figcaption>`, alt text |
| `hard_03` | Accessible modal dialog: role=dialog, aria-modal, aria-labelledby, tabindex |
| `hard_04` | Accessible registration form: CSS Grid, label/for, aria-describedby, aria-disabled |
| `hard_05` | Responsive 3-tier pricing table: CSS Grid, highlighted Pro card, aria-label on CTAs |

---

## Reward System

### Scoring by Difficulty

#### Easy (max 1.0)

```
element present    →  +0.5
style correct      →  +0.5
```

#### Medium (max 1.0)

```
correct structure  →  +0.4
required elements  →  +0.3
styling            →  +0.3
```

#### Hard (max 1.0)

```
structure          →  +0.3
responsiveness     →  +0.3   (flex/grid/media queries)
accessibility      →  +0.2   (aria-*, alt, role, label)
code quality       →  +0.2   (semantic HTML, minimal inline styles)
```

### Penalties

| Condition | Penalty |
|---|---|
| Empty code | −0.5 |
| Whitespace-only | −0.5 |
| No HTML-like content | −0.5 |

### Final reward

```python
total_reward = max(-0.5, min(1.0, sum_of_subscores + penalties))
```

Scoring is **partial** (not binary) and fully **deterministic** –
the same code always produces the same score.

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- An [OpenAI API key](https://platform.openai.com/) (only for `baseline.py`)

### 1 – Clone / copy the project

```bash
git clone <repo-url> frontend_code_review_env
cd frontend_code_review_env
```

### 2 – Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3 – Install dependencies

```bash
pip install -r requirements.txt
```

### 4 – Set your API key

```bash
export OPENAI_API_KEY="sk-..."   # Windows: set OPENAI_API_KEY=sk-...
```

---

## Running the Baseline

### Evaluate all 15 tasks

```bash
python baseline.py --all
```

### Evaluate a single task

```bash
python baseline.py --task-id easy_01
python baseline.py --task-id hard_03 --verbose
```

### Use a different model

```bash
python baseline.py --all --model gpt-4o-mini
```

### Save results to JSON

```bash
python baseline.py --all --output-json results.json
```

### Example output

```
============================================================
Task ID  : easy_01
Difficulty: EASY
Task     : Create a simple red button with the label 'Click Me'.…
Model    : gpt-4o
------------------------------------------------------------
  Calling OpenAI API… done (1.4s)

  Results for easy_01:
    structure_score      : 0.500
    style_score          : 0.500
    responsiveness_score : 0.000
    accessibility_score  : 0.000
    code_quality_score   : 0.000
    penalties            : 0.000
    ─────────────────────────
    TOTAL REWARD         : 1.000  (done=True)
```

---

## Using the Environment Programmatically

```python
from env import FrontendCodeReviewEnv
from models import Action

# Fixed task
env = FrontendCodeReviewEnv(task_id="medium_01")
obs = env.reset()

print(obs.task_description)
print(obs.requirements)
print(obs.difficulty)

# Submit code
action = Action(code="""
<!DOCTYPE html>
<html>
<head>
<style>
  form { border: 1px solid #ccc; padding: 20px; width: 300px; margin: auto; }
  input { display: block; margin-bottom: 10px; width: 100%; }
</style>
</head>
<body>
  <form>
    <input type="email" placeholder="Email">
    <input type="password" placeholder="Password">
    <button type="submit">Log In</button>
  </form>
</body>
</html>
""")

obs_after, reward, done, info = env.step(action)
print(f"Reward: {reward}")
print(f"Info:   {info}")

# Cycle through all tasks
env_all = FrontendCodeReviewEnv()  # uses all 15 tasks round-robin
for _ in range(15):
    obs = env_all.reset()
    # … generate code …
    obs_after, reward, done, info = env_all.step(Action(code="<p>stub</p>"))
```

---

## Docker

### Build

```bash
docker build -t frontend-code-review-env .
```

### Run (all tasks)

```bash
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  frontend-code-review-env
```

### Run (single task, verbose)

```bash
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  frontend-code-review-env \
  --task-id hard_01 --verbose
```

### Run (specific model)

```bash
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  frontend-code-review-env \
  --all --model gpt-4o-mini
```

---

## Testing

Run the unit tests (no API key required):

```bash
pytest -v
```

Tests cover:

- Pydantic model validation (valid and invalid inputs)
- Grader correctness for all three difficulty tiers
- Penalty application for empty / invalid submissions
- `env.reset()` / `env.step()` / `env.state()` lifecycle
- Round-robin task cycling

---

## License

MIT
