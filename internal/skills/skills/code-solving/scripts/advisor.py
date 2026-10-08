#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving Advisor - builds a 7-step coding plan (Define, Decompose,
Prioritize, Plan, Execute, Verify, Communicate) for a task type, with an
evidence gate per step, named techniques, tests, principles, bias warnings,
a review checklist and the hand-off artifact.

Usage:
    from advisor import generate_code_plan
    print(generate_code_plan("TypeError in checkout", task_type="debug"))
"""

from datetime import datetime
from pathlib import Path

from context import gather as gather_context
from workspace import prepare_folder, record_state
from core import (
    classify_task, detect_project_commands, find_named, load_csv, match_errors, save_docs, search,
    slugify, default_output_dir, task_type_names,
)

VALID_DEPTHS = ["quick", "standard", "deep", "executive"]

DEPTH_CONFIG = {
    "quick": {"steps": ["Define", "Execute", "Verify"], "techniques": 3, "testing": 1,
              "principles": 0, "biases": 1, "review": 0, "extras": 0},
    "standard": {"steps": None, "techniques": 5, "testing": 3,
                 "principles": 3, "biases": 2, "review": 4, "extras": 0},
    "deep": {"steps": None, "techniques": 8, "testing": 3,
             "principles": 5, "biases": 4, "review": 11, "extras": 3},
    "executive": {"steps": None, "techniques": 8, "testing": 3,
                  "principles": 5, "biases": 4, "review": 11, "extras": 3},
}

# Task types whose Execute step is a search for a cause, logged as hypotheses
HYPOTHESIS_TYPES = {"debug", "flaky-test", "incident", "performance"}

# Small tasks fold Decompose, Prioritize and Plan into Execute (quick and standard depth)
LIGHT_STEPS = {"quick-fix": ["Define", "Execute", "Verify", "Communicate"]}

HANDOFF_FILES = {
    "Pull Request Description": "06-PR.md",
    "Blameless Postmortem": "06-POSTMORTEM.md",
    "Design Doc (RFC)": "06-DESIGN-DOC.md",
    "Code Review Report": "06-REVIEW.md",
    "Code Explanation": "06-EXPLANATION.md",
    "Security Fix Note": "06-SECURITY-NOTE.md",
    "Commit Message": "06-COMMIT.md",
}


def _short_name(text: str, limit: int = 60) -> str:
    """First `limit` characters of text, cut at a word boundary."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut or text[:limit]


