#!/usr/bin/env python3
"""Regression tests for the skill engines (classification, reasoning rules, output paths).

Usage: python3 scripts/test_skill_engines.py   (standard library only)

Each skill ships modules named core/advisor/search, so they are loaded one
skill at a time with load_skill() instead of plain imports.
"""

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
MODULES = ("core", "advisor", "search")


def load_skill(name):
    """Import a skill's core and advisor modules in isolation."""
    for mod in MODULES:
        sys.modules.pop(mod, None)
    path = str(SKILLS / name / "scripts")
    sys.path.insert(0, path)
    try:
        core = importlib.import_module("core")
        advisor = importlib.import_module("advisor")
    finally:
        sys.path.remove(path)
        for mod in MODULES:
            sys.modules.pop(mod, None)
    return core, advisor


def run_script(script, args, cwd):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(script)] + args, cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8")


class ProblemSolvingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.advisor = load_skill("problem-solving-pro")
        cls.engine = cls.advisor.ProblemSolvingAdvisor()

    def plan(self, query, **kwargs):
        return self.engine.generate(query, **kwargs)

    def test_tokenizer_keeps_short_tech_terms_and_stems(self):
        tokens = self.core.tokenize("CI is red, DB declining; declined; decline")
        self.assertIn("ci", tokens)
        self.assertIn("db", tokens)
        self.assertNotIn("is", tokens)
        self.assertEqual(tokens.count(self.core.stem("decline")), 3)

    def test_every_category_has_a_reasoning_rule(self):
        for category in self.core.category_names():
            with self.subTest(category=category):
                rule = self.engine._find_reasoning_rule(category)
                self.assertEqual(rule.get("Problem_Category"), category)

    def test_auto_classification(self):
        cases = [
            ("Revenue dropped 20% despite market growth", "Diagnostic", "Business Performance"),
            ("Customer churn increased after the pricing change", "Diagnostic", "Business Performance"),
            ("Should we expand into the Japanese market next year", "Opportunity", "Market Entry Strategy"),
            ("Cut operating costs by 15% without layoffs", None, "Cost Reduction"),
            ("Forecast demand for next quarter", "Prediction", "Data / Analytics Problem"),
            ("Should we acquire our main competitor", None, "Partnership / M&A"),
            ("The engineering team resists the reorganization", None, "Organizational Change"),
            ("New EU regulation requires changes to how we store data", None, "Policy / Public Sector"),
            ("Production outage took checkout down for 3 hours", "Diagnostic", "Crisis / Turnaround"),
            ("Design a better onboarding flow for new users", "Design", "Product Development"),
        ]
        for query, ptype, category in cases:
            with self.subTest(query=query):
                plan = self.plan(query)
                if ptype:
                    self.assertEqual(plan["problem_type"]["name"], ptype)
                self.assertEqual(plan["problem_category"], category)
                self.assertTrue(plan["classification"]["rule_applied"])

    def test_reasoning_rule_drives_framework_choice(self):
        plan = self.plan("Revenue dropped 20% despite market growth")
        self.assertEqual(plan["decomposition"]["primary"], "Profitability Tree")
        self.assertEqual(plan["analysis"]["primary_tool"], "Benchmarking")
        self.assertNotIn("Profitability Tree", plan["decomposition"]["alternatives"])

    def test_explicit_type_and_category_override_detection(self):
        plan = self.plan("something vague", problem_type="design", category="product development")
        self.assertEqual(plan["problem_type"]["name"], "Design")
        self.assertEqual(plan["problem_category"], "Product Development")
        self.assertEqual(plan["classification"]["type_source"], "explicit")
        self.assertEqual(plan["classification"]["category_source"], "explicit")

    def test_unknown_type_or_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.plan("x", problem_type="Nope")
        with self.assertRaises(ValueError):
            self.plan("x", category="Nope")

    def test_unmatched_query_falls_back_to_defaults(self):
        plan = self.plan("zzz qqq")
        self.assertEqual(plan["problem_category"], "General")
        self.assertFalse(plan["classification"]["rule_applied"])

    def test_slugify_cannot_escape_output_dir(self):
        for name in ("../../etc/passwd", "a/b\\c", "..", "", "   "):
            with self.subTest(name=name):
                slug = self.core.slugify(name)
                self.assertTrue(slug)
                self.assertNotIn("/", slug)
                self.assertNotIn("\\", slug)
                self.assertNotEqual(slug, "..")

    def test_persist_stays_inside_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.plan("Revenue dropped", project_name="../../escape")
            path = Path(self.advisor.persist_plan(plan, tmp)).resolve()
            self.assertIn(Path(tmp).resolve(), path.parents)


class MakeDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.advisor = load_skill("make-decision")

    def plan(self, query, decision_type=None):
        return self.advisor.DecisionAdvisor(query, decision_type=decision_type).generate()

    def test_classification(self):
        cases = [
            ("Postgres vs MongoDB for our app", "Binary Choice"),
            ("React vs Vue vs Angular", "Multi-Option Selection"),
            ("should we use microservices or a monolith", "Binary Choice"),
            ("Which cloud: AWS, Azure or GCP", "Multi-Option Selection"),
            ("How should we split the Q3 budget across teams", "Resource Allocation"),
            ("We need to decide fast, the offer expires Friday", "Time-Pressured Decision"),
            ("Board must reach consensus on the new CEO", "Group / Stakeholder Decision"),
            ("Launch now with unknown demand and incomplete data", "Decision Under Uncertainty"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(self.plan(query)["decision_type"]["name"], expected)

    def test_recommended_framework_wins(self):
        plan = self.plan("Postgres vs MongoDB for our app")
        self.assertEqual(plan["framework"]["name"], "Pros-Cons-Fixes Analysis")
        self.assertIn("Pre-Mortem Decision Test", plan["framework"]["alternatives"])

    def test_explicit_type(self):
        plan = self.plan("anything", decision_type="strategic direction")
        self.assertEqual(plan["decision_type"]["name"], "Strategic Direction")
        with self.assertRaises(ValueError):
            self.plan("anything", decision_type="Nope")


class OutputLocationTests(unittest.TestCase):
    """Plans and journals must land in the project even when the AI cd's into the skill."""

    def test_outputs_go_to_project_root_from_inside_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            for name in ("problem-solving-pro", "make-decision"):
                shutil.copytree(SKILLS / name, project / ".claude" / "skills" / name,
                                ignore=shutil.ignore_patterns("__pycache__"))

            ps = project / ".claude/skills/problem-solving-pro/scripts"
            r = run_script(ps / "search.py", ["revenue dropped", "--plan", "--persist", "-p", "demo"], cwd=ps)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((project / "solving-plans/demo/PLAN.md").exists())
            self.assertFalse((ps / "solving-plans").exists())

            md = project / ".claude/skills/make-decision/scripts"
            r = run_script(md / "search.py", ["--journal", "pick a database"], cwd=md)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(list((project / ".decisions").glob("*.md")))
            self.assertFalse((md / ".decisions").exists())

    def test_cli_rejects_unknown_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_script(SKILLS / "problem-solving-pro/scripts/search.py",
                           ["x", "--plan", "--type", "Nope"], cwd=tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("unknown problem type", r.stderr)
            r = run_script(SKILLS / "make-decision/scripts/search.py",
                           ["x", "--plan", "--type", "Nope"], cwd=tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("unknown decision type", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
