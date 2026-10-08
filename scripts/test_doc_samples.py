#!/usr/bin/env python3
"""Keep the sample outputs in the docs true.

README.md, the website and the examples show what the skill scripts answer for
a few requests (decision type, framework, bias warnings, ...). This script
runs those requests through the real scripts and checks two things:

1. the script still gives the answer the sample shows (catches engine changes
   that make a sample wrong), and
2. every doc that shows the sample still names those values (catches a sample
   edited by hand without re-running it).

When it fails after you change a skill's knowledge base or classification,
re-run the request, update the sample in the docs it names and the expected
values below. Prefer clear-cut requests for samples, so they stay stable.

Run: python3 scripts/test_doc_samples.py   (standard library only, Python 3.9+)
scripts/test_docs.py runs it too.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".agents" / "skills"

# A small Node project for the /code.debug sample: the stack trace in the
# request points into these files, and package.json gives the project checks.
CHECKOUT_PROJECT = {
    "package.json": '{"name": "shop", "scripts": {"test": "vitest run", '
                    '"lint": "eslint .", "build": "tsc -p ."}}\n',
    "src/checkout/total.js": (
        "// totals\n\nfunction applyGiftCards(cart, total) {\n  return total;\n}\n\n"
        "function orderTotal(cart) {\n  const items = cart.items || [];\n"
        "  const subtotal = items.reduce((s, i) => s + i.price, 0);\n"
        "  const discount = cart.coupon.id ? cart.coupon.amount : 0;\n"
        "  return applyGiftCards(cart, subtotal - discount);\n}\n"
        "module.exports = { orderTotal };\n"),
    "src/checkout/handler.js": (
        "const { orderTotal } = require('./total');\n\n"
        "function payHandler(req, res) {\n  const total = orderTotal(req.session.cart);\n"
        "  res.json({ total });\n}\nmodule.exports = { payHandler };\n"),
}

CHECKOUT_REQUEST = """Checkout throws after yesterday's deploy when paying with a gift card:
TypeError: Cannot read properties of undefined (reading 'id')
    at orderTotal (src/checkout/total.js:10:33)
    at payHandler (src/checkout/handler.js:4:17)
    at Layer.handle (node_modules/express/lib/router/layer.js:95:5)