# ============ PLAN ============
class CodeSolvingAdvisor:
    """Assembles a plan from the task type's own recommendations plus search."""

    def generate(self, query: str, project_name: str = None, depth: str = "standard",
                 task_type: str = None, project_dir: str = None, context: bool = True,
                 diff: str = None) -> dict:
        """Build the plan dict.

        context: look up what the request points at in the project (stack-trace
        locations, named files and symbols, recent commits, working tree).
        diff: base to review against ("auto" picks one); reviews default to "auto".

        Raises:
            ValueError: if task_type, depth or the diff base is invalid.
        """
        if depth not in DEPTH_CONFIG:
            raise ValueError(f"unknown depth {depth!r}; choose one of: {', '.join(VALID_DEPTHS)}")
        cfg = DEPTH_CONFIG[depth]
        task, source = classify_task(query, task_type)

        wanted = cfg["steps"]
        if task["Type"] in LIGHT_STEPS and depth in ("quick", "standard"):
            wanted = LIGHT_STEPS[task["Type"]]
        steps = []
        for row in load_csv("steps"):
            if wanted and row["Name"] not in wanted:
                continue
            # A task type may state its own gate inline ("... Gate: ...")
            guidance, _, own_gate = task.get(row["Name"], "").partition("Gate:")
            steps.append({
                "number": int(row["Step"]),
                "name": row["Name"],
                "goal": row["Goal"],
                "guidance": guidance.strip(),
                "gate": (own_gate.strip()[:1].upper() + own_gate.strip()[1:]) or row["Quality Gate"],
                "evidence": row["Evidence"],
                "pitfalls": row["Pitfalls"],
                "file": row["Output File"],
            })

        techniques = (find_named("debugging", task["Techniques"]) +
                      find_named("changes", task["Techniques"]))
        order = [n.strip() for n in task["Techniques"].split(";")]
        techniques.sort(key=lambda r: order.index(r["Technique"]))

        extras = []
        if cfg["extras"]:
            named = {t["Technique"] for t in techniques}
            hits = search(query, "debugging", 5)["results"] + search(query, "changes", 5)["results"]
            extras = [r for r in hits if r["Technique"] not in named][:cfg["extras"]]

        artifact = (find_named("artifacts", task["Artifact"]) or [{}])[0]

        try:
            commands = detect_project_commands(Path(project_dir) if project_dir else None)
        except OSError:
            commands = []

        ctx = {}
        if context:
            if diff is None and task["Type"] == "review":
                diff = "auto"
            ctx = gather_context(query, Path(project_dir) if project_dir else default_output_dir(), diff)

        # Review areas the diff touches come first, and are never cut by depth
        diff_areas = [a["area"] for a in ctx.get("diff", {}).get("areas", [])]
        focus = [n.strip() for n in task["Review Focus"].split(";") if n.strip()]
        review_names = diff_areas + [n for n in focus if n not in diff_areas]
        review_count = max(cfg["review"], len(diff_areas))

        return {
            "depth": depth,
            "query": query,
            "project_name": project_name or _short_name(query),
            "task": {
                "type": task["Type"],
                "name": task["Name"],
                "description": task["Description"],
                "source": source,
            },
            "steps": steps,
            "techniques": [
                {"name": t["Technique"], "description": t["Description"],
                 "how": t["How to Apply"], "evidence": t.get("Evidence", "")}
                for t in techniques[:cfg["techniques"]]
            ],
            "extra_techniques": [{"name": t["Technique"], "when": t["When to Use"]} for t in extras],
            "testing": [
                {"name": t["Strategy"], "how": t["How to Apply"], "pitfalls": t["Pitfalls"]}
                for t in find_named("testing", task["Testing"])[:cfg["testing"]]
            ],
            "principles": [
                {"name": p["Principle"], "description": p["Description"], "violation": p["Violation Signs"]}
                for p in find_named("principles", task["Principles"])[:cfg["principles"]]
            ],
            "biases": [
                {"name": b["Bias"], "shows_up": b["How It Shows Up"], "countermeasure": b["Countermeasure"]}
                for b in find_named("biases", task["Biases"])[:cfg["biases"]]
            ],
            "review": [
                {"area": r["Area"], "check": r["What to Check"], "red_flags": r["Red Flags"], "how": r["How to Verify"]}
                for r in find_named("review", review_names)[:review_count]
            ],
            "artifact": {"name": artifact.get("Artifact", "Pull Request Description"),
                         "structure": artifact.get("Structure", "")},
            "anti_patterns": task["Anti-Patterns"],
            "escalate": task["Escalate"],
            "commands": [{"purpose": p, "command": c, "source": s} for p, c, s in commands],
            "context": ctx,
            "errors": [
                {"error": e["Error"], "language": e["Language"], "meaning": e["Meaning"],
                 "causes": e["Likely Causes"], "checks": e["First Checks"], "fix": e["Fix"]}
                for e in match_errors(query)
            ],
        }


