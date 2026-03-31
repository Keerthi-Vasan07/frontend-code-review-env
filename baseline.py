"""
baseline.py – Baseline agent for frontend_code_review_env.

Uses the OpenAI Chat Completions API to generate frontend code for each task,
then evaluates the generated code with the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

try:
    import openai
except ImportError:
    print("[ERROR] 'openai' package not found.  Run: pip install openai", file=sys.stderr)
    sys.exit(1)

from env import FrontendCodeReviewEnv
from models import Action
from tasks import ALL_TASKS


def test_api_connection(client: Optional[openai.OpenAI]) -> bool:
    """Test the OpenAI API connection before starting evaluations."""
    if not client:
        return False
    try:
        print("Testing API connection...")
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
        )
        print("[API TEST SUCCESS]")
        return True
    except Exception as e:
        print("\n[API ERROR]:", str(e))
        print("[API TEST FAILED]:", e)
        return False


def extract_code(text: str) -> str:
    """Extract ONLY the HTML/CSS/JS code from an AI response."""
    match = re.search(r"```(?:html|css|javascript)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def build_user_prompt(task_description: str, requirements: List[str]) -> str:
    """Construct the strict instruction prompt."""
    req_block = "\n".join(f"- {r}" for r in requirements)
    return f"""You are a frontend developer.

TASK:
{task_description}

REQUIREMENTS:
{req_block}