Repro: add a gift card, then pay."""

# Each sample: the request, the script's answer, and the docs that show it.
# "expect" keys are read from the script's --json output (see extract()).
SAMPLES = [
    {
        "name": "README /decide",
        "skill": "make-decision",
        "text": "Postgres vs MongoDB vs DynamoDB for our order service",
        "expect": {
            "type": "Multi-Option Selection",
            "framework": "Weighted Criteria Matrix",
            "criteria": "Tech Stack / Framework Choice",
            "options": ["Postgres", "MongoDB", "DynamoDB"],
            "biases": ["Anchoring Effect", "Availability Heuristic", "Confirmation Bias"],
        },
        "docs": ["README.md", "docs/index.html"],
    },
    {
        "name": "README /solve",
        "skill": "problem-solving-pro",
        "text": "Signups dropped 15% after the pricing change",
        "expect": {
            "type": "Diagnostic",
            "category": "Business Performance",
            "decomposition": "Fishbone (Ishikawa)",
            "biases": ["Confirmation Bias", "Narrative Fallacy", "Availability Heuristic"],
        },
        "docs": ["README.md"],
    },
    {
        "name": "website /solve.deep",
        "skill": "problem-solving-pro",
        "text": "Revenue dropped 20% despite market growth",
        "args": ["--depth", "deep"],
        "expect": {
            "type": "Diagnostic",
            "decomposition": "Fishbone (Ishikawa)",
            "biases": ["Confirmation Bias", "Narrative Fallacy", "Availability Heuristic", "Anchoring"],
        },
        "docs": ["docs/index.html"],
    },
    {
        "name": "README /code.debug",
        "skill": "code-solving",
        "text": CHECKOUT_REQUEST,
        "args": ["--type", "debug"],
        "project": CHECKOUT_PROJECT,
        "expect": {
            "type": "debug",
            "error": "TypeError: Cannot read properties of undefined/null",
            "locations": ["src/checkout/total.js:10", "src/checkout/handler.js:4"],
            "checks": ["npm run test", "npm run lint", "npm run build"],
        },
        "docs": ["README.md", "examples/06-code-debug-typeerror.md"],
    },
    {
        "name": "example 01",
        "skill": "make-decision",
        "text": "Should we add more bundled skills to the CLI tool or keep it minimal with 2 skills",
        "expect": {
            "type": "Binary Choice",
            "framework": "Pros-Cons-Fixes Analysis",
            "biases": ["Confirmation Bias", "Sunk Cost Fallacy", "Status Quo Bias"],
        },
        "docs": ["examples/01-product-strategy.md"],
    },
    {
        "name": "example 02",
        "skill": "make-decision",
        "text": "AWS vs Azure vs GCP for our enterprise migration with HIPAA workloads",
        "expect": {
            "type": "Multi-Option Selection",
            "framework": "Weighted Criteria Matrix",
            "criteria": "Tech Stack / Framework Choice",
            "options": ["AWS", "Azure", "GCP"],
            "biases": ["Anchoring Effect", "Availability Heuristic", "Confirmation Bias"],
        },
        "docs": ["examples/02-cloud-migration.md"],
    },
    {
        "name": "example 03",
        "skill": "make-decision",
        "text": "hiring senior software engineer from 3 finalists with payments domain",
        "expect": {
            "type": "Multi-Option Selection",
            "framework": "Weighted Criteria Matrix",
            "criteria": "Hiring Decision",
            "biases": ["Anchoring Effect", "Confirmation Bias", "Availability Heuristic"],
        },
        "docs": ["examples/03-hiring-decision.md"],
    },
    {
        "name": "example 04",
        "skill": "make-decision",
        "text": "allocate 10 engineers across 5 competing projects with constraints",
        "expect": {
            "type": "Resource Allocation",
            "framework": "Expected Value Calculation",
            "criteria": "Investment / Resource Allocation",
            "biases": ["Sunk Cost Fallacy", "Status Quo Bias", "Overconfidence"],
        },
        "docs": ["examples/04-budget-allocation.md"],
    },
    {
        "name": "example 05",
        "skill": "code-solving",
        "text": ("My API sometimes returns stale data after updates. POST /users/{id} succeeds "
                 "(200 OK) but a GET /users/{id} right after returns old data for ~30 seconds, "
                 "then corrects itself."),
        "args": ["--type", "debug", "--no-context"],
        "expect": {
            "type": "debug",
            "techniques": ["Minimal Reproduction", "Check Recent Changes", "Divide and Conquer"],
            "biases": ["Anchoring on the First Clue", "Confirmation Bias in Debugging"],
        },
        "docs": ["examples/05-debugging-race-condition.md"],
    },
]


def run(sample, cwd):
    script = SKILLS_DIR / sample["skill"] / "scripts" / "search.py"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, str(script), "--stdin", "--plan", "--json", *sample.get("args", [])],
        input=sample["text"], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)


def extract(skill, plan):
    """The fields the samples show, from one skill's --json plan."""
    if skill == "make-decision":
        return {
            "type": plan["decision_type"]["name"],
            "framework": plan["framework"]["name"],
            "criteria": plan["criteria"]["domain"],
            "options": plan.get("options", []),
            "biases": [b["bias"] for b in plan.get("bias_warnings", [])],
        }
    if skill == "problem-solving-pro":
        return {
            "type": plan["problem_type"]["name"],
            "category": plan["problem_category"],
            "decomposition": plan["decomposition"]["primary"],
            "biases": [b["bias"] for b in plan.get("bias_warnings", [])],
        }
    if skill == "code-solving":
        context = plan.get("context") or {}
        return {
            "type": plan["task"]["type"],
            "error": (plan.get("errors") or [{}])[0].get("error", ""),
            "locations": [f"{loc['file']}:{loc['line']}" for loc in context.get("locations", [])],
            "checks": [c["command"] for c in plan.get("commands", [])],
            "techniques": [t["name"] for t in plan.get("techniques", [])],
            "biases": [b["name"] for b in plan.get("biases", [])],
        }
    raise ValueError(f"no extractor for skill {skill!r}")


def compare(want, got):
    """Problems where the script's answer differs from the expected values.

    Lists must contain the expected items (order does not matter, and the
    script may return more, e.g. a fourth bias at a deeper depth)."""
    problems = []
    for key, value in want.items():
        actual = got.get(key)
        if isinstance(value, list):
            missing = [v for v in value if v not in (actual or [])]
            if missing:
                problems.append(f"{key}: expected {value}, script gives {actual}")
        elif actual != value:
            problems.append(f"{key}: expected {value!r}, script gives {actual!r}")
    return problems


def doc_values(want):
    for value in want.values():
        if isinstance(value, list):
            yield from value
        else:
            yield value


def check(fail):
    for sample in SAMPLES:
        label = f"sample '{sample['name']}' ({sample['skill']})"
        with tempfile.TemporaryDirectory() as tmp:
            for rel_path, content in sample.get("project", {}).items():
                path = Path(tmp, rel_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            try:
                got = extract(sample["skill"], run(sample, tmp))
            except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
                fail(f"{label}: the script failed: {exc}")
                continue
        for problem in compare(sample["expect"], got):
            fail(f"{label}: {problem}; update the sample in {', '.join(sample['docs'])} "
                 "and the expected values in scripts/test_doc_samples.py")
        for doc in sample["docs"]:
            text = (ROOT / doc).read_text(encoding="utf-8")
            for value in doc_values(sample["expect"]):
                if value not in text:
                    fail(f"{doc}: {label} should show '{value}' (an expected value in "
                         "scripts/test_doc_samples.py)")


def main():
    errors = []
    check(errors.append)
    if errors:
        print(f"{len(errors)} problem(s) with the doc samples:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"doc samples OK ({len(SAMPLES)} requests re-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
