#!/usr/bin/env python3
"""Smoke-test every skill's search.py so broken scripts or CSVs fail CI.

Discovers skills generically (.agents/skills/*/scripts/search.py), so new
skills are covered without editing this file. Uses only the standard library.

Usage: python3 scripts/smoke_test_skills.py
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, ".agents", "skills")
QUERIES = [
    "should we migrate to microservices",
    "revenue dropped 20% despite market growth",
    "nên chọn AWS hay GCP",
]
DEPTHS = ["quick", "standard", "deep", "executive"]


def run(script, args, cwd):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, script] + args,
        cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


def cases():
    for q in QUERIES:
        yield [q]
        yield [q, "--json"]
        for fmt in ("ascii", "markdown"):
            yield [q, "--plan", "--format", fmt]
        for depth in DEPTHS:
            yield [q, "--plan", "--depth", depth]


def main():
    skills = sorted(
        name for name in os.listdir(SKILLS_DIR)
        if os.path.isfile(os.path.join(SKILLS_DIR, name, "scripts", "search.py"))
    )
    if not skills:
        print("no skills with scripts/search.py found", file=sys.stderr)
        return 1

    failures = 0
    total = 0
    for skill in skills:
        script = os.path.join(SKILLS_DIR, skill, "scripts", "search.py")
        # Run from a temp dir so nothing (journals, plans) leaks into the repo.
        with tempfile.TemporaryDirectory() as tmp:
            for args in cases():
                total += 1
                code, out, err = run(script, args, tmp)
                problem = None
                if code != 0:
                    problem = "exit code %d\n%s" % (code, err.strip())
                elif not out.strip():
                    problem = "empty output"
                elif "--json" in args:
                    try:
                        json.loads(out)
                    except ValueError as e:
                        problem = "invalid JSON: %s" % e
                if problem:
                    failures += 1
                    print("FAIL %s %s: %s" % (skill, args, problem))
        print("ok   %s" % skill)

    print("%d/%d checks passed" % (total - failures, total))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