# ============ FORMATTING ============
def _context_lines(ctx: dict) -> list:
    """The context section: facts found in the project, for Step 2 to start from."""
    lines = []
    if ctx.get("locations"):
        lines.append("**Where the error points** (project frames only):")
        for loc in ctx["locations"]:
            where = f"`{loc['file']}:{loc['line']}`" + (f" in `{loc['func']}`" if loc["func"] else "")
            lines.append(f"- {where}" + (f": `{loc['code']}`" if loc["code"] else ""))
    if ctx.get("files"):
        lines.append("**Files named in the request:** " + ", ".join(f"`{f}`" for f in ctx["files"]))
    if ctx.get("symbols"):
        lines.append("**Symbols:**")
        for s in ctx["symbols"]:
            defined = ("defined at " + ", ".join(f"`{d}`" for d in s["defined"])) if s["defined"] \
                else "definition not found"
            plural = "" if s["files"] == 1 else "s"
            lines.append(f"- `{s['name']}`: {defined}; mentioned in {s['files']} file{plural}")
    if ctx.get("commits"):
        scope = "these files" if ctx.get("touched") else "the repository"
        lines.append(f"**Recent commits touching {scope}** (check them first for regressions):")
        lines += [f"- `{c['sha']}` {c['date']} {c['author']}: {c['subject']}" for c in ctx["commits"]]
    tree = ctx.get("tree")
    if tree and tree.get("branch"):
        line = f"**Working tree:** branch `{tree['branch']}`"
        if tree["change_count"]:
            shown = ", ".join(f"`{c}`" for c in tree["changes"][:5])
            more = f" and {tree['change_count'] - 5} more" if tree["change_count"] > 5 else ""
            line += f", {tree['change_count']} uncommitted changes: {shown}{more}"
        else:
            line += ", no uncommitted changes"
        lines.append(line)
    diff = ctx.get("diff")
    if diff:
        if diff.get("error"):
            lines.append(f"**Diff:** {diff['error']}")
        elif not diff.get("files"):
            lines.append(f"**Diff** (`{diff['label']}`): no changes found. Ask which change to review.")
        else:
            files = diff["files"]
            lines.append(f"**Diff under review** (`{diff['label']}`): {len(files)} file{'' if len(files) == 1 else 's'}, "
                         f"+{diff['added']} −{diff['removed']}")
            lines += ["", "| File | + | − |", "|---|---|---|"]
            lines += [f"| `{f['file']}`{' (new, untracked)' if f.get('new') else ''} | {f['added']} | {f['removed']} |"
                      for f in files[:15]]
            if len(files) > 15:
                lines.append(f"| … {len(files) - 15} more | | |")
            lines.append("")
            if diff["areas"]:
                lines.append("**Review focus from the diff** (checked first in the review checklist):")
                for a in diff["areas"]:
                    more = f" (+{a['count'] - len(a['reasons'])} more)" if a["count"] > len(a["reasons"]) else ""
                    lines.append(f"- **{a['area']}**: " + "; ".join(a["reasons"]) + more)
    if lines:
        lines.insert(0, "Found in the code and git history, not guessed. Read these first in Step 2.")
    elif ctx.get("git") is False:
        lines.append("Not a git repository: no history or diff available. Search the code by hand in Step 2.")
    return lines