STRICT RULES:
- Output ONLY valid HTML/CSS code
- DO NOT include explanations
- DO NOT include markdown
- DO NOT include ``` blocks
- DO NOT include comments
- Output raw code only

Generate the code now."""


def call_openai(
    client: Optional[openai.OpenAI],
    task_description: str,
    requirements: List[str],
    model: str,
    max_retries: int = 2,
) -> Optional[str]:
    """Call the OpenAI API and return the raw code string, or None on failure."""
    if not client:
        return None
    user_prompt = build_user_prompt(task_description, requirements)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.2,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except openai.RateLimitError as e:
            wait = 2**attempt
            print(f"  [WARN] Rate-limited, retrying in {wait}s (attempt {attempt}/{max_retries})…")
            time.sleep(wait)
        except Exception as e:
            print("\n[API ERROR]:", str(e))
            if attempt == max_retries:
                # We return None so we can handle it with the fallback dummy logic
                return None
            time.sleep(2)

    return None


def evaluate_task(
    env: FrontendCodeReviewEnv,
    client: Optional[openai.OpenAI],
    task_id: str,
    model: str,
    verbose: bool = False,
) -> Optional[Dict[str, Any]]:
    """Run one episode and return the info dict augmented with metadata."""
    obs = env.reset()

    print(f"\n{'='*60}")
    print(f"Task ID   : {task_id}")
    print(f"Difficulty: {obs.difficulty.value.upper()}")
    print(f"Task      : {obs.task_description[:80]}{'…' if len(obs.task_description) > 80 else ''}")
    print(f"Model     : {model}")
    print("-" * 60)

    # --- Generate code ---
    print("  Calling OpenAI API…", end=" ", flush=True)
    t0 = time.time()
    raw_response = call_openai(client, obs.task_description, obs.requirements, model)
    elapsed = time.time() - t0
    print(f"done ({elapsed:.1f}s)")

    # 2. HANDLE EMPTY API RESPONSE & 3. ADD FALLBACK DUMMY RESPONSE
    if not raw_response or not raw_response.strip():
        print("[ERROR] API returned empty response. Skipping evaluation.")
        fallback_code = "<div>Fallback response</div>"
        print("[FALLBACK] Using dummy code due to API failure.")
        raw_response = fallback_code
    
    # 6. PRINT RESPONSE LENGTH
    print(f"[DEBUG] Response length: {len(raw_response)}")

    # 1. AI RESPONSE PARSING
    extracted_code = extract_code(raw_response)

    # 7. ENSURE SAFE EXTRACTION
    if not extracted_code or len(extracted_code.strip()) == 0:
        print("[ERROR] Extracted code is empty.")
        extracted_code = "<div>Fallback response</div>"
        print("[FALLBACK] Using dummy code due to extraction failure.")

    # 8. CLEAN TERMINAL OUTPUT
    print("\n--- RAW MODEL OUTPUT ---")
    print(raw_response)
    print("\n--- EXTRACTED CODE ---")
    print(extracted_code)
    print("------------------------\n")

    # Optional Bonus: If code does not contain any HTML tag
    if "<" not in extracted_code and extracted_code.strip():
        extracted_code = "<div>" + extracted_code + "</div>"

    extracted_code = extracted_code.strip()

    # --- Step environment ---
    try:
        action = Action(code=extracted_code)
        obs_after, reward, done, info = env.step(action)
    except Exception as e:
        # 1. SHOW REAL API ERRORS (in case step or Action initialization fails fundamentally)
        print("\n[API ERROR]:", str(e))
        raise

    # CLEAN OUTPUT FORMAT
    print(f"\n  Results for {task_id}:")
    print(f"    structure_score      : {info['structure_score']:.3f}")
    
    if info.get('style_score') is not None:
        print(f"    style_score          : {info['style_score']:.3f}")
    if info.get('responsiveness_score') is not None:
        print(f"    responsiveness_score : {info['responsiveness_score']:.3f}")
    if info.get('accessibility_score') is not None:
        print(f"    accessibility_score  : {info['accessibility_score']:.3f}")
    if info.get('code_quality_score') is not None:
        print(f"    code_quality_score   : {info['code_quality_score']:.3f}")
        
    print(f"    penalties            : {info['penalties']:.3f}")
    print(f"    ─────────────────────────")
    print(f"    TOTAL REWARD         : {reward:.3f}  (done={done})")

    # Ensure required fields for summary
    return {**info, "task_id": task_id, "difficulty": obs.difficulty.value}


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary(results: List[Dict[str, Any]]) -> None:
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    header = f"{'Task ID':<12} {'Diff':<8} {'Struct':>6} {'Style':>6} {'Resp':>6} {'A11y':>6} {'Qual':>6} {'Total':>7}"
    print(header)
    print("-" * len(header))

    total_reward = 0.0
    for r in results:
        row = (
            f"{r.get('task_id', ''):<12} "
            f"{r.get('difficulty', ''):<8} "
            f"{r.get('structure_score', 0.0):>6.3f} "
            f"{r.get('style_score', 0.0):>6.3f} "
            f"{r.get('responsiveness_score', 0.0):>6.3f} "
            f"{r.get('accessibility_score', 0.0):>6.3f} "
            f"{r.get('code_quality_score', 0.0):>6.3f} "
            f"{r.get('total_reward', 0.0):>7.3f}"
        )
        print(row)
        total_reward += r.get("total_reward", 0.0)

    avg = total_reward / len(results) if results else 0.0
    print("-" * len(header))
    print(f"{'AVERAGE':<12} {'':>8} {'':>6} {'':>6} {'':>6} {'':>6} {'':>6} {avg:>7.3f}")
    print(f"\nTotal tasks evaluated : {len(results)}")
    print(f"Average total reward  : {avg:.4f}")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseline agent for frontend_code_review_env."
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Evaluate a single task by ID (e.g. easy_01).  Omit to run all tasks.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Evaluate all 15 tasks (default if --task-id not given).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print generated code to stdout.",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        metavar="FILE",
        help="Write results to a JSON file.",
    )
    args = parser.parse_args()

    # --- API key ---
    api_key = os.environ.get("OPENAI_API_KEY")
    client = None
    if not api_key:
        print("[WARN] OPENAI_API_KEY environment variable is not set. Using fallback dummy responses.")
    else:
        client = openai.OpenAI(api_key=api_key)
        # 5. ADD API HEALTH CHECK FUNCTION
        if not test_api_connection(client):
            print("[WARN] API test failed. Continuing anyway, but expect fallback responses.")

    # --- Determine tasks to run ---
    if args.task_id:
        task_ids = [args.task_id]
    else:
        task_ids = [t.task_id for t in ALL_TASKS]

    # Warm up environment to validate pool
    _ = FrontendCodeReviewEnv(task_pool=task_ids)

    results: List[Dict[str, Any]] = []
    for task_id in task_ids:
        # Pin environment to this specific task for reproducibility
        single_env = FrontendCodeReviewEnv(task_id=task_id)
        result = evaluate_task(
            single_env, client, task_id, args.model, verbose=args.verbose
        )
        if result:
            results.append(result)

    # --- Summary ---
    if len(results) > 1:
        print_summary(results)

    # --- Optional JSON output ---
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"\nResults written to: {args.output_json}")


if __name__ == "__main__":
    main()
