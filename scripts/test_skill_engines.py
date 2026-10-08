#!/usr/bin/env python3
"""Regression tests for the skill engines (classification, reasoning rules, output paths).

Usage: python3 scripts/test_skill_engines.py   (standard library only)

Each skill ships modules named core/advisor/search, so they are loaded one
skill at a time with load_skill() instead of plain imports.
"""

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Importing skill modules must not leave __pycache__ inside the skill folders
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
MODULES = ("core", "context", "workspace", "advisor", "search")


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


def git_available():
    return shutil.which("git") is not None


def make_repo(root, files, message="initial"):
    """Commit files into a git repo at root (created if needed)."""
    env = dict(os.environ, GIT_AUTHOR_NAME="Dev", GIT_AUTHOR_EMAIL="dev@example.com",
               GIT_COMMITTER_NAME="Dev", GIT_COMMITTER_EMAIL="dev@example.com")
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, env=env)
        subprocess.run(["git", "-C", str(root), "config", "core.autocrlf", "false"], check=True)
    for name, content in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(content.encode("utf-8"))
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", message], check=True, env=env)


class CodeContextTests(unittest.TestCase):
    """The plan's "Context from the project": facts found in the code and git."""

    @classmethod
    def setUpClass(cls):
        sys.modules.pop("context", None)
        path = str(SKILLS / "code-solving" / "scripts")
        sys.path.insert(0, path)
        try:
            cls.context = importlib.import_module("context")
        finally:
            sys.path.remove(path)
            sys.modules.pop("context", None)
        cls.core, cls.advisor = load_skill("code-solving")
        cls.engine = cls.advisor.CodeSolvingAdvisor()

    FILES = {
        "app/orders.py": "def get_total(items):\n    return items[0].price\n",
        "app/json/decoder.py": "x = 1\n",
        "src/main/java/com/shop/OrderService.java":
            "package com.shop;\nclass OrderService {\n  public int getTotal() {\n    return items.get(0).price;\n  }\n}\n",
        "web/src/UserList.tsx": "export function UserList(props) {\n  return props.users.map(u => u.name)\n}\n",
        "main.go": "package main\n\nfunc main() {\n\tvar m map[string]int\n\tm[\"a\"] = 1\n}\n",
        "src/lib.rs": "fn parse() {\n    let x: i32 = \"a\".parse().unwrap();\n}\n",
    }

    def write(self, root, files):
        for name, content in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(content.encode("utf-8"))

    def test_trace_frames_resolve_to_project_lines(self):
        trace = (
            'Traceback (most recent call last):\n'
            '  File "/home/ci/work/shop/app/orders.py", line 2, in get_total\n'
            '  File "/usr/lib/python3.11/json/decoder.py", line 337, in decode\n'
            "\tat java.base/java.util.ArrayList.get(ArrayList.java:427)\n"
            "\tat com.shop.OrderService.getTotal(OrderService.java:4)\n"
            "    at UserList (webpack:///./web/src/UserList.tsx:2:22)\n"
            "    at renderWithHooks (node_modules/react-dom/cjs/react-dom.development.js:14985:18)\n"
            "\t/home/runner/build/main.go:5 +0x1d\n"
            "  --> src/lib.rs:2:18\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, self.FILES)
            files = self.context.project_files(root, False)
            found = [(loc["file"], loc["line"]) for loc in self.context.trace_locations(trace, files, root)]
            self.assertEqual(found, [("app/orders.py", 2), ("src/main/java/com/shop/OrderService.java", 4),
                                     ("web/src/UserList.tsx", 2), ("main.go", 5), ("src/lib.rs", 2)])
            first = self.context.trace_locations(trace, files, root)[0]
            self.assertEqual(first["code"], "return items[0].price")
            self.assertEqual(first["func"], "get_total")

    def test_library_frames_never_match_project_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, self.FILES)
            files = self.context.project_files(root, False)
            trace = 'File "/usr/lib/python3.11/json/decoder.py", line 1, in decode'
            self.assertEqual(self.context.trace_locations(trace, files, root), [])
            # ...but a project folder that merely looks like one still resolves
            self.assertEqual(self.context.resolve("src/lib/python_utils.py", ["src/lib/python_utils.py"], root),
                             "src/lib/python_utils.py")

    def test_named_files_and_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, self.FILES)
            files = self.context.project_files(root, False)
            text = "TypeError in UserList.tsx when OrderService.getTotal runs get_total"
            self.assertEqual(self.context.named_files(text, files, root), ["web/src/UserList.tsx"])
            self.assertEqual(self.context.candidate_symbols(text), ["UserList", "OrderService", "getTotal", "get_total"])
            self.assertEqual(self.context.candidate_symbols("NullPointerException TypeError the login page"), [])

    def test_plan_context_from_git(self):
        if not git_available():
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, self.FILES, "add orders")
            plan = self.engine.generate(
                'getTotal fails:\n  File "app/orders.py", line 2, in get_total', task_type="debug", project_dir=tmp)
            ctx = plan["context"]
            self.assertEqual(ctx["locations"][0]["file"], "app/orders.py")
            symbols = {s["name"]: s for s in ctx["symbols"]}
            self.assertEqual(symbols["getTotal"]["defined"], ["src/main/java/com/shop/OrderService.java:3"])
            self.assertEqual(symbols["get_total"]["defined"], ["app/orders.py:1"])
            self.assertEqual(ctx["commits"][0]["subject"], "add orders")
            self.assertEqual(ctx["tree"]["branch"], "main")
            text = self.advisor.format_markdown(plan)
            self.assertIn("### Context from the project", text)
            self.assertIn("`app/orders.py:2` in `get_total`: `return items[0].price`", text)

            plan_dir, _, _ = self.advisor.persist_step_by_step(plan, tmp)
            change_map = (Path(plan_dir) / "02-CHANGE-MAP.md").read_text(encoding="utf-8")
            self.assertIn("`app/orders.py:2` | in the stack trace", change_map)

            plain = self.engine.generate("getTotal fails", task_type="debug", project_dir=tmp, context=False)
            self.assertEqual(plain["context"], {})
            self.assertNotIn("Context from the project", self.advisor.format_markdown(plain))

    def test_review_includes_diff_and_its_areas_first(self):
        if not git_available():
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, {"src/auth/login.py": "def login(u, p):\n    return check(u, p)\n"})
            subprocess.run(["git", "-C", tmp, "checkout", "-q", "-b", "feature"], check=True)
            make_repo(root, {"src/auth/login.py": "def login(u, p):\n    t = eval(u)\n    return check(u, p)\n",
                             "migrations/002.sql": "ALTER TABLE users DROP COLUMN email;\n"}, "risky change")
            # Plans and AI tool folders left untracked do not count as the change under review
            (root / "coding-plans/x").mkdir(parents=True)
            (root / "coding-plans/x/PLAN.md").write_text("notes", encoding="utf-8")
            (root / ".claude/skills/a").mkdir(parents=True)
            (root / ".claude/skills/a/SKILL.md").write_text("x", encoding="utf-8")
            plan = self.engine.generate("review my branch", task_type="review", project_dir=tmp)
            diff = plan["context"]["diff"]
            self.assertEqual(diff["label"], "main...HEAD")
            self.assertEqual(sorted(f["file"] for f in diff["files"]), ["migrations/002.sql", "src/auth/login.py"])
            areas = {a["area"]: a["reasons"] for a in diff["areas"]}
            self.assertIn("src/auth/login.py adds `eval(`", areas["Security"])
            self.assertIn("Data Safety", areas)
            self.assertIn("no test files", areas["Tests"][0])
            self.assertEqual([r["area"] for r in plan["review"]][:3], ["Security", "Data Safety", "Tests"])

            # Uncommitted changes win in auto mode, new untracked files included;
            # risky strings in tests and comments are not flagged
            (root / "src/auth/login.py").write_text("def login(u, p):\n    return True\n", encoding="utf-8")
            (root / "src/jobs.py").write_text("# eval( is banned here\nimport asyncio\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests/test_login.py").write_text("assert eval('1') == 1\n", encoding="utf-8")
            uncommitted = self.context.review_diff(root)
            self.assertEqual(uncommitted["label"], "uncommitted changes")
            new_files = {f["file"] for f in uncommitted["files"] if f.get("new")}
            self.assertEqual(new_files, {"src/jobs.py", "tests/test_login.py"})
            areas = {a["area"]: a["reasons"] for a in uncommitted["areas"]}
            self.assertEqual(areas["Security"], ["src/auth/login.py"])
            self.assertIn("src/jobs.py adds `asyncio`", areas["Concurrency"])
            self.assertEqual(self.context.review_diff(root, "main")["label"], "main")
            with self.assertRaises(ValueError):
                self.context.review_diff(root, "--output=/tmp/x")

    def test_not_a_git_repo_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.engine.generate("TypeError in UserList.tsx", task_type="debug", project_dir=tmp)
            self.assertIs(plan["context"]["git"], False)
            self.assertIn("Not a git repository", self.advisor.format_markdown(plan))

    def test_cli_context_and_bad_diff_base(self):
        if not git_available():
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(Path(tmp), self.FILES)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, str(SKILLS / "code-solving/scripts/search.py"), "--stdin", "--context"],
                               input='  File "app/orders.py", line 2'.encode("utf-8"), cwd=tmp, env=env,
                               capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("app/orders.py:2", r.stdout.decode("utf-8"))
            r = run_script(SKILLS / "code-solving/scripts/search.py",
                           ["review", "--plan", "--type", "review", "--diff=-x"], cwd=tmp)
            self.assertEqual(r.returncode, 2)
            self.assertIn("invalid --diff base", r.stderr)


class WorkspaceStatusTests(unittest.TestCase):
    """--status / --done: resume a saved workspace at the first gate not met."""

    SCRIPT = SKILLS / "code-solving/scripts/search.py"

    @classmethod
    def setUpClass(cls):
        sys.modules.pop("workspace", None)
        path = str(SKILLS / "code-solving" / "scripts")
        sys.path.insert(0, path)
        try:
            cls.ws = importlib.import_module("workspace")
        finally:
            sys.path.remove(path)
            sys.modules.pop("workspace", None)

    def cli(self, cwd, *args, stdin=None):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(self.SCRIPT)] + list(args), cwd=cwd, env=env, capture_output=True,
                           input=(stdin or "").encode("utf-8"))
        return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")

    def test_progress_and_marking_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = self.cli(tmp, "panic: assignment to entry in nil map", "--plan", "--persist",
                                    "--step-docs", "-p", "worker panic")
            self.assertEqual(code, 0, err)
            plan_dir = Path(tmp) / "coding-plans" / "worker-panic"
            self.assertTrue((plan_dir / ".workspace.json").exists())

            status = self.ws.workspace_status(plan_dir)
            self.assertEqual(status["type"], "debug")
            self.assertEqual([r["label"] for r in status["rows"]][:3],
                             ["1. Define", "2. Decompose", "3-4. Prioritize & Plan"])
            self.assertEqual(status["next"]["label"], "1. Define")
            self.assertEqual({r["filled"] for r in status["rows"]}, {False})

            define = plan_dir / "01-DEFINE.md"
            define.write_text(define.read_text(encoding="utf-8") + "\nRepro: go test ./worker\n", encoding="utf-8")
            code, out, _ = self.cli(tmp, "--done", "define", "-p", "worker panic")
            self.assertEqual(code, 0)
            self.assertIn("Gate met: 1. Define", out)
            self.assertIn("### Next: 2. Decompose", out)
            self.assertIn("**Gate:** A change map", out)
            self.assertIn("--done 2 -p worker-panic", out)

            # 3 and 4 share a row; ticking either ticks it
            self.ws.mark(plan_dir, "2")
            self.ws.mark(plan_dir, "4")
            status = self.ws.workspace_status(plan_dir)
            self.assertEqual(status["next"]["label"], "5. Execute")
            self.assertTrue(status["rows"][0]["filled"])

            # Saving again keeps the notes and their "filled" state
            self.cli(tmp, "panic: assignment to entry in nil map", "--plan", "--persist", "--step-docs", "-p", "worker panic")
            self.assertTrue(self.ws.workspace_status(plan_dir)["rows"][0]["filled"])

            self.ws.mark(plan_dir, "execute", done=False)
            for step in ("5", "6", "7"):
                self.ws.mark(plan_dir, step)
            self.assertTrue(self.ws.workspace_status(plan_dir)["done"])
            with self.assertRaises(ValueError):
                self.ws.step_number("8")

    def test_picking_the_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = self.cli(tmp, "--status")
            self.assertEqual(code, 1)
            self.assertIn("No saved workspace", err)
            self.cli(tmp, "worker crashes with nil map", "--plan", "--persist", "--step-docs", "-p", "worker panic")
            self.cli(tmp, "add csv export", "--plan", "--persist", "--step-docs", "-p", "csv export")
            base = Path(tmp)
            self.assertEqual(self.ws.pick_workspace(base, "continue the worker fix").name, "worker-panic")
            self.assertEqual(self.ws.pick_workspace(base, "", "csv-export").name, "csv-export")
            self.assertIsNone(self.ws.pick_workspace(base, "", "nope"))
            code, out, _ = self.cli(tmp, "--stdin", "--status", stdin="the csv export please")
            self.assertEqual(code, 0)
            self.assertIn("## Workspace: csv-export", out)
            self.assertIn("Other workspaces: `worker-panic`", out)
            code, _, err = self.cli(tmp, "--status", "-p", "nope")
            self.assertEqual(code, 1)
            self.assertIn("csv-export", err)

    def test_workspaces_saved_before_tracking_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.cli(tmp, "fix login", "--plan", "--persist", "--step-docs", "-p", "old")
            plan_dir = Path(tmp) / "coding-plans" / "old"
            (plan_dir / ".workspace.json").unlink()
            status = self.ws.workspace_status(plan_dir)
            self.assertEqual({r["filled"] for r in status["rows"]}, {None})
            self.assertIn("| 1. Define | `01-DEFINE.md` | ? | ☐ |", self.ws.format_status(status))


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
            path, written = self.advisor.persist_plan(plan, tmp)
            self.assertTrue(written)
            self.assertIn(Path(tmp).resolve(), Path(path).resolve().parents)


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


class CodeSolvingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.advisor = load_skill("code-solving")
        cls.engine = cls.advisor.CodeSolvingAdvisor()

    def test_task_type_references_resolve(self):
        """Every technique, test, principle, bias, review area and artifact a type names exists."""
        core = self.core
        for row in core.load_csv("task-types"):
            for col, domains in (("Techniques", ["debugging", "changes"]), ("Testing", ["testing"]),
                                 ("Principles", ["principles"]), ("Biases", ["biases"]),
                                 ("Review Focus", ["review"]), ("Artifact", ["artifacts"])):
                names = [n.strip() for n in row[col].split(";") if n.strip()]
                found = sum(len(core.find_named(d, names)) for d in domains)
                with self.subTest(type=row["Type"], column=col):
                    self.assertEqual(found, len(names), f"unresolved names in {names}")

    def test_classification(self):
        cases = [
            ("TypeError in checkout after the last deploy, users see a blank page", "debug"),
            ("NullPointerException in OrderService", "debug"),
            ("sửa lỗi đăng nhập bị lỗi", "debug"),
            ("add a settings page so users can change their email", "feature"),
            ("implement OAuth login with Google", "feature"),
            ("refactor the payment module", "refactor"),
            ("API latency spiked after deploy", "performance"),
            ("Postgres query is slow on the orders page", "performance"),
            ("memory leak in node worker", "performance"),
            ("tối ưu trang chậm", "performance"),
            ("test sometimes fails in CI", "flaky-test"),
            ("site is down, 500s for all users", "incident"),
            ("upgrade React 17 to 18", "migration"),
            ("nâng cấp thư viện", "migration"),
            ("review my PR", "review"),
            ("review giúp code này", "review"),
            # Real-world phrasings; add a case here whenever a request is misclassified
            ("TypeError: Cannot read properties of undefined (reading 'map') in UserList.tsx", "debug"),
            ("panic: runtime error: index out of range [3] with length 3", "debug"),
            ("ModuleNotFoundError: No module named 'requests'", "debug"),
            ("the login button does nothing when clicked", "debug"),
            ("form submit doesn't work on Safari", "debug"),
            ("the export stopped working after yesterday's merge", "debug"),
            ("app freezes when I open a large file", "debug"),
            ("totals are incorrect when a discount is applied", "debug"),
            ("nút lưu không hoạt động", "debug"),
            ("implement pagination for /api/orders", "feature"),
            ("write a CLI command to export reports as CSV", "feature"),
            ("write unit tests for the parser", "test"),
            ("add tests for UserService", "test"),
            ("support uploading avatars to S3", "feature"),
            ("thêm tính năng xuất file Excel", "feature"),
            ("viết test cho module thanh toán", "test"),
            ("increase test coverage for the payments module", "test"),
            ("how does the auth middleware work", "explain"),
            ("explain what OrderService.getTotal does", "explain"),
            ("giải thích code này làm gì", "explain"),
            ("SQL injection in the search endpoint", "security"),
            ("Dependabot alert: CVE-2024-1234 in lodash", "security"),
            ("our API key was leaked in a commit", "security"),
            ("lỗ hổng XSS ở trang profile", "security"),
            ("fix typo in README", "quick-fix"),
            ("change the button text from Submit to Save", "quick-fix"),
            ("sửa chính tả ở trang chủ", "quick-fix"),
            ("this function is 400 lines, split it up", "refactor"),
            ("extract the payment logic into its own module", "refactor"),
            ("clean up duplicate code in the controllers", "refactor"),
            ("tái cấu trúc module thanh toán", "refactor"),
            ("API p95 latency went from 200ms to 2s", "performance"),
            ("the dashboard takes 10 seconds to load", "performance"),
            ("memory usage keeps growing until OOM", "performance"),
            ("fix the slow query in reports", "performance"),
            ("trang chủ load chậm quá", "performance"),
            ("test_user_signup fails randomly on CI", "flaky-test"),
            ("CI passes locally but fails on GitHub Actions", "flaky-test"),
            ("test chạy lúc được lúc không trên CI", "flaky-test"),
            ("production is down, 502 for all users", "incident"),
            ("server production bị sập", "incident"),
            ("move from Python 3.8 to 3.12", "migration"),
            ("switch from MySQL to Postgres", "migration"),
            ("replace moment.js with date-fns", "migration"),
            ("Bump lodash from 4.17.20 to 4.17.21", "migration"),
            ("nâng cấp Next.js lên 14", "migration"),
            ("chuyển từ REST sang GraphQL", "migration"),
            ("review this PR for security issues", "review"),
            ("can you look over my changes before I merge", "review"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                row, source = self.core.classify_task(query)
                self.assertEqual(row["Type"], expected)
                self.assertEqual(source, "auto")

    def test_known_errors_are_recognized(self):
        cases = {
            "TypeError: Cannot read properties of undefined (reading 'map')": "TypeError: Cannot read properties of undefined/null",
            "panic: assignment to entry in nil map": "panic: assignment to entry in nil map",
            "ModuleNotFoundError: No module named 'requests'": "ModuleNotFoundError / ImportError",
            "fatal error: all goroutines are asleep - deadlock!": "fatal error: all goroutines are asleep - deadlock!",
            "ERROR: duplicate key value violates unique constraint \"users_email_key\"": "Unique constraint violation (duplicate key)",
            "pod is in CrashLoopBackOff": "Kubernetes CrashLoopBackOff",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(self.core.match_errors(text)[0]["Error"], expected)
        self.assertEqual(self.core.match_errors("add a settings page"), [])
        for row in self.core.load_csv("errors"):
            with self.subTest(error=row["Error"]):
                for col in ("Meaning", "Likely Causes", "First Checks", "Fix"):
                    self.assertTrue(row[col].strip(), col)

    def test_known_error_feeds_the_plan_and_hypothesis_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.engine.generate("panic: assignment to entry in nil map in worker", project_dir=tmp)
            self.assertEqual(plan["task"]["type"], "debug")
            text = self.advisor.format_markdown(plan)
            self.assertIn("### Known error: panic: assignment to entry in nil map (Go)", text)
            plan_dir, _, _ = self.advisor.persist_step_by_step(plan, tmp)
            log = (Path(plan_dir) / "04-LOG.md").read_text(encoding="utf-8")
            self.assertIn("| 1 | var m map[K]V or a struct field map never initialized with make |", log)

    def test_quick_fix_plan_is_light(self):
        plan = self.engine.generate("fix typo in README", depth="standard")
        self.assertEqual(plan["task"]["type"], "quick-fix")
        self.assertEqual([s["name"] for s in plan["steps"]], ["Define", "Execute", "Verify", "Communicate"])
        self.assertIn("Small change", self.advisor.format_markdown(plan))
        deep = self.engine.generate("fix typo in README", depth="deep")
        self.assertEqual(len(deep["steps"]), 7)
        self.assertEqual(plan["artifact"]["name"], "Commit Message")

    def test_new_types_have_their_own_hand_off(self):
        expected = {"test": "Pull Request Description", "explain": "Code Explanation",
                    "security": "Security Fix Note", "quick-fix": "Commit Message"}
        with tempfile.TemporaryDirectory() as tmp:
            for task_type, artifact in expected.items():
                with self.subTest(type=task_type):
                    plan = self.engine.generate("x", task_type=task_type, project_dir=tmp, context=False)
                    self.assertEqual(plan["artifact"]["name"], artifact)
                    self.assertTrue(plan["artifact"]["structure"])
            plan = self.engine.generate("x", task_type="explain", project_name="ex", context=False)
            _, files, _ = self.advisor.persist_step_by_step(plan, tmp)
            self.assertIn("06-EXPLANATION.md", files)

    def test_unmatched_query_says_so(self):
        row, source = self.core.classify_task("zzz qqq")
        self.assertEqual(source, "default")
        plan = self.engine.generate("zzz qqq")
        self.assertIn("--type", self.advisor.format_markdown(plan))

    def test_explicit_type(self):
        plan = self.engine.generate("anything", task_type="Incident")
        self.assertEqual(plan["task"]["type"], "incident")
        self.assertEqual(plan["task"]["source"], "explicit")
        self.assertEqual(plan["artifact"]["name"], "Blameless Postmortem")
        with self.assertRaises(ValueError):
            self.engine.generate("anything", task_type="nope")

    def test_every_step_has_guidance_and_gate(self):
        for task_type in self.core.task_type_names():
            plan = self.engine.generate("x", task_type=task_type, depth="deep")
            with self.subTest(type=task_type):
                self.assertEqual([s["name"] for s in plan["steps"]],
                                 ["Define", "Decompose", "Prioritize", "Plan", "Execute", "Verify", "Communicate"])
                for step in plan["steps"]:
                    self.assertTrue(step["guidance"], step["name"])
                    self.assertTrue(step["gate"], step["name"])
                    self.assertNotIn("Gate:", step["guidance"])

    def test_quick_depth_keeps_define_and_verify(self):
        plan = self.engine.generate("fix bug", task_type="debug", depth="quick")
        self.assertEqual([s["name"] for s in plan["steps"]], ["Define", "Execute", "Verify"])

    def test_both_formats_render(self):
        for depth in ("quick", "standard", "deep", "executive"):
            plan = self.engine.generate("API latency spiked", depth=depth)
            self.assertIn("Gate", self.advisor.format_markdown(plan))
            self.assertNotIn("**", self.advisor.format_text(plan))

    def test_split_identifiers(self):
        self.assertEqual(self.core.split_identifiers("NullPointerException in getUserId"),
                         "Null Pointer Exception in get User Id")

    def test_detect_project_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(self.core.detect_project_commands(root), [])
            (root / "package.json").write_text('{"scripts": {"test": "vitest", "lint": "eslint .", "build": "vite build"}}')
            (root / "pnpm-lock.yaml").write_text("")
            (root / "go.mod").write_text("module x\n")
            (root / "Makefile").write_text("VERSION := 1\ntest:\n\tgo test ./...\nbuild: deps\n\tgo build\n")
            commands = [c for _, c, _ in self.core.detect_project_commands(root)]
            for expected in ("pnpm test", "pnpm lint", "pnpm build", "make test", "make build", "go test ./..."):
                self.assertIn(expected, commands)
            self.assertNotIn("make VERSION", commands)
            self.assertEqual(len(commands), len(set(commands)))
            self.assertIn('pnpm test <file> -t "<name>"', commands)

    def detect(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, content in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(content)
            return {c: (p, s) for p, c, s in self.core.detect_project_commands(root)}

    def test_detect_python_runs_inside_the_project_environment(self):
        for lock, runner in (("uv.lock", "uv run "), ("poetry.lock", "poetry run "), ("pdm.lock", "pdm run ")):
            with self.subTest(lock=lock):
                found = self.detect({"pyproject.toml": "[tool.pytest.ini_options]\n[tool.ruff]\n", lock: ""})
                self.assertIn(runner + "pytest", found)
                self.assertIn(runner + "ruff check .", found)
                self.assertEqual(found[runner + "pytest <file>::<name>"][0], "one test")
        self.assertIn("pytest", self.detect({"pyproject.toml": "[tool.pytest.ini_options]\n"}))

    def test_detect_reads_ci_check_steps(self):
        found = self.detect({".github/workflows/ci.yml": (
            "jobs:\n  t:\n    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - run: npm ci\n"
            "      - run: npm test -- --coverage\n"
            "      - name: checks\n"
            "        run: |\n"
            "          npx eslint . --format=stylish\n"
            "          npx tsc --noEmit\n"
            "      - run: echo done\n"
            "      - run: npm publish\n"
            "      - run: \"golangci-lint run --out-format=github-actions\"\n"
            "      - run: go test ./... -run ${{ matrix.pattern }}\n")})
        self.assertEqual(found["npm test -- --coverage"][0], "test")
        self.assertEqual(found["npx eslint . --format=stylish"][0], "lint")
        self.assertEqual(found["npx tsc --noEmit"][0], "typecheck")
        self.assertEqual(found["golangci-lint run --out-format=github-actions"][0], "lint")
        self.assertEqual(found["npm test -- --coverage"][1], ".github/workflows/ci.yml")
        for skipped in ("npm ci", "echo done", "npm publish"):
            self.assertNotIn(skipped, found)
        self.assertFalse([c for c in found if "${{" in c])

    def test_detect_local_config_wins_over_ci_duplicates(self):
        found = self.detect({"go.mod": "module x\n", ".github/workflows/ci.yml": "steps:\n  - run: go test ./...\n"})
        self.assertEqual(found["go test ./..."][1], "go.mod")

    def test_detect_workspaces_without_root_test_script(self):
        found = self.detect({"package.json": '{"workspaces": ["packages/*"]}', "pnpm-lock.yaml": ""})
        self.assertIn("pnpm -r test", found)
        found = self.detect({"package.json": '{"workspaces": ["packages/*"]}'})
        self.assertIn("npm test --workspaces --if-present", found)

    def test_step_docs_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.engine.generate("site is down", project_name="../checkout outage", task_type="incident")
            plan_dir, files, kept = self.advisor.persist_step_by_step(plan, tmp)
            self.assertEqual(kept, [])
            self.assertIn(Path(tmp).resolve(), Path(plan_dir).resolve().parents)
            self.assertIn("06-POSTMORTEM.md", files)
            self.assertEqual(len(files), 7)
            log = (Path(plan_dir) / "04-LOG.md").read_text(encoding="utf-8")
            self.assertIn("Hypothesis", log)

    def test_verify_checklist_leaves_out_the_single_test_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "go.mod").write_text("module x\n")
            plan = self.engine.generate("fix bug", task_type="debug", project_dir=tmp)
            plan_dir, _, _ = self.advisor.persist_step_by_step(plan, tmp)
            verify = (Path(plan_dir) / "05-VERIFY.md").read_text(encoding="utf-8")
            self.assertIn("`go test ./...`", verify)
            self.assertNotIn("<TestName>", verify)


class SharedHelperTests(unittest.TestCase):
    """The skills each ship their own copy of the text helpers (they are installed independently);
    the copies must be the same code, not merely agree on a few samples."""

    SHARED = ("stem", "tokenize", "fold", "has_accents", "match_tokens", "query_grams", "phrase_tokens",
              "display_width", "pad_display", "wrap_display", "slugify", "default_output_dir", "save_docs",
              "read_stdin_query", "matched_phrases")
    CONSTANTS = ("STOPWORDS", "_SUFFIXES")

    @staticmethod
    def definitions(skill):
        """{name: ast.dump of its top-level definition} in a skill's core.py."""
        import ast
        tree = ast.parse((SKILLS / skill / "scripts" / "core.py").read_text(encoding="utf-8"))
        found = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                found[node.name] = ast.dump(node)
            elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                found[node.targets[0].id] = ast.dump(node)
        return found

    def test_shared_helpers_have_identical_source(self):
        skills = ("problem-solving-pro", "make-decision", "code-solving")
        defs = {skill: self.definitions(skill) for skill in skills}
        for name in self.SHARED + self.CONSTANTS:
            for skill in skills:
                with self.subTest(helper=name, skill=skill):
                    self.assertIn(name, defs[skill])
                    self.assertEqual(defs[skill][name], defs[skills[0]][name],
                                     f"{name} in {skill} differs from {skills[0]}")

    def test_slugify_cannot_escape_and_never_is_empty(self):
        for name in ("problem-solving-pro", "make-decision", "code-solving"):
            core = load_skill(name)[0]
            for bad in ("../../x", "a/b", "..", "", "!!!"):
                with self.subTest(skill=name, text=bad):
                    slug = core.slugify(bad)
                    self.assertNotIn("/", slug)
                    self.assertNotEqual(slug, "..")
                    self.assertTrue(slug)


class BoxWidthTests(unittest.TestCase):
    """ASCII boxes and tables line up in terminal columns, whatever the Unicode form of the text."""

    TEXT = "Có nên mở rộng sang Nhật Bản 🎯 hay giữ thị trường 中文 hiện tại không?"

    def box_widths(self, skill, text, *args):
        import unicodedata
        core = load_skill(skill)[0]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(SKILLS / skill / "scripts/search.py"), "--stdin"] + list(args),
                               input=unicodedata.normalize("NFD", text).encode("utf-8"), cwd=tmp, env=env,
                               capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        lines = r.stdout.decode("utf-8").splitlines()
        borders = [i for i, line in enumerate(lines) if line.startswith("+=")]
        box = lines[borders[0]:borders[-1] + 1]
        self.assertGreater(len(box), 10)
        return box, {core.display_width(line) for line in box}

    def test_plan_boxes_have_a_straight_right_border(self):
        for skill in ("problem-solving-pro", "make-decision"):
            for depth in ("quick", "standard"):
                with self.subTest(skill=skill, depth=depth):
                    out, widths = self.box_widths(skill, self.TEXT, "--plan", "--depth", depth)
                    self.assertEqual(len(widths), 1, widths)

    def test_display_width(self):
        import unicodedata
        for skill in ("problem-solving-pro", "make-decision", "code-solving"):
            core = load_skill(skill)[0]
            with self.subTest(skill=skill):
                self.assertEqual(core.display_width(unicodedata.normalize("NFD", "Giảm")), 4)
                self.assertEqual(core.display_width("中文🎯"), 6)
                self.assertEqual(core.display_width(core.pad_display(unicodedata.normalize("NFD", "lỗi"), 6)), 6)
                lines = core.wrap_display("một hai ba bốn năm sáu bảy tám chín mười " * 3, 20, "  ", "    ")
                self.assertTrue(all(core.display_width(line) <= 20 for line in lines))
                self.assertTrue(lines[0].startswith("  m") and lines[1].startswith("    "))

    def test_matrix_columns_line_up(self):
        _, advisor = load_skill("make-decision")
        text = advisor.format_matrix(advisor.build_matrix("Nhật Bản hay 中文市场", "Chi phí:2,Rủi ro:1",
                                                          "Nhật Bản:4,3;中文市场:3,5"))
        core = load_skill("make-decision")[0]
        table = [line for line in text.split("Winner")[0].splitlines() if " | " in line]
        positions = {tuple(core.display_width(line[:i]) for i, ch in enumerate(line) if ch == "|")
                     for line in table}
        self.assertEqual(len(positions), 1, table)


class OutputLocationTests(unittest.TestCase):
    """Plans and journals must land in the project even when the AI cd's into the skill."""

    def test_outputs_go_to_project_root_from_inside_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".git").mkdir()
            for name in ("problem-solving-pro", "make-decision", "code-solving"):
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

            cs = project / ".claude/skills/code-solving/scripts"
            r = run_script(cs / "search.py", ["fix login bug", "--plan", "--persist", "--step-docs", "-p", "login"], cwd=cs)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((project / "coding-plans/login/01-DEFINE.md").exists())
            self.assertFalse((cs / "coding-plans").exists())

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
            r = run_script(SKILLS / "code-solving/scripts/search.py",
                           ["x", "--plan", "--type", "Nope"], cwd=tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("unknown task type", r.stderr)


class SavedWorkTests(unittest.TestCase):
    """Re-running a plan must never wipe notes the user wrote into saved files."""

    SKILLS_AND_DIRS = (("problem-solving-pro", "solving-plans"), ("make-decision", "decision-plans"),
                       ("code-solving", "coding-plans"))

    def run_plan(self, skill, cwd, *extra):
        r = run_script(SKILLS / skill / "scripts/search.py",
                       ["login is broken", "--plan", "--persist", "-p", "demo"] + list(extra), cwd=cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_step_docs_keep_existing_files_unless_forced(self):
        for skill, folder in self.SKILLS_AND_DIRS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                self.run_plan(skill, tmp, "--step-docs")
                docs = sorted((Path(tmp) / folder / "demo").glob("0[1-9]-*.md"))
                note = docs[0]
                note.write_text(note.read_text(encoding="utf-8") + "\nMY NOTES\n", encoding="utf-8")

                out = self.run_plan(skill, tmp, "--step-docs")
                self.assertIn("MY NOTES", note.read_text(encoding="utf-8"))
                self.assertIn("--force", out)

                self.run_plan(skill, tmp, "--step-docs", "--force")
                self.assertNotIn("MY NOTES", note.read_text(encoding="utf-8"))

    def test_plan_file_is_kept_unless_forced(self):
        for skill, folder in self.SKILLS_AND_DIRS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                self.run_plan(skill, tmp)
                plan = Path(tmp) / folder / "demo" / "PLAN.md"
                plan.write_text("MY EDITS", encoding="utf-8")
                self.assertIn("Kept the existing plan", self.run_plan(skill, tmp))
                self.assertEqual(plan.read_text(encoding="utf-8"), "MY EDITS")
                self.assertIn("Plan saved to", self.run_plan(skill, tmp, "--force"))
                self.assertNotEqual(plan.read_text(encoding="utf-8"), "MY EDITS")


class StdinInputTests(unittest.TestCase):
    """Slash commands pass the user's text on stdin so the shell never interprets it."""

    HOSTILE = 'TypeError: `touch pwned` at $HOME "x" $(touch pwned2) — lỗi đăng nhập'

    def test_stdin_text_reaches_the_plan_verbatim(self):
        for skill in ("problem-solving-pro", "make-decision", "code-solving"):
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
                r = subprocess.run([sys.executable, str(SKILLS / skill / "scripts/search.py"),
                                    "--stdin", "--plan", "-f", "markdown"],
                                   input=(self.HOSTILE + "\n").encode("utf-8"), cwd=tmp, env=env,
                                   capture_output=True)
                self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
                out = r.stdout.decode("utf-8")
                self.assertIn("`touch pwned`", out if skill != "problem-solving-pro" else out.lower())
                self.assertIn("lỗi", out.lower())
                self.assertEqual(os.listdir(tmp), [])

    def test_workflows_pass_arguments_on_stdin(self):
        """$ARGUMENTS must sit alone inside a quoted heredoc, never on a command line."""
        for path in sorted((ROOT / ".agents" / "workflows").glob("*.md")):
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if "$ARGUMENTS" not in line:
                    continue
                with self.subTest(workflow=path.name, line=i + 1):
                    self.assertEqual(line.strip(), "$ARGUMENTS")
                    self.assertIn(" --stdin ", lines[i - 1])
                    self.assertTrue(lines[i - 1].endswith("<<'TASK'"))
                    self.assertEqual(lines[i + 1], "TASK")

    def test_read_stdin_query_strips_bom_and_whitespace(self):
        import io
        for skill in ("problem-solving-pro", "make-decision", "code-solving"):
            core = load_skill(skill)[0]
            stream = io.TextIOWrapper(io.BytesIO("\ufeff  lỗi `x` $y \n".encode("utf-8")), encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertEqual(core.read_stdin_query(stream), "lỗi `x` $y")

    def test_max_results_must_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            for skill in ("problem-solving-pro", "make-decision", "code-solving"):
                with self.subTest(skill=skill):
                    r = run_script(SKILLS / skill / "scripts/search.py", ["bias", "-n", "0"], cwd=tmp)
                    self.assertEqual(r.returncode, 2)
                    self.assertIn("must be 1 or more", r.stderr)


class ProblemSolvingProTests(unittest.TestCase):
    """problem-solving-pro: Vietnamese and English classification, depth, data references, resume."""

    SCRIPT = SKILLS / "problem-solving-pro/scripts/search.py"

    # (request, problem type, category): half Vietnamese, including text typed without accents
    LABELED = [
        ("Revenue dropped 20% despite market growth", "Diagnostic", "Business Performance"),
        ("Reduce homelessness in our city", "Wicked", "Policy / Public Sector"),
        ("We are running out of cash in 4 months", "Diagnostic", "Crisis / Turnaround"),
        ("Should we enter the Vietnamese market?", "Opportunity", "Market Entry Strategy"),
        ("I'm burned out at work", "Diagnostic", "Organizational Change"),
        ("Our cloud bill doubled in three months", "Diagnostic", "Cost Reduction"),
        ("Cut operating costs by 15% without layoffs", "Well-Structured", "Cost Reduction"),
        ("Forecast demand for next quarter", "Prediction", "Data / Analytics Problem"),
        ("Should we acquire our main competitor", "Opportunity", "Partnership / M&A"),
        ("Negotiate a new contract with our biggest supplier", "Negotiation", "Partnership / M&A"),
        ("Design a better onboarding flow for new users", "Design", "Product Development"),
        ("A startup using AI is disrupting our core business", "Ill-Structured", "Innovation / Disruption"),
        ("Production outage took checkout down for 3 hours", "Diagnostic", "Crisis / Turnaround"),
        ("Employee attrition doubled after the reorganization", "Diagnostic", "Organizational Change"),
        ("Two departments disagree over who owns the marketing budget", "Negotiation", "Organizational Change"),
        ("Optimize warehouse inventory levels to minimize holding cost", "Well-Structured", "Cost Reduction"),
        ("Our dashboard metrics don't match the finance numbers", "Diagnostic", "Data / Analytics Problem"),
        ("doanh thu giảm 20% quý này", "Diagnostic", "Business Performance"),
        ("Mở rộng sang thị trường Nhật Bản", "Opportunity", "Market Entry Strategy"),
        ("Công ty sắp hết tiền mặt", "Diagnostic", "Crisis / Turnaround"),
        ("Cắt giảm chi phí vận hành 15% mà không sa thải", "Well-Structured", "Cost Reduction"),
        ("Dự báo nhu cầu bán hàng quý tới", "Prediction", "Data / Analytics Problem"),
        ("Có nên mua lại đối thủ cạnh tranh không", "Opportunity", "Partnership / M&A"),
        ("Nhân viên nghỉ việc nhiều sau khi tái cấu trúc", "Diagnostic", "Organizational Change"),
        ("Thiết kế tính năng mới cho ứng dụng di động", "Design", "Product Development"),
        ("Đàm phán lại hợp đồng với nhà cung cấp lớn nhất", "Negotiation", "Partnership / M&A"),
        ("Tỷ lệ khách hàng rời bỏ tăng mạnh", "Diagnostic", "Business Performance"),
        ("Hệ thống bị sập, khách hàng không thanh toán được", "Diagnostic", "Crisis / Turnaround"),
        ("Giảm ùn tắc giao thông ở Hà Nội", "Wicked", "Policy / Public Sector"),
        ("Đối thủ dùng AI đang thay đổi cả ngành của chúng tôi", "Ill-Structured", "Innovation / Disruption"),
        ("Nhân viên bị kiệt sức vì quá tải công việc", "Diagnostic", "Organizational Change"),
        ("Hóa đơn cloud tăng gấp đôi", "Diagnostic", "Cost Reduction"),
        ("Số liệu trên dashboard không khớp với báo cáo tài chính", "Diagnostic", "Data / Analytics Problem"),
        ("Hai phòng ban mâu thuẫn về ngân sách marketing", "Negotiation", "Organizational Change"),
        ("doanh thu giam manh sau khi tang gia", "Diagnostic", "Business Performance"),
        ("Tối ưu lịch giao hàng để giảm chi phí vận chuyển", "Well-Structured", "Cost Reduction"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.core, cls.advisor = load_skill("problem-solving-pro")
        cls.engine = cls.advisor.ProblemSolvingAdvisor()

    def cli(self, cwd, *args, stdin=None):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(self.SCRIPT)] + list(args), cwd=cwd, env=env, capture_output=True,
                           input=(stdin or "").encode("utf-8"))
        return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")

    def test_labeled_requests_classify(self):
        vietnamese = sum(1 for q, _, _ in self.LABELED if not q.isascii() or "giam" in q)
        self.assertGreaterEqual(len(self.LABELED), 30)
        self.assertGreaterEqual(vietnamese * 2, len(self.LABELED))
        for query, ptype, category in self.LABELED:
            with self.subTest(query=query):
                plan = self.engine.generate(query)
                self.assertEqual((plan["problem_type"]["name"], plan["problem_category"]), (ptype, category))
                self.assertEqual(plan["classification"]["type_source"], "auto")
                self.assertEqual(plan["classification"]["category_source"], "auto")
                self.assertEqual(plan["hints"], [])

    def test_accents_are_optional(self):
        self.assertEqual(self.core.fold_accents("Giảm chi phí ĐIỆN"), "Giam chi phi DIEN")
        for accented, plain in (("Công ty sắp hết tiền mặt", "Cong ty sap het tien mat"),
                                ("Mở rộng sang thị trường Nhật Bản", "Mo rong sang thi truong Nhat Ban")):
            with self.subTest(query=plain):
                self.assertEqual(self.core.classify_category(plain), self.core.classify_category(accented))

    def test_unmatched_request_tells_the_ai_to_pass_type_and_category(self):
        plan = self.engine.generate("zzz qqq")
        self.assertEqual((plan["classification"]["type_source"], plan["classification"]["category_source"]),
                         ("default", "default"))
        text = self.advisor.format_markdown(plan)
        self.assertIn("No problem type matched clearly. Re-run with `--type`", text)
        self.assertIn("Re-run with `--category`", text)
        for value in self.core.problem_type_names() + self.core.category_names():
            self.assertIn(value, text)
        plan = self.engine.generate("zzz qqq", problem_type="Wicked", category="Policy / Public Sector")
        self.assertEqual(plan["hints"], [])
        self.assertNotIn("Re-run", self.advisor.format_markdown(plan))

    def test_depth_changes_the_plan(self):
        query = "Revenue dropped 20% despite market growth"
        plans = {d: self.engine.generate(query, depth=d) for d in self.advisor.VALID_DEPTHS}
        md = {d: self.advisor.format_markdown(p) for d, p in plans.items()}
        sizes = [len(md[d]) for d in ("quick", "standard", "deep", "executive")]
        self.assertEqual(sizes, sorted(sizes))
        self.assertLess(sizes[0] * 2, sizes[1])
        self.assertLess(sizes[1] * 1.5, sizes[2])
        for heading in ("The 7 Steps", "Problem-Solving Checklist", "Decision Rules", "Prioritization:"):
            self.assertNotIn(heading, md["quick"])
            self.assertIn(heading, md["standard"])
        self.assertIn("First Move", md["quick"])
        self.assertNotIn("Danger zone", md["standard"])
        self.assertIn("Danger zone", md["deep"])
        self.assertIn("Pitfalls:", md["deep"])
        self.assertGreater(len(plans["deep"]["mental_models"]), len(plans["standard"]["mental_models"]))
        self.assertGreater(len(plans["deep"]["bias_warnings"]), len(plans["standard"]["bias_warnings"]))
        self.assertGreater(len(plans["deep"]["decomposition"]["alternatives"]
                               + plans["deep"]["analysis"]["alternatives"]),
                           len(plans["standard"]["decomposition"]["alternatives"]
                               + plans["standard"]["analysis"]["alternatives"]))
        for heading in ("Executive Summary (SCR)", "**Situation:**", "**Complication:**", "**Resolution",
                        "Key Risks", "Decision Needed"):
            self.assertNotIn(heading, md["deep"])
            self.assertIn(heading, md["executive"])
        # ASCII follows the same depth rules, and every box line has the same width
        for depth in ("quick", "executive"):
            box = self.advisor.format_ascii_box(plans[depth]).splitlines()
            self.assertEqual({len(line) for line in box}, {self.advisor.BOX_WIDTH})
        self.assertIn("EXECUTIVE SUMMARY", self.advisor.format_ascii_box(plans["executive"]))

    def test_biases_and_mental_models_come_from_type_and_context(self):
        for query, ptype, category in self.LABELED:
            with self.subTest(query=query):
                plan = self.engine.generate(query)
                self.assertGreaterEqual(len(plan["bias_warnings"]), 3)
                self.assertGreaterEqual(len(plan["mental_models"]), 3)
        rule = self.engine._find_reasoning_rule("Crisis / Turnaround")
        plan = self.engine.generate("Công ty sắp hết tiền mặt")
        first_bias = self.core.split_names(rule["Key_Biases"])[0]
        first_model = self.core.find_record("heuristics", self.core.split_names(rule["Key_Heuristics"])[0])
        self.assertEqual(plan["bias_warnings"][0]["bias"], first_bias)
        self.assertEqual(plan["mental_models"][0]["name"], first_model["Mental Model"])

    def test_every_referenced_name_resolves(self):
        data = SKILLS / "problem-solving-pro" / "data"
        refs = [  # (file, column, separator, domains the names must exist in)
            ("reasoning.csv", "Decomposition_Style", None, ("decomposition", "prioritization")),
            ("reasoning.csv", "Analysis_Priority", None, ("analysis", "prioritization")),
            ("reasoning.csv", "Communication_Style", None, ("communication",)),
            ("reasoning.csv", "Key_Heuristics", ";", ("heuristics",)),
            ("reasoning.csv", "Key_Biases", ";", ("biases",)),
            ("problem-types.csv", "Key Biases", ";", ("biases",)),
            ("problem-types.csv", "Mental Models", ";", ("heuristics",)),
        ]
        checked = 0
        for file, column, sep, domains in refs:
            for row in self.core._load_csv(data / file):
                for name in self.core.split_names(row[column], sep):
                    with self.subTest(file=file, column=column, name=name):
                        self.assertTrue(any(self.core.find_record(d, name) for d in domains),
                                        f"{name!r} in {file}:{column} is not defined in {domains}")
                        checked += 1
        self.assertGreater(checked, 100)

    def test_every_step_is_rendered_with_its_gate(self):
        plan = self.engine.generate("Revenue dropped 20%")
        self.assertEqual([s["number"] for s in plan["methodology"]["steps"]], list(range(1, 8)))
        text = self.advisor.format_markdown(plan)
        for step in plan["methodology"]["steps"]:
            self.assertIn(step["name"], text)
            self.assertIn(step["gate"], text)
        self.assertIn("If revenue problem: decompose price x volume", text)
        self.assertIn("stakes HIGH", text)
        self.assertIn("(auto-detected)", text)

    def test_long_request_is_shortened_in_titles_but_kept_in_files(self):
        query = "Revenue dropped " + " ".join(f"word{i}" for i in range(700))
        plan = self.engine.generate(query)
        self.assertLessEqual(len(plan["project_name"]), 60)
        text = self.advisor.format_markdown(plan)
        self.assertLess(max(len(line) for line in text.splitlines()[:3]), 700)
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.advisor.persist_plan(plan, tmp)
            self.assertIn("word699", Path(path).read_text(encoding="utf-8"))

    def test_json_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(tmp, "--stdin", "--plan", "--json", stdin="Hóa đơn cloud tăng gấp đôi")
            self.assertEqual(code, 0, err)
            plan = json.loads(out)
            self.assertEqual(plan["query"], "Hóa đơn cloud tăng gấp đôi")
            self.assertEqual(plan["problem_category"], "Cost Reduction")
            self.assertEqual(len(plan["methodology"]["steps"]), 7)
            code, out, err = self.cli(tmp, "cloud bill doubled", "--plan", "--json", "--persist", "--step-docs",
                                      "-p", "cloud")
            self.assertEqual(code, 0, err)
            self.assertIn("00-OVERVIEW.md", json.loads(out)["saved"]["written"])
            self.assertEqual(os.listdir(tmp), ["solving-plans"])

    def test_next_steps_appear_once(self):
        for path in sorted((ROOT / ".agents" / "workflows").glob("solve*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(workflow=path.name):
                if path.name == "solve.resume.md":
                    self.assertIn("--stdin --status", text)
                else:
                    self.assertNotIn("Next Steps:**", text)
        with tempfile.TemporaryDirectory() as tmp:
            for depth in self.advisor.VALID_DEPTHS:
                code, out, _ = self.cli(tmp, "revenue dropped", "--plan", "--depth", depth, "-f", "markdown")
                self.assertEqual(out.count("Next Steps"), 1, depth)

    def test_resume_status_and_done(self):
        request = "Công ty sắp hết tiền mặt trong 4 tháng, cần làm gì?"
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(tmp, "--stdin", "--plan", "--persist", "--step-docs", "-p", "Cash Crunch",
                                      "-f", "markdown", stdin=request)
            self.assertEqual(code, 0, err)
            self.assertIn("/solve.resume", out)
            plan_dir = Path(tmp) / "solving-plans" / "cash-crunch"
            state = json.loads((plan_dir / ".workspace.json").read_text(encoding="utf-8"))
            self.assertEqual(state["request"], request)
            self.assertEqual(state["category"], "Crisis / Turnaround")
            self.assertIn(request, (plan_dir / "01-PROBLEM-DEFINITION.md").read_text(encoding="utf-8"))
            self.assertIn("| Step | File | Done? |", (plan_dir / "00-OVERVIEW.md").read_text(encoding="utf-8"))

            code, out, _ = self.cli(tmp, "--status")
            self.assertEqual(code, 0)
            self.assertIn("### Next: 1. Define the Problem", out)
            self.assertIn("| 1. Define the Problem | `01-PROBLEM-DEFINITION.md` | not yet | ☐ |", out)
            self.assertIn("**Done when (quality gate):**", out)

            define = plan_dir / "01-PROBLEM-DEFINITION.md"
            define.write_text(define.read_text(encoding="utf-8") + "\nCash runway: 4 months\n", encoding="utf-8")
            code, out, _ = self.cli(tmp, "--done", "define", "-p", "cash crunch")
            self.assertEqual(code, 0)
            self.assertIn("Done: 1. Define the Problem", out)
            self.assertIn("| 1. Define the Problem | `01-PROBLEM-DEFINITION.md` | yes | ☑ |", out)
            self.assertIn("### Next: 2. Disaggregate the Problem", out)
            self.assertIn("--done 2 -p cash-crunch", out)

            # Saving again keeps the notes, the ticks and their "filled" state
            self.cli(tmp, "--stdin", "--plan", "--persist", "--step-docs", "-p", "Cash Crunch", stdin=request)
            code, out, _ = self.cli(tmp, "--status", "--json", "-p", "cash crunch")
            status = json.loads(out)
            self.assertTrue(status["rows"][0]["filled"] and status["rows"][0]["done"])

            # A second workspace; the request text picks the right one, else the latest
            self.cli(tmp, "Design a better onboarding flow", "--plan", "--persist", "--step-docs", "-p", "onboarding")
            code, out, _ = self.cli(tmp, "--stdin", "--status", stdin="tiếp tục vụ tiền mặt")
            self.assertIn("## Workspace: cash-crunch", out)
            self.assertIn("Other workspaces: `onboarding`", out)

            for step in ("2", "prioritize", "plan", "5", "synthesize"):
                self.cli(tmp, "--done", step, "-p", "cash-crunch")
            code, out, _ = self.cli(tmp, "--done", "communicate", "-p", "cash-crunch")
            self.assertIn("All steps are done", out)
            code, out, _ = self.cli(tmp, "--undone", "5", "-p", "cash-crunch")
            self.assertIn("### Next: 5. Conduct Analyses", out)

            code, _, err = self.cli(tmp, "--done", "9", "-p", "cash-crunch")
            self.assertEqual(code, 2)
            self.assertIn("unknown step", err)
            code, _, err = self.cli(tmp, "--status", "-p", "nope")
            self.assertEqual(code, 1)
            self.assertIn("cash-crunch", err)

    def test_workspaces_saved_before_tracking_still_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.cli(tmp, "revenue dropped", "--plan", "--persist", "--step-docs", "-p", "old")
            plan_dir = Path(tmp) / "solving-plans" / "old"
            (plan_dir / ".workspace.json").unlink()
            overview = plan_dir / "00-OVERVIEW.md"
            text = overview.read_text(encoding="utf-8")
            overview.write_text(text[:text.index("| Step |")], encoding="utf-8")
            code, out, _ = self.cli(tmp, "--status")
            self.assertEqual(code, 0)
            self.assertIn("| 1. Define the Problem | `01-PROBLEM-DEFINITION.md` | ? | ☐ |", out)
            self.assertIn("saved before progress tracking", out)
            code, out, _ = self.cli(tmp, "--done", "1")
            self.assertEqual(code, 0)
            self.assertIn("### Next: 2. Disaggregate the Problem", out)
            self.assertIn("## Progress", overview.read_text(encoding="utf-8"))


class MakeDecisionUpgradeTests(unittest.TestCase):
    """make-decision: classification regression set (English and Vietnamese), options, depths,
    scoring matrix, journal, workspace resume and the shared stemmer."""

    SCRIPT = SKILLS / "make-decision" / "scripts" / "search.py"

    # (request, decision type, criteria template); about half Vietnamese
    CASES = [
        ("React or Vue for our new project?", "Binary Choice", "Tech Stack / Framework Choice"),
        ("Postgres vs MongoDB for the orders service", "Binary Choice", "Tech Stack / Framework Choice"),
        ("AWS vs Azure vs GCP", "Multi-Option Selection", "Tech Stack / Framework Choice"),
        ("Build in-house vs Buy SaaS vs Hire agency for our new CRM system", "Multi-Option Selection",
         "Technology Selection"),
        ("Buy a house or keep renting", "Binary Choice", "Housing / Home"),
        ("We have to decide by Friday whether to renew the vendor contract or switch suppliers",
         "Time-Pressured Decision", "Vendor / Partner Selection"),
        ("Should we raise prices given uncertain demand?", "Decision Under Uncertainty", "Pricing"),
        ("Which CRM: Salesforce, HubSpot or Pipedrive", "Multi-Option Selection", "Technology Selection"),
        ("Accept the job offer at Google or stay at my current startup", "Binary Choice", "Job Offer / Career"),
        ("Which of three candidates should we hire for the senior backend role", "Multi-Option Selection",
         "Hiring Decision"),
        ("How should we split the Q3 budget across marketing, sales and R&D", "Resource Allocation",
         "Investment / Resource Allocation"),
        ("Should we expand into the Japanese market next year", "Strategic Direction", "Market Entry / Expansion"),
        ("Board must reach consensus on the new CEO", "Group / Stakeholder Decision", "Hiring Decision"),
        ("Should I do an MBA or keep working", "Binary Choice", "Education / Study"),
        ("Should I relocate to Berlin for better career opportunities", "Binary Choice",
         "Relocation / Where to Live"),
        ("Which features should go into the next sprint", "Operational / Tactical", "Product Feature Prioritization"),
        ("Launch now with unknown demand and incomplete data", "Decision Under Uncertainty", "General Decision"),
        ("Should we restructure the company into business units? The leadership team disagrees",
         "Group / Stakeholder Decision", "Organizational Change"),
        ("Where should we open our new office: Austin or Denver", "Binary Choice", "Location / Facility"),
        ("Should we migrate to microservices or keep the monolith", "Binary Choice", "Tech Stack / Framework Choice"),
        ("Pick a JavaScript framework: Svelte, React, Angular or Vue", "Multi-Option Selection",
         "Tech Stack / Framework Choice"),
        ("Should I accept the offer from Stripe? The deadline is tomorrow", "Time-Pressured Decision",
         "Job Offer / Career"),
        ("Allocate the engineering headcount between platform and growth teams", "Resource Allocation",
         "Investment / Resource Allocation"),
        ("Should we set our SaaS subscription price at $29 or $49", "Binary Choice", "Pricing"),
        ("nên chọn React hay Vue", "Binary Choice", "Tech Stack / Framework Choice"),
        ("nen chon react hay vue cho du an moi", "Binary Choice", "Tech Stack / Framework Choice"),
        ("Nên dùng AWS, Azure hay GCP cho hệ thống mới?", "Multi-Option Selection", "Tech Stack / Framework Choice"),
        ("So sánh Postgres với MongoDB cho dịch vụ đơn hàng", "Binary Choice", "Tech Stack / Framework Choice"),
        ("Nên dùng Flutter hay React Native cho app mobile", "Binary Choice", "Tech Stack / Framework Choice"),
        ("Mua nhà hay tiếp tục thuê nhà?", "Binary Choice", "Housing / Home"),
        ("Có nên nhận offer ở công ty mới với mức lương cao hơn không?", "Binary Choice", "Job Offer / Career"),
        ("Có nên nghỉ việc để đi du học thạc sĩ không?", "Binary Choice", "Education / Study"),
        ("Phải quyết định trước thứ Sáu: gia hạn hợp đồng với nhà cung cấp hay đổi sang bên khác",
         "Time-Pressured Decision", "Vendor / Partner Selection"),
        ("Có nên tăng giá sản phẩm khi nhu cầu thị trường chưa rõ ràng?", "Decision Under Uncertainty", "Pricing"),
        ("Chọn nhà cung cấp CRM nào: Salesforce, HubSpot hay Pipedrive", "Multi-Option Selection",
         "Technology Selection"),
        ("Tuyển ứng viên A hay ứng viên B cho vị trí trưởng nhóm", "Binary Choice", "Hiring Decision"),
        ("Phân bổ ngân sách marketing quý 3 giữa Facebook, Google và TikTok thế nào", "Resource Allocation",
         "Investment / Resource Allocation"),
        ("Có nên mở rộng sang thị trường Nhật Bản năm sau không", "Strategic Direction", "Market Entry / Expansion"),
        ("Hội đồng quản trị cần thống nhất chọn CEO mới", "Group / Stakeholder Decision", "Hiring Decision"),
        ("Nên học thạc sĩ hay đi làm luôn", "Binary Choice", "Education / Study"),
        ("Có nên chuyển vào Sài Gòn sống và làm việc không", "Binary Choice", "Relocation / Where to Live"),
        ("Ưu tiên tính năng nào cho sprint tới", "Operational / Tactical", "Product Feature Prioritization"),
        ("Ra mắt sản phẩm khi chưa có dữ liệu về nhu cầu, rủi ro cao", "Decision Under Uncertainty",
         "General Decision"),
        ("Ban lãnh đạo không đồng ý về việc tái cấu trúc công ty", "Group / Stakeholder Decision",
         "Organizational Change"),
        ("Chọn văn phòng mới ở quận 1 hay quận 7", "Binary Choice", "Location / Facility"),
        ("Gấp: cần quyết định ngay hôm nay có ký hợp đồng thuê ngoài hay không", "Time-Pressured Decision",
         "Vendor / Partner Selection"),
        ("Nên đặt giá gói SaaS 29 đô hay 49 đô", "Binary Choice", "Pricing"),
        ("Mình nên chuyển sang Đà Nẵng sống hay ở lại Hà Nội", "Binary Choice", "Relocation / Where to Live"),
        ("Nên đầu tư vàng hay gửi tiết kiệm ngân hàng", "Binary Choice", "Investment / Resource Allocation"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.core, cls.advisor = load_skill("make-decision")
        cls.journal = cls.advisor.journal
        cls.workspace = cls.advisor.workspace

    def plan(self, query, depth="standard", **kwargs):
        return self.advisor.DecisionAdvisor(query, **kwargs).generate(depth=depth)

    def cli(self, args, cwd, stdin=None):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(self.SCRIPT)] + args, cwd=cwd, env=env, capture_output=True,
                           input=(stdin or "").encode("utf-8"))
        return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")

    # ---- classification ----
    def test_regression_set_types_and_criteria(self):
        vietnamese = sum(1 for q, _, _ in self.CASES if self.core.has_accents(q) or q.startswith("nen "))
        self.assertGreaterEqual(len(self.CASES), 30)
        self.assertGreaterEqual(vietnamese * 2, len(self.CASES) - 1)
        for query, dtype, template in self.CASES:
            with self.subTest(query=query):
                plan = self.plan(query)
                self.assertEqual(plan["decision_type"]["name"], dtype)
                self.assertEqual(plan["criteria"]["domain"], template)

    def test_unicode_form_does_not_change_the_result(self):
        import unicodedata
        for query in ("nên chọn React hay Vue", "Mua nhà hay tiếp tục thuê nhà?"):
            nfd = unicodedata.normalize("NFD", query)
            with self.subTest(query=query):
                a, b = self.plan(query), self.plan(nfd)
                self.assertEqual(a["decision_type"]["name"], b["decision_type"]["name"])
                self.assertEqual(a["criteria"]["domain"], b["criteria"]["domain"])
                self.assertEqual(self.core.slugify(query), self.core.slugify(nfd))
                self.assertTrue(self.core.slugify(nfd).isascii())

    def test_accented_text_is_matched_exactly(self):
        # "chi nhánh" (branch) must not count as "nhanh" (fast) - a Time-Pressured signal
        plan = self.plan("Có nên mở thêm chi nhánh ở Đà Nẵng không")
        self.assertNotEqual(plan["decision_type"]["name"], "Time-Pressured Decision")
        self.assertEqual(plan["criteria"]["domain"], "Location / Facility")

    def test_unmatched_request_says_so(self):
        plan = self.plan("zzz qqq")
        self.assertEqual(plan["decision_type"]["source"], "default")
        self.assertEqual(plan["criteria"]["domain"], "General Decision")
        text = self.advisor.DecisionAdvisor("zzz qqq").format_markdown(plan)
        self.assertIn("No decision type matched clearly. Re-run with `--type`", text)
        for name in self.advisor.DecisionAdvisor.decision_type_names():
            self.assertIn(name, text)
        self.assertNotIn("No decision type matched", self.advisor.DecisionAdvisor("x").format_markdown(
            self.plan("React or Vue?")))

    def test_knowledge_base_references_resolve(self):
        for row in self.core.load_csv("types"):
            for col, domain in (("Recommended Frameworks", "frameworks"), ("Analysis Methods", "analysis"),
                                ("Key Biases", "biases"), ("Facilitation", "facilitation")):
                for name in self.advisor.split_names(row[col]):
                    with self.subTest(type=row["Decision Type"], col=col, name=name):
                        self.assertTrue(self.core.find_row(domain, name))
            self.assertNotIn("Expected Value Calculation", row["Analysis Methods"])
        for row in self.core.load_csv("criteria"):
            with self.subTest(template=row["Domain"]):
                names = self.advisor.split_names(row["Criteria"])
                weights = [int(w) for w in self.advisor.split_names(row["Default Weights"])]
                self.assertEqual(len(names), 5)  # SKILL.md: never more than 5 criteria
                self.assertEqual(sum(weights), 100)
                for bias in self.advisor.split_names(row["Key Biases"]):
                    self.assertTrue(self.core.find_row("biases", bias), bias)
                self.assertTrue(all(i["guide"] for i in self.advisor.criteria_items(row)))

    def test_every_plan_has_criteria_biases_and_analysis(self):
        for query, _, _ in self.CASES + [("zzz qqq", "", "")]:
            with self.subTest(query=query):
                plan = self.plan(query)
                self.assertEqual(len(plan["criteria"]["items"]), 5)
                self.assertEqual(sum(i["weight"] for i in plan["criteria"]["items"]), 100)
                self.assertGreaterEqual(len(plan["bias_warnings"]), 3)
                self.assertGreaterEqual(len(plan["analysis_techniques"]), 2)
                frameworks = {r["Framework"] for r in self.core.load_csv("frameworks")}
                for a in plan["analysis_techniques"]:
                    self.assertNotIn(a["technique"], frameworks)

    # ---- options ----
    def test_options_are_parsed(self):
        cases = [
            ("Which CRM: Salesforce, HubSpot or Pipedrive", ["Salesforce", "HubSpot", "Pipedrive"]),
            ("Should we use Postgres or MySQL", ["Postgres", "MySQL"]),
            ("React or Vue for our new project?", ["React", "Vue"]),
            ("Build in-house vs Buy SaaS vs Hire agency", ["Build in-house", "Buy SaaS", "Hire agency"]),
            ("nên chọn React hay Vue", ["React", "Vue"]),
            ("nen chon react hay vue", ["react", "vue"]),
            ("Dùng Go hoặc Rust cho dịch vụ mới", ["Dùng Go", "Rust"]),
            ("Chọn giữa Shopee, Lazada và Tiki để mở gian hàng", ["Shopee", "Lazada", "Tiki"]),
            ("So sánh Postgres với MongoDB", ["Postgres", "MongoDB"]),
            ("Postgres so với MongoDB", ["Postgres", "MongoDB"]),
            ("Allocate headcount between platform and growth", ["platform", "growth"]),
            ("Should we set the price at $29 or $49", ["$29", "$49"]),
            ("Should we renew the contract or not", ["renew the contract", "Not (keep things as they are)"]),
            ("How should we split the budget across marketing, sales and R&D", []),
            ("We need to decide fast, the offer expires Friday", []),
            ("Should we raise prices given uncertain demand?", []),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.advisor.parse_options(text), expected)

    def test_plan_and_saved_files_name_the_options_and_request(self):
        import json
        query = "nên chọn React hay Vue cho dự án mới"
        plan = self.plan(query)
        text = self.advisor.DecisionAdvisor(query).format_markdown(plan)
        self.assertIn("**Options:** React | Vue", text)
        self.assertIn(f"**Request:** {query}", text)
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--stdin", "--plan", "--persist", "--step-docs", "-p", "Frontend"], tmp, query)
            self.assertEqual(code, 0, err)
            folder = Path(tmp) / "decision-plans" / "frontend"
            options = (folder / "05-OPTIONS.md").read_text(encoding="utf-8")
            self.assertIn("| React |", options)
            self.assertIn("| Criterion | Weight | React | Vue |", options)
            self.assertNotIn("Option A", options)
            criteria = (folder / "03-CRITERIA.md").read_text(encoding="utf-8")
            self.assertIn("| Team expertise and learning curve | 25 |", criteria)
            self.assertIn(query, (folder / "01-DECISION-TYPE.md").read_text(encoding="utf-8"))
            decision = (folder / "06-DECISION.md").read_text(encoding="utf-8")
            self.assertIn("## Pre-Mortem", decision)
            self.assertIn("## Kill Criteria", decision)
            state = json.loads((folder / ".workspace.json").read_text(encoding="utf-8"))
            self.assertEqual(state["request"], query)
            self.assertEqual(state["options"], ["React", "Vue"])
            code, out, err = self.cli(["--stdin", "--plan", "--persist", "-p", "Single"], tmp, query)
            self.assertIn(query, (Path(tmp) / "decision-plans/single/PLAN.md").read_text(encoding="utf-8"))

    # ---- depth ----
    def test_depths_are_materially_different(self):
        query = "Should we migrate to microservices or keep the monolith"
        texts = {d: self.advisor.DecisionAdvisor(query).format_markdown(self.plan(query, d))
                 for d in self.advisor.VALID_DEPTHS}

        def headings(text):
            return [line[3:] for line in text.splitlines() if line.startswith("## ")]

        self.assertEqual(len({tuple(headings(t)) for t in texts.values()}), 4)
        self.assertLess(len(texts["quick"]), len(texts["standard"]))
        self.assertLess(len(texts["standard"]), len(texts["deep"]))
        self.assertNotIn("Bias Warnings", headings(texts["quick"]))
        self.assertNotIn("Decision Checklist", headings(texts["quick"]))
        for section in ("Pre-Mortem", "Sensitivity", "Reversibility", "Information to Gather"):
            self.assertIn(section, headings(texts["deep"]))
            self.assertNotIn(section, headings(texts["standard"]))
        execu = headings(texts["executive"])
        self.assertEqual(execu[0], "Recommendation")
        for section in ("Decision Needed", "Key Risks", "Reversibility", "What Would Change the Call"):
            self.assertIn(section, execu)
        self.assertLess(execu.index("Key Risks"), execu.index("Criteria and Weights"))
        self.assertIn("Executive Decision Brief", texts["executive"])
        self.assertEqual(len(self.plan(query, "quick")["criteria"]["items"]), 3)

    # ---- matrix ----
    def test_matrix_criteria_and_alignment(self):
        m = self.advisor.build_matrix("React vs Vue", "Cost,,Speed")
        self.assertEqual([c["name"] for c in m["criteria"]], ["Cost", "Speed"])
        text = self.advisor.format_matrix(self.advisor.build_matrix(
            "Which CRM: Salesforce, HubSpot or Pipedrive", "Total cost:3,Fit:2", "Salesforce:2,5;HubSpot:4,4;"
            "Pipedrive:5,2"))
        table = [ln for ln in text.split("Winner")[0].splitlines() if " | " in ln]
        self.assertEqual(len(table), 4)
        self.assertEqual(len({tuple(i for i, ch in enumerate(ln) if ch == "|") for ln in table}), 1)
        self.assertEqual([ln.split(" | ")[0].strip() for ln in table[1:] if not ln.startswith("-")],
                         ["Salesforce", "HubSpot", "Pipedrive"])
        md = self.advisor.format_matrix(m, "markdown")
        self.assertIn("| Option | Cost (w 1, 50%) | Speed (w 1, 50%) | Weighted |", md)

    def test_weighted_scores_winner_and_sensitivity(self):
        m = self.advisor.build_matrix("React vs Vue", "Cost:3,Speed:2,Risk:1", "React:4,3,5;Vue:5,4,3")
        totals = {o["name"]: round(o["total"], 2) for o in m["options"]}
        self.assertEqual(totals, {"React": 3.83, "Vue": 4.33})
        self.assertEqual(m["winner"], "Vue")
        first = m["sensitivity"][0]
        self.assertEqual((first["criterion"], first["new_winner"]), ("Risk", "React"))
        self.assertAlmostEqual(first["new_weight"], 2.5)
        # At the reported weight the two options tie
        weights = [3, 2, first["new_weight"]]
        self.assertAlmostEqual(self.advisor.weighted_total([4, 3, 5], weights),
                               self.advisor.weighted_total([5, 4, 3], weights))
        cost = next(s for s in m["sensitivity"] if s["criterion"] == "Cost")
        self.assertIsNone(cost["change"])  # dropping Cost to 0 only ties
        text = self.advisor.format_matrix(m, "markdown")
        self.assertIn("**Winner:** Vue", text)
        self.assertIn("weight of Risk rises from 1 to 2.5", text)

        dominant = self.advisor.build_matrix("A vs B", "X:1,Y:1", "A:5,5;B:1,1")
        self.assertTrue(all(s["change"] is None for s in dominant["sensitivity"]))
        tie = self.advisor.build_matrix("A vs B", "X:1,Y:1", "A:5,1;B:1,5")
        self.assertEqual(tie["tie"], ["A", "B"])
        for criteria, scores in (("X:1,Y:1", "A:5;B:1,1"), ("X:1,Y:1", "C:1,1;B:1,1"), ("X:1,Y", "A:1,1"),
                                 ("X:1,X:2", None), ("X:-1,Y:1", None)):
            with self.subTest(criteria=criteria, scores=scores), self.assertRaises(ValueError):
                self.advisor.build_matrix("A vs B", criteria, scores)

    def test_matrix_cli_reads_stdin_and_reports_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--stdin", "--matrix", "-f", "markdown", "-c", "Cost:3,Speed:2,Risk:1",
                                       "--scores", "React:4,3,5;Vue:5,4,3"], tmp, 'nên chọn "React" hay `Vue`?')
            self.assertEqual(code, 0, err)
            self.assertIn("**Winner:** Vue", out)
            code, out, err = self.cli(["--matrix", "A vs B", "-c", "X:1,Y:1", "--scores", "A:1"], tmp)
            self.assertEqual(code, 2)
            self.assertIn("1 scores but there are 2 criteria", err)
            self.assertEqual(out, "")

    # ---- journal ----
    def test_journal_create_update_and_review(self):
        from datetime import date
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--stdin", "--journal", "--confidence", "70", "--review-in", "2w"], tmp,
                                      "Chọn React hay Vue cho dự án mới")
            self.assertEqual(code, 0, err)
            files = list((Path(tmp) / ".decisions").glob("*.md"))
            self.assertEqual(len(files), 1)
            entry = files[0]
            self.assertTrue(entry.name.isascii())
            self.assertIn("chon-react-hay-vue", entry.name)
            text = entry.read_text(encoding="utf-8")
            self.assertIn("- **Confidence:** 70%", text)
            self.assertIn("1. React\n2. Vue", text)
            self.assertIn("- **Framework:** Pros-Cons-Fixes Analysis", text)
            self.assertRegex(text, r"\*\*Review by:\*\* \d{4}-\d{2}-\d{2}")
            entry.write_text(text + "\n## My notes\nkeep me\n", encoding="utf-8")

            outcome = "saved to C:\\Users\\me\n## not a heading\n\\1 \\g<0>"
            code, out, err = self.cli(["--journal", "--update", "chon-react", "--outcome", outcome], tmp)
            self.assertEqual(code, 0, err)
            text = entry.read_text(encoding="utf-8")
            self.assertIn("saved to C:\\Users\\me", text)
            self.assertIn("\\1 \\g<0>", text)
            self.assertNotIn("\n## not a heading", text)
            self.assertIn("## My notes\nkeep me", text)
            self.assertEqual(text.count("## Reflection"), 1)
            self.assertIn("**Status:** Reviewed", text)
            code, out, err = self.cli(["--journal", "--update", "chon-react", "--stdin"], tmp, "second outcome")
            self.assertEqual(code, 0, err)
            text = entry.read_text(encoding="utf-8")
            self.assertIn("saved to C:\\Users\\me", text)  # earlier outcome kept
            self.assertIn("second outcome", text)

            self.cli(["--journal", "React again"], tmp)
            code, out, err = self.cli(["--journal", "--update", "react", "--outcome", "x"], tmp)
            self.assertEqual(code, 2)
            self.assertIn("2 journal entries match", err)
            self.assertEqual(out, "")
            code, out, err = self.cli(["--journal", "--update", "zzz", "--outcome", "x"], tmp)
            self.assertEqual(code, 2)
            self.assertIn("no journal entry matches", err)

            other = Path(tmp) / "elsewhere"
            code, out, err = self.cli(["--journal", "Pick a CRM", "-o", str(other)], tmp)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(list((other / ".decisions").glob("*.md"))), 1)
            code, out, err = self.cli(["--journal", "--review", "-o", str(other)], tmp)
            self.assertIn("Pick a CRM", out)
            self.assertNotIn("React again", out)

        with tempfile.TemporaryDirectory() as tmp:
            j = self.journal
            j.create_journal("old decision", output_dir=tmp, today=date(2026, 1, 5), review_days=30)
            j.create_journal("zebra newest", output_dir=tmp, today=date(2026, 3, 1), review_days=7)
            j.create_journal("aardvark middle", output_dir=tmp, today=date(2026, 2, 1), review_days=365)
            listing = j.review_journals(tmp, today=date(2026, 3, 20))
            order = [ln.split(" | ")[1] for ln in listing.splitlines() if ln.startswith("[")]
            self.assertEqual(order, ["zebra newest", "aardvark middle", "old decision"])
            due = j.review_journals(tmp, due=True, today=date(2026, 3, 20))
            self.assertIn("old decision", due)
            self.assertIn("zebra newest", due)
            self.assertIn("overdue", due)
            self.assertNotIn("aardvark middle", due)
            self.assertEqual(j.parse_duration("2w"), 14)
            with self.assertRaises(ValueError):
                j.parse_duration("3q")

    # ---- workspace resume ----
    def test_status_done_and_undone(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--stdin", "--plan", "--persist", "--step-docs", "-p", "Cloud"], tmp,
                                      "AWS vs Azure vs GCP")
            self.assertEqual(code, 0, err)
            self.assertIn("--status -p cloud", out)
            overview = (Path(tmp) / "decision-plans/cloud/00-OVERVIEW.md").read_text(encoding="utf-8")
            self.assertIn("| Step | File | Done? |", overview)
            code, out, err = self.cli(["--stdin", "--status"], tmp, "azure")
            self.assertEqual(code, 0, err)
            self.assertIn("### Next: 1. Classify the decision", out)
            self.assertIn("AWS vs Azure vs GCP", out)
            code, out, err = self.cli(["--done", "1", "-p", "cloud"], tmp)
            code, out, err = self.cli(["--done", "criteria", "-p", "cloud"], tmp)
            self.assertEqual(code, 0, err)
            self.assertIn("### Next: 2. Apply the framework", out)
            status = self.workspace.workspace_status(Path(tmp) / "decision-plans/cloud")
            self.assertEqual([r["done"] for r in status["rows"]], [True, False, True, False, False, False])
            code, out, err = self.cli(["--undone", "1", "-p", "cloud"], tmp)
            self.assertIn("### Next: 1. Classify the decision", out)
            code, out, err = self.cli(["--done", "9", "-p", "cloud"], tmp)
            self.assertEqual(code, 2)
            self.assertIn("unknown step", err)
            code, out, err = self.cli(["--status", "-p", "nope"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("No workspace named", err)
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--status"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("No saved workspace", err)

    # ---- CLI odds and ends ----
    def test_json_plan_blank_plan_and_next_steps_once(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.cli(["--stdin", "--plan", "--json"], tmp, "nên chọn React hay Vue")
            self.assertEqual(code, 0, err)
            data = json.loads(out)
            self.assertEqual(data["options"], ["React", "Vue"])
            self.assertEqual(data["request"], "nên chọn React hay Vue")
            self.assertEqual(data["criteria"]["domain"], "Tech Stack / Framework Choice")
            code, out, err = self.cli(["--stdin", "--plan", "--json", "--persist", "-p", "j"], tmp, "React or Vue")
            self.assertTrue(json.loads(out)["saved"]["written"])
            code, out, err = self.cli(["   ", "--plan"], tmp)
            self.assertEqual(code, 2)
            self.assertIn("describe the decision", err)
            for depth in self.advisor.VALID_DEPTHS:
                code, out, err = self.cli(["--stdin", "--plan", "-f", "markdown", "--depth", depth], tmp, "A or B")
                self.assertEqual(out.count("Next Steps"), 1, depth)
        for path in sorted((ROOT / ".agents" / "workflows").glob("decide*.md")):
            with self.subTest(workflow=path.name):
                self.assertNotIn("🎯 **Next Steps:**", path.read_text(encoding="utf-8"))
        self.assertTrue((ROOT / ".agents" / "workflows" / "decide.resume.md").exists())

    def test_prompt_mirrors_skill(self):
        folder = SKILLS / "make-decision"
        skill = (folder / "SKILL.md").read_text(encoding="utf-8")
        body = skill[skill.index("\n---\n", 4) + 5:].lstrip("\n")
        self.assertEqual((folder / "PROMPT.md").read_text(encoding="utf-8"), body)

    # ---- shared stemmer ----
    def test_stemmer_joins_inflected_forms_in_every_skill(self):
        groups = [("hire", "hiring", "hired", "hires"), ("uncertain", "uncertainty"), ("secure", "security"),
                  ("decline", "declining", "declined"), ("agree", "agreed"), ("employee", "employees"),
                  ("case", "cases"), ("rent", "renting")]
        cores = {name: load_skill(name)[0] for name in ("problem-solving-pro", "make-decision", "code-solving")}
        for name, core in cores.items():
            for words in groups:
                with self.subTest(skill=name, words=words):
                    self.assertEqual(len({core.stem(w) for w in words}), 1, [core.stem(w) for w in words])
            self.assertEqual(core.stem("city"), cores["make-decision"].stem("city"))
            self.assertNotEqual(core.stem("party"), core.stem("par"))


class ClassificationRegressionTests(unittest.TestCase):
    """Requests an audit found misclassified: keywords must match as whole phrases, each once,
    with or without Vietnamese accents."""

    @classmethod
    def setUpClass(cls):
        cls.cs, _ = load_skill("code-solving")
        cls.ps, _ = load_skill("problem-solving-pro")
        cls.md_core, cls.md = load_skill("make-decision")

    def test_code_task_types(self):
        traceback = ("Traceback (most recent call last):\n"
                     "  File \"app/main.py\", line 12, in <module>\n    run()\n"
                     "  File \"app/services/users.py\", line 40, in run\n    return user.name\n"
                     "AttributeError: 'NoneType' object has no attribute 'name'")
        cases = [
            ("Add a logout button", "feature"),
            ("Add pagination to the orders list", "feature"),
            ("Add rate limiting to the public API", "feature"),
            ("chuyen tu MySQL sang PostgreSQL", "migration"),
            (traceback, "debug"),
            ("Traceback (most recent call last):\n  File \"app/views.py\", line 88, in get_profile\n"
             "    uid = request.session['user_id']\nKeyError: 'user_id'", "debug"),
            ("The /search endpoint takes 4 seconds at p95, need it under 300ms", "performance"),
            ("How is the JWT validated in this service?", "explain"),
            ("Production API is returning 502s for all users since the 14:00 deploy", "incident"),
            # Vietnamese typed without accents
            ("sua loi dang nhap", "debug"),
            ("toi uu truy van", "performance"),
            ("nang cap React 17 len 18", "migration"),
            ("lo hong bao mat", "security"),
            ("doi mau nut", "quick-fix"),
            ("loi dang nhap khong hoat dong sau khi doi mat khau", "debug"),
            # one-syllable Vietnamese keywords without accents need Vietnamese around them
            ("Migrate our SAP ERP to Odoo", "migration"),
        ]
        for query, expected in cases:
            with self.subTest(query=query[:60]):
                row, source = self.cs.classify_task(query)
                self.assertEqual((row["Type"], source), (expected, "auto"))

    def test_code_keywords_count_once_and_whole(self):
        scores = self.cs.task_scores("test test test test the login bug")
        self.assertEqual(scores["test"][0], 0)  # 'test' alone is not a keyword, however often it appears
        self.assertNotIn("one line", self.cs.task_scores("error on line 5")["quick-fix"][1])
        self.assertNotIn("on-call", self.cs.task_scores("Traceback (most recent call last):")["incident"][1])

    def test_problem_keywords_keep_short_and_stop_words(self):
        cases = [
            ("Too many meetings are killing our productivity", "Diagnostic", "Organizational Change"),
            ("Our US market share is falling", "Diagnostic", "Business Performance"),
            ("Kinh tế khó khăn, cửa hàng vắng khách", "Diagnostic", "Business Performance"),
            ("Our checkout conversion is 1.2% while the industry benchmark is 3%", "Diagnostic",
             "Business Performance"),
        ]
        for query, ptype, category in cases:
            with self.subTest(query=query):
                self.assertEqual(self.ps.classify_problem_type(query).get("Problem Type"), ptype)
                self.assertEqual(self.ps.classify_category(query), category)
        self.assertNotEqual(self.ps.classify_problem_type("Too many meetings").get("Problem Type"), "Prediction")
        self.assertNotEqual(self.ps.classify_category("Kinh tế khó khăn"), "Policy / Public Sector")

    def test_decision_options_and_types(self):
        parse = self.md.parse_options
        self.assertEqual(parse("Which CRM: Salesforce, HubSpot and Pipedrive"), ["Salesforce", "HubSpot", "Pipedrive"])
        self.assertEqual(parse("Chọn giữa ba nhà cung cấp phần mềm kế toán: MISA, Fast và Bravo"),
                         ["MISA", "Fast", "Bravo"])
        self.assertEqual(parse("Which cloud should we use?\n1. AWS\n2. GCP\n3. Azure"), ["AWS", "GCP", "Azure"])
        self.assertEqual(parse("Pick one:\n- MacBook Pro\n- ThinkPad X1\n* Dell XPS"),
                         ["MacBook Pro", "ThinkPad X1", "Dell XPS"])
        self.assertEqual(parse("Context:\n- revenue down 20% in Q3\n- churn up\nShould we cut prices or invest "
                               "in marketing?"), ["cut prices", "invest in marketing"])
        self.assertEqual(parse("We need marketing, sales and R&D to align"), [])
        cases = [
            ("Chọn giữa ba nhà cung cấp phần mềm kế toán: MISA, Fast và Bravo", "Multi-Option Selection"),
            ("We're not sure the market will recover; should we hire 10 more salespeople?",
             "Decision Under Uncertainty"),
            ("Should we move our daily standup from 9am to 10am?", "Operational / Tactical"),
            ("Should we change our on-call rotation from weekly to bi-weekly?", "Operational / Tactical"),
            ("Should we use Postgres or MySQL now", "Binary Choice"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(self.md.DecisionAdvisor(query).classify()["row"]["Decision Type"], expected)
        m = self.md.build_matrix("1. AWS\n2. GCP\n3. Azure", "Cost,Speed")
        self.assertEqual([o["name"] for o in m["options"]], ["AWS", "GCP", "Azure"])

    def test_matrix_scores_must_be_on_the_1_to_5_scale(self):
        for scores in ("A:9,3;B:4,4", "A:0,3;B:4,4", "A:-1,3;B:4,4"):
            with self.subTest(scores=scores), self.assertRaises(ValueError) as e:
                self.md.build_matrix("A vs B", "X,Y", scores)
            self.assertIn("from 1 to 5", str(e.exception))
        self.assertEqual(self.md.build_matrix("A vs B", "X,Y", "A:1,5;B:2.5,3")["winner"], "A")

    def test_search_domains_match_whole_words(self):
        self.assertNotEqual(self.cs.detect_domain("catalog page is slow"), "debugging")
        self.assertGreater(self.cs.search("catalog page is slow")["count"], 0)
        self.assertEqual(self.cs.search("TypeError: Cannot read properties of undefined")["domain"], "errors")
        self.assertEqual(self.cs.detect_domain("read the logs"), "debugging")
        self.assertNotEqual(self.ps.detect_domain("our latest prototype got bad reviews"), "problem-types")
        self.assertEqual(self.ps.detect_domain("what type of problem is this"), "problem-types")
        self.assertEqual(self.md_core.auto_detect_domains("steam bias"), ["biases"])
        self.assertIn("facilitation", self.md_core.auto_detect_domains("our team workshop"))


class WorkspaceReuseTests(unittest.TestCase):
    """A saved workspace holds one plan: saving another request or type into it is refused
    unless --force, and names typed with or without accents (NFC or NFD) find the same folder."""

    SKILLS_AND_DIRS = (("problem-solving-pro", "solving-plans"), ("make-decision", "decision-plans"),
                       ("code-solving", "coding-plans"))

    def run_cli(self, skill, cwd, args, stdin):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        extra = ["--no-context"] if skill == "code-solving" else []
        r = subprocess.run([sys.executable, str(SKILLS / skill / "scripts/search.py"), "--stdin"] + args + extra,
                           input=stdin.encode("utf-8"), cwd=cwd, env=env, capture_output=True)
        return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")

    def test_saving_another_plan_into_a_workspace_is_refused(self):
        save = ["--plan", "--persist", "--step-docs", "-p", "X", "-f", "markdown"]
        for skill, folder in self.SKILLS_AND_DIRS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                code, _, err = self.run_cli(skill, tmp, save, "Doanh thu quý 3 giảm 18%")
                self.assertEqual(code, 0, err)
                plan_dir = Path(tmp) / folder / "x"
                overview = (plan_dir / "00-OVERVIEW.md").read_text(encoding="utf-8")
                state = (plan_dir / ".workspace.json").read_text(encoding="utf-8")
                victim = sorted(plan_dir.glob("0[2-5]-*.md"))[0]
                victim.unlink()
                code, out, err = self.run_cli(skill, tmp, save, "Design a new onboarding flow")
                self.assertEqual(code, 2)
                self.assertIn("already holds another plan", err)
                self.assertIn("--force", err)
                self.assertEqual(out, "")
                self.assertFalse(victim.exists())
                self.assertEqual((plan_dir / "00-OVERVIEW.md").read_text(encoding="utf-8"), overview)
                self.assertEqual((plan_dir / ".workspace.json").read_text(encoding="utf-8"), state)
                # The same request again is fine and keeps the notes
                code, _, err = self.run_cli(skill, tmp, save, "Doanh thu quý 3 giảm 18%")
                self.assertEqual(code, 0, err)
                # --force replaces the plan; overview, state and status agree
                code, _, err = self.run_cli(skill, tmp, save + ["--force"], "Design a new onboarding flow")
                self.assertEqual(code, 0, err)
                self.assertIn("Design a new onboarding flow", (plan_dir / "00-OVERVIEW.md").read_text(encoding="utf-8"))
                code, out, err = self.run_cli(skill, tmp, ["--status", "--json", "-p", "x"], "")
                self.assertEqual(code, 0, err)
                self.assertEqual(json.loads(out)["request"], "Design a new onboarding flow")

    def test_changing_the_code_task_type_leaves_no_stray_hand_off(self):
        save = ["--plan", "--persist", "--step-docs", "-p", "w"]
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_cli("code-solving", tmp, save, "fix typo in footer")[0], 0)
            plan_dir = Path(tmp) / "coding-plans" / "w"
            self.assertTrue((plan_dir / "06-COMMIT.md").exists())
            code, _, err = self.run_cli("code-solving", tmp, save + ["--type", "debug"], "fix typo in footer")
            self.assertEqual(code, 2)
            self.assertIn("quick-fix", err)
            code, _, err = self.run_cli("code-solving", tmp, save + ["--type", "debug", "--force"], "fix typo in footer")
            self.assertEqual(code, 0, err)
            self.assertEqual(sorted(p.name for p in plan_dir.glob("06-*")), ["06-PR.md"])
            state = json.loads((plan_dir / ".workspace.json").read_text(encoding="utf-8"))
            self.assertEqual(state["type"], "debug")
            self.assertNotIn("06-COMMIT.md", state["files"])

    def test_workspace_names_fold_accents(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "Giảm doanh thu")
        for skill, folder in self.SKILLS_AND_DIRS:
            core = load_skill(skill)[0]
            with self.subTest(skill=skill):
                self.assertEqual(core.slugify(nfd), "giam-doanh-thu")
                self.assertEqual(core.slugify("Giảm doanh thu"), "giam-doanh-thu")
                self.assertEqual(core.slugify("Đổi mới"), "doi-moi")
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                code, _, err = self.run_cli(skill, tmp, ["--plan", "--persist", "--step-docs", "-p", nfd], nfd)
                self.assertEqual(code, 0, err)
                self.assertEqual([p.name for p in (Path(tmp) / folder).iterdir()], ["giam-doanh-thu"])
                for name in ("giam doanh thu", "Giảm doanh thu", nfd):
                    code, out, err = self.run_cli(skill, tmp, ["--status", "-p", name], "")
                    self.assertEqual(code, 0, err)
                    self.assertIn("giam-doanh-thu", out)
                # A folder saved before folding (accents in its name) is still found
                old = Path(tmp) / folder / "giảm-chi-phí"
                shutil.copytree(Path(tmp) / folder / "giam-doanh-thu", old)
                code, out, err = self.run_cli(skill, tmp, ["--status", "-p", "giam chi phi"], "")
                self.assertEqual(code, 0, err)
                self.assertIn("giảm-chi-phí", out)

    def test_next_steps_stop_offering_to_save_once_saved(self):
        for skill, _ in self.SKILLS_AND_DIRS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                code, out, err = self.run_cli(skill, tmp, ["--plan", "-f", "markdown"], "login is broken")
                self.assertIn("save step-by-step", out)
                code, out, err = self.run_cli(skill, tmp, ["--plan", "--persist", "--step-docs", "-p", "a",
                                                           "-f", "markdown"], "login is broken")
                self.assertEqual(code, 0, err)
                self.assertNotIn("save step-by-step", out)


class ConsistentCliTests(unittest.TestCase):
    """The three search.py scripts take the same flag spellings and use the same exit codes."""

    SKILLS_AND_DIRS = WorkspaceReuseTests.SKILLS_AND_DIRS

    def test_flag_spellings_are_shared(self):
        for skill, folder in self.SKILLS_AND_DIRS:
            script = SKILLS / skill / "scripts/search.py"
            with tempfile.TemporaryDirectory() as tmp:
                for flag in ("-p", "--project", "--project-name"):
                    with self.subTest(skill=skill, flag=flag):
                        name = "n" + flag.strip("-").replace("-", "")
                        r = run_script(script, ["login is broken", "--plan", "--persist", flag, name], tmp)
                        self.assertEqual(r.returncode, 0, r.stderr)
                        self.assertTrue((Path(tmp) / folder / name / "PLAN.md").exists())
                for flag in ("-n", "--results", "--max-results"):
                    with self.subTest(skill=skill, flag=flag):
                        r = run_script(script, ["bias", flag, "1", "--json"], tmp)
                        self.assertEqual(r.returncode, 0, r.stderr)
                        self.assertLessEqual(json.loads(r.stdout)["count"], 1)

    def test_empty_input_is_a_one_line_error(self):
        for skill, _ in self.SKILLS_AND_DIRS:
            script = SKILLS / skill / "scripts/search.py"
            for args in ([], ["--plan"], ["   ", "--plan", "--json"]):
                with self.subTest(skill=skill, args=args), tempfile.TemporaryDirectory() as tmp:
                    r = run_script(script, args, tmp)
                    self.assertEqual(r.returncode, 2)
                    self.assertEqual(r.stdout, "")
                    self.assertEqual(len(r.stderr.strip().splitlines()), 1, r.stderr)
                    self.assertTrue(r.stderr.startswith("Error: "))
                    self.assertEqual(os.listdir(tmp), [])

    def test_bad_values_exit_2_and_missing_workspace_exits_1(self):
        for skill, _ in self.SKILLS_AND_DIRS:
            script = SKILLS / skill / "scripts/search.py"
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(run_script(script, ["x", "--plan", "--type", "Nope"], tmp).returncode, 2)
                self.assertEqual(run_script(script, ["--status"], tmp).returncode, 1)
                run_script(script, ["login is broken", "--plan", "--persist", "--step-docs", "-p", "a"], tmp)
                self.assertEqual(run_script(script, ["--done", "9", "-p", "a"], tmp).returncode, 2)

    def test_empty_code_review_reviews_the_current_changes(self):
        script = SKILLS / "code-solving/scripts/search.py"
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, str(script), "--stdin", "--plan", "--type", "review", "--json"],
                               input=b"\n", cwd=tmp, env=env, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            plan = json.loads(r.stdout)
            self.assertEqual(plan["query"], "Review the current changes")
            self.assertEqual(plan["task"]["type"], "review")
            r = run_script(script, ["--plan", "--type", "debug"], tmp)
            self.assertEqual(r.returncode, 2)


class CodeContextRegressionTests(unittest.TestCase):
    """Stack frames with spaces in Windows paths, symbols that are not the project's, folders without git."""

    @classmethod
    def setUpClass(cls):
        sys.modules.pop("context", None)
        path = str(SKILLS / "code-solving" / "scripts")
        sys.path.insert(0, path)
        try:
            cls.context = importlib.import_module("context")
        finally:
            sys.path.remove(path)
            sys.modules.pop("context", None)

    def test_csharp_frame_with_spaces_in_the_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src/App").mkdir(parents=True)
            (root / "src/App/Program.cs").write_text("using System;\nclass Program {\n  static void Main() {\n"
                                                     "    Run();\n    var x = obj.Name;\n  }\n}\n")
            trace = ("Unhandled exception. System.NullReferenceException: Object reference not set to an instance "
                     "of an object.\n   at App.Program.Main() in C:\\Users\\John Smith\\src\\App\\Program.cs:line 5")
            locs = self.context.trace_locations(trace, ["src/App/Program.cs"], root)
            self.assertEqual([(loc["file"], loc["line"]) for loc in locs], [("src/App/Program.cs", 5)])
            self.assertEqual(locs[0]["code"], "var x = obj.Name;")

    def test_language_names_are_not_project_symbols(self):
        names = self.context.candidate_symbols("AttributeError: 'NoneType' object has no attribute 'getTotal' "
                                               "in JavaScript and PostgreSQL")
        self.assertEqual(names, ["getTotal"])

    def test_symbols_are_found_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app/orders.py").write_text("def get_order_total(order):\n    return 1\n")
            (root / "app/views.py").write_text("from app.orders import get_order_total\nget_order_total(x)\n")
            (root / "node_modules/lib").mkdir(parents=True)
            (root / "node_modules/lib/x.js").write_text("function get_order_total() {}\n")
            ctx = self.context.gather("get_order_total returns the wrong value", root)
            self.assertIs(ctx["git"], False)
            self.assertEqual(ctx["symbols"], [{"name": "get_order_total", "defined": ["app/orders.py:1"],
                                               "files": 2}])


class LongRequestTests(unittest.TestCase):
    """A pasted log or document (hundreds of KB) must not stall a plan."""

    LIMIT_SECONDS = 15  # generous: about 1 s on a laptop; CI machines are slower

    def test_long_requests_finish_quickly(self):
        import random
        import time
        rng = random.Random(7)
        words = ("timeout deploy vendor error React we users budget revenue should or Vue hire latency cache "
                 "database customer churn lỗi doanh thu giảm nên chọn hay").split()
        lines, size = [], 0
        while size < 250_000:
            line = " ".join(rng.choice(words) for _ in range(rng.randint(5, 30)))
            lines.append(line)
            size += len(line.encode("utf-8")) + 1
        text = "\n".join(lines)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        for skill in ("make-decision", "problem-solving-pro", "code-solving"):
            args = [sys.executable, str(SKILLS / skill / "scripts/search.py"), "--stdin", "--plan", "--depth", "deep"]
            if skill == "code-solving":
                args.append("--no-context")
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                start = time.monotonic()
                r = subprocess.run(args, input=text.encode("utf-8"), cwd=tmp, env=env, capture_output=True)
                elapsed = time.monotonic() - start
                self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace")[-500:])
                self.assertLess(elapsed, self.LIMIT_SECONDS)


class CodeExecutiveDepthTests(unittest.TestCase):
    """code-solving executive depth leads with a summary a stakeholder can act on."""

    def test_executive_plan_starts_with_a_summary(self):
        _, advisor = load_skill("code-solving")
        engine = advisor.CodeSolvingAdvisor()
        with tempfile.TemporaryDirectory() as tmp:
            query = "Production checkout returns 502 for all users since the deploy"
            plans = {d: engine.generate(query, depth=d, project_dir=tmp) for d in ("deep", "executive")}
        texts = {d: advisor.format_markdown(p) for d, p in plans.items()}
        headings = [line[4:] for line in texts["executive"].splitlines() if line.startswith("### ")]
        self.assertEqual(headings[0], "Executive summary")
        self.assertNotIn("Executive summary", texts["deep"])
        summary = texts["executive"].split("### Executive summary")[1].split("###")[0]
        for label in ("Situation", "Evidence so far", "Approach", "Main risks", "Decision needed"):
            self.assertIn(f"**{label}:**", summary)
        self.assertIn("mitigation", summary)  # incidents: mitigate before root-causing
        self.assertIn("EXECUTIVE SUMMARY", advisor.format_text(plans["executive"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