def _sections(plan: dict) -> list:
    """Plan as (heading, [lines]) pairs, lines in light markdown."""
    task = plan["task"]
    depth = plan["depth"]
    out = []

    head = [f"**Task:** {task['name']} (`{task['type']}`, {task['source']}): {task['description']}"]
    if task["source"] == "default":
        head.append("> No task type matched clearly. Re-run with `--type` "
                    f"({', '.join(task_type_names())}).")
    head.append("Work the steps in order. Do not move on until the step's **Gate** is met "
                "with evidence you actually produced (command output, test result).")
    if task["type"] in LIGHT_STEPS and len(plan["steps"]) == len(LIGHT_STEPS[task["type"]]):
        head.append("Small change: Decompose, Prioritize and Plan are folded into Execute. "
                    "If it turns out to touch logic, re-run with `--type feature` or `--type debug`.")
    out.append(("", head))

    lines = _context_lines(plan.get("context", {}))
    if lines:
        out.append(("Context from the project", lines))

    for e in plan.get("errors", []):
        out.append((f"Known error: {e['error']} ({e['language']})", [
            e["meaning"],
            f"- **Likely causes:** {e['causes']}",
            f"- **Check first:** {e['checks']}",
            f"- **Fix at the root:** {e['fix']}",
            "Treat the causes as hypotheses to test in Step 5, not as the answer.",
        ]))

    for step in plan["steps"]:
        lines = [f"*{step['goal']}*", step["guidance"]]
        lines.append(f"- **Gate:** {step['gate']}")
        lines.append(f"- **Evidence:** {step['evidence']}")
        if depth in ("deep", "executive"):
            lines.append(f"- **Pitfalls:** {step['pitfalls']}")
        if step["name"] == "Verify" and plan["commands"]:
            lines.append("- **Run:** the commands under *Project checks* below (`one test` is for "
                         "the inner loop while you work).")
        out.append((f"{step['number']}. {step['name']}", lines))

    if plan["commands"]:
        lines = ["| Purpose | Command | Found in |", "|---|---|---|"]
        lines += [f"| {c['purpose']} | `{c['command']}` | {c['source']} |" for c in plan["commands"]]
    else:
        lines = ["No test/lint/build config detected. Find the project's test command before Step 6 "
                 "(README, CI config) and say so if there is none."]
    out.append(("Project checks", lines))

    if plan["techniques"]:
        lines = []
        for t in plan["techniques"]:
            lines.append(f"- **{t['name']}**: {t['description']}")
            if depth != "quick":
                lines.append(f"  How: {t['how']}")
        for t in plan["extra_techniques"]:
            lines.append(f"- *Also consider* **{t['name']}**: {t['when']}")
        out.append(("Techniques", lines))

    if plan["testing"]:
        out.append(("Testing", [f"- **{t['name']}**: {t['how']}" for t in plan["testing"]]))

    if plan["principles"]:
        out.append(("Design principles",
                    [f"- **{p['name']}**: {p['description']} Watch for: {p['violation']}" for p in plan["principles"]]))

    if plan["biases"]:
        out.append(("Watch out for",
                    [f"- **{b['name']}**: {b['shows_up']} → {b['countermeasure']}" for b in plan["biases"]]))

    if plan["review"]:
        lines = []
        for r in plan["review"]:
            line = f"- [ ] **{r['area']}**: {r['check']}"
            if depth in ("deep", "executive"):
                line += f" Red flags: {r['red_flags']} Verify: {r['how']}"
            lines.append(line)
        out.append(("Review checklist (Step 6)", lines))

    out.append((f"Hand-off: {plan['artifact']['name']}", [plan["artifact"]["structure"]]))
    out.append(("Anti-patterns", [plan["anti_patterns"]]))
    out.append(("Escalate when", [plan["escalate"]]))

    if depth == "executive":
        out.append(("Stakeholder summary", [
            "- **Outcome:** what changes for users or the business, in one sentence",
            "- **Status:** current step and the evidence so far",
            "- **Risk:** what could go wrong and how likely",
            "- **Rollback:** how the change is undone and how fast",
            "- **ETA / next update:**",
        ]))
    return out


def format_markdown(plan: dict) -> str:
    depth = f" [{plan['depth'].upper()}]" if plan["depth"] != "standard" else ""
    out = [f"## Code Plan: {plan['project_name']}{depth}", ""]
    for heading, lines in _sections(plan):
        if heading:
            level = "####" if heading[0].isdigit() else "###"
            out += [f"{level} {heading}", ""]
        out += lines + [""]
    return "\n".join(out).rstrip() + "\n"


def format_text(plan: dict) -> str:
    """Plain-text rendering for terminals (--format ascii)."""
    depth = f" [{plan['depth'].upper()}]" if plan["depth"] != "standard" else ""
    out = [f"CODE PLAN: {plan['project_name']}{depth}", "=" * 72]
    for heading, lines in _sections(plan):
        if heading:
            out += ["", heading.upper(), "-" * min(len(heading), 72)]
        out += [line.replace("**", "").replace("`", "") for line in lines]
    return "\n".join(out) + "\n"


NEXT_STEPS = """
---
**Next steps:**
| Command | When |
|---|---|
| `/code.deep` | More techniques, full review checklist, pitfalls per step |
| `/decide` | Two or more designs with real trade-offs (record an ADR) |
| `/solve` | The root problem is not in the code (process, product, business) |
| Add "save step-by-step" | Create a workspace file per step |
"""


def next_steps_table(text: str, saved_step_docs: bool) -> str:
    """The Next Steps table, without the "save step-by-step" row once the workspace is saved."""
    if not saved_step_docs:
        return text
    return "".join(line for line in text.splitlines(True) if "save step-by-step" not in line)


# ============ PERSISTENCE ============
def _plan_dir(plan: dict, output_dir: str = None) -> Path:
    base = Path(output_dir) if output_dir else default_output_dir()
    plan_dir = base / "coding-plans" / slugify(plan["project_name"])
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


def persist_plan(plan: dict, output_dir: str = None, force: bool = False) -> tuple:
    """Save the plan as coding-plans/<slug>/PLAN.md; returns (path, written).

    An existing PLAN.md is kept unless force is set.
    """
    plan_dir = _plan_dir(plan, output_dir)
    prepare_folder(plan_dir, plan["query"], plan["task"]["type"], ["PLAN.md"], force)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    written, _ = save_docs(plan_dir, {"PLAN.md": format_markdown(plan) + f"\n---\n*Generated: {stamp}*\n"}, force)
    return str(plan_dir / "PLAN.md"), bool(written)


def persist_step_by_step(plan: dict, output_dir: str = None, force: bool = False) -> tuple:
    """Write one workspace file per step; returns (dir, written, kept).

    Files that already exist hold the user's notes and are kept unless force is set.
    """
    plan_dir = _plan_dir(plan, output_dir)
    steps = {s["name"]: s for s in CodeSolvingAdvisor().generate(
        plan["query"], plan["project_name"], "deep", plan["task"]["type"], context=False)["steps"]}
    task = plan["task"]
    handoff = HANDOFF_FILES.get(plan["artifact"]["name"], "06-HANDOFF.md")

    def guide(name):
        s = steps[name]
        return f"> {s['guidance']}\n>\n> **Gate:** {s['gate']}"

    files = {}
    files["00-OVERVIEW.md"] = f"""# {plan['project_name']}

**Task:** {task['name']} (`{task['type']}`)
**Request:** {plan['query']}

| Step | File | Gate met? |
|---|---|---|
| 1. Define | [01-DEFINE.md](./01-DEFINE.md) | ☐ |
| 2. Decompose | [02-CHANGE-MAP.md](./02-CHANGE-MAP.md) | ☐ |
| 3-4. Prioritize & Plan | [03-PLAN.md](./03-PLAN.md) | ☐ |
| 5. Execute | [04-LOG.md](./04-LOG.md) | ☐ |
| 6. Verify | [05-VERIFY.md](./05-VERIFY.md) | ☐ |
| 7. Communicate | [{handoff}](./{handoff}) | ☐ |
"""
    files["01-DEFINE.md"] = f"""# 1. Define

{guide('Define')}

## Statement
<!-- One sentence: what must be true when this is done -->

## Expected vs actual / acceptance criteria
-

## Check that fails today
```
<!-- repro command, failing test, or benchmark baseline -->
```

## Out of scope
-
"""
    ctx = plan.get("context", {})
    rows = [f"| `{loc['file']}:{loc['line']}` | in the stack trace{', ' + loc['func'] if loc['func'] else ''} |  |"
            for loc in ctx.get("locations", [])]
    rows += [f"| `{f}` | named in the request |  |" for f in ctx.get("files", [])]
    rows += [f"| `{s['defined'][0]}` | defines `{s['name']}` (mentioned in {s['files']} file(s)) |  |"
             for s in ctx.get("symbols", []) if s["defined"]]
    rows += [f"| `{f['file']}` | changed in the diff (+{f['added']} −{f['removed']}) |  |"
             for f in ctx.get("diff", {}).get("files", [])[:15]]
    files["02-CHANGE-MAP.md"] = f"""# 2. Decompose: change map

{guide('Decompose')}

| Path | Role | Change? |
|---|---|---|
{chr(10).join(rows) or '|  |  |  |'}

## Call path
<!-- input → ... → output -->
"""
    files["03-PLAN.md"] = f"""# 3-4. Prioritize & Plan

{guide('Prioritize')}

{guide('Plan')}

| # | Task | Proving test / check | Rollback | Done |
|---|---|---|---|---|
| 1 |  |  |  | ☐ |
"""
    if task["type"] in HYPOTHESIS_TYPES:
        causes = [c.strip().rstrip(".") for e in plan.get("errors", [])[:1] for c in e["causes"].split(";")]
        rows = "\n".join(f"| {i} | {c} |  |  |  |" for i, c in enumerate(causes, 1)) or "| 1 |  |  |  |  |"
        log_table = ("| # | Hypothesis | Prediction / check | Result | Verdict |\n"
                     "|---|---|---|---|---|\n" + rows)
    else:
        log_table = "| # | Step | Tests after step | Commit |\n|---|---|---|---|\n| 1 |  |  |  |"
    files["04-LOG.md"] = f"""# 5. Execute: log

{guide('Execute')}

{log_table}
"""
    checks = "\n".join(f"- [ ] `{c['command']}`" for c in plan["commands"]
                       if c["purpose"] != "one test") or "- [ ] <test command>"
    review = "\n".join(f"- [ ] {r['area']}: {r['check']}" for r in plan["review"]) or "- [ ] Diff reviewed"
    files["05-VERIFY.md"] = f"""# 6. Verify

{guide('Verify')}

## Step 1 check passes now
- [ ]

## Project checks
{checks}

## Review
{review}
"""
    sections = [s.strip() for s in plan["artifact"]["structure"].split("/") if s.strip()]
    body = "\n\n".join(f"## {s}\n" for s in sections)
    files[handoff] = f"""# 7. {plan['artifact']['name']}

{guide('Communicate')}

{body}
"""
    prepare_folder(plan_dir, plan["query"], task["type"], files, force)
    written, kept = save_docs(plan_dir, files, force)
    record_state(plan_dir, plan, {name: files[name] for name in written})
    return str(plan_dir), written, kept


# ============ PUBLIC API ============
def generate_code_plan(query: str, project_name: str = None, output_format: str = "markdown",
                       persist: bool = False, output_dir: str = None, depth: str = "standard",
                       step_docs: bool = False, task_type: str = None, project_dir: str = None,
                       force: bool = False, context: bool = True, diff: str = None) -> str:
    """Generate a formatted plan; optionally save it (existing files are kept unless force).

    Raises ValueError for unknown values.
    """
    plan = CodeSolvingAdvisor().generate(query, project_name, depth, task_type, project_dir, context, diff)
    result = format_markdown(plan) if output_format == "markdown" else format_text(plan)
    if persist:
        if step_docs:
            plan_dir, files, kept = persist_step_by_step(plan, output_dir, force)
            result += f"\nWorkspace saved to: {plan_dir}/\n" + "".join(f"  {f}\n" for f in files)
            if kept:
                result += (f"Kept {len(kept)} existing files with your notes (add --force to replace them):\n"
                           + "".join(f"  {f}\n" for f in kept))
        else:
            path, written = persist_plan(plan, output_dir, force)
            result += (f"\nPlan saved to: {path}\n" if written
                       else f"\nKept the existing plan at {path} (add --force to replace it).\n")
    return result + next_steps_table(NEXT_STEPS, persist and step_docs)
