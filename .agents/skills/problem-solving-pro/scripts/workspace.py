#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Workspace - progress of a saved step-by-step plan
(solving-plans/<name>/), so work can resume in a later session: which steps
are done, which files were filled in, and the next step with its quality gate.

A step is done when its row in 00-OVERVIEW.md is ticked (☑, ✅, [x], x, yes,
done); `--done <step>` ticks it. Whether a file was filled in is judged
against the content it was generated with, recorded in .workspace.json.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

PLANS_DIR = "solving-plans"
STATE_FILE = ".workspace.json"
OVERVIEW = "00-OVERVIEW.md"

STEP_FILES = {
    1: ("Define the Problem", "01-PROBLEM-DEFINITION.md"),
    2: ("Disaggregate the Problem", "02-DECOMPOSITION.md"),
    3: ("Prioritize Issues", "03-PRIORITIZATION.md"),
    4: ("Build a Workplan", "04-ANALYSIS-PLAN.md"),
    5: ("Conduct Analyses", "05-FINDINGS.md"),
    6: ("Synthesize Findings", "06-SYNTHESIS.md"),
    7: ("Communicate Results", "07-RECOMMENDATION.md"),
}
STEP_NAMES = {
    "define": 1, "definition": 1, "problem": 1, "disaggregate": 2, "decompose": 2, "decomposition": 2,
    "prioritize": 3, "prioritise": 3, "prioritization": 3, "workplan": 4, "plan": 4, "build": 4,
    "analyze": 5, "analyse": 5, "analysis": 5, "analyses": 5, "conduct": 5, "findings": 5,
    "synthesize": 6, "synthesise": 6, "synthesis": 6, "communicate": 7, "recommend": 7, "recommendation": 7,
}

# | 3. Prioritize Issues | [03-PRIORITIZATION.md](./03-PRIORITIZATION.md) | ☐ |
ROW = re.compile(r"^\|\s*(?P<num>\d)\.\s*(?P<label>[^|]+?)\s*\|\s*\[[^\]]*\]\(\./(?P<file>[^)]+)\)\s*\|"
                 r"(?P<done>[^|\n]*)\|\s*$", re.M)
TICKED = re.compile(r"☑|✅|✔|\[x\]|^\s*(x|yes|done|met)\s*$", re.I)
UNTICKED = "☐"
CANONICAL = "define, decompose, prioritize, plan, analyze, synthesize, communicate"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_state(plan_dir: Path, plan: dict, written: dict) -> None:
    """Remember the request and what each written file looked like when generated."""
    path = Path(plan_dir) / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state.setdefault("created", datetime.now().strftime("%Y-%m-%d %H:%M"))
    state.update({"request": plan["query"], "project_name": plan["project_name"],
                  "type": plan["problem_type"]["name"], "category": plan["problem_category"],
                  "depth": plan["depth"]})
    files = state.setdefault("files", {})
    files.update({name: digest(content) for name, content in written.items()})
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _state(plan_dir: Path) -> dict:
    try:
        return json.loads((Path(plan_dir) / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ============ FINDING WORKSPACES ============
def list_workspaces(base: Path) -> list:
    """Workspace folders under base/solving-plans, most recently changed first."""
    root = Path(base) / PLANS_DIR
    if not root.is_dir():
        return []
    found = []
    for d in root.iterdir():
        if d.is_dir() and (d / OVERVIEW).exists():
            latest = max(f.stat().st_mtime for f in d.iterdir() if f.is_file())
            found.append((latest, d))
    return [d for _, d in sorted(found, key=lambda x: x[0], reverse=True)]


def pick_workspace(base: Path, text: str = "", name: str = ""):
    """The workspace named exactly, else the one whose name and request share most words
    with text, else the most recently changed. None when there is none."""
    spaces = list_workspaces(base)
    if not spaces:
        return None
    if name:
        return next((d for d in spaces if d.name == name), None)
    words = set(re.findall(r"\w{3,}", text.lower()))
    if words:
        def score(d):
            about = d.name.replace("-", " ") + " " + _state(d).get("request", "") + " " + \
                _read_overview(d).get("request", "")
            return len(words & set(re.findall(r"\w{3,}", about.lower())))
        best = max(spaces, key=score)
        if score(best):
            return best
    return spaces[0]


def _read_overview(plan_dir: Path) -> dict:
    try:
        text = (Path(plan_dir) / OVERVIEW).read_text(encoding="utf-8")
    except OSError:
        return {}
    problem = re.search(r"\*\*Problem:\*\*\s*([^|\n]+?)\s*\|", text) or re.search(r"\*\*Type:\*\*\s*([^\n(]+)", text)
    context = re.search(r"\*\*Context:\*\*\s*([^|\n(]+)", text)
    request = re.search(r"\*\*Request:\*\*\s*(.*)", text)
    return {"text": text, "type": problem.group(1).strip() if problem else "",
            "category": context.group(1).strip() if context else "",
            "request": request.group(1).strip() if request else ""}


# ============ STATUS ============
def workspace_status(plan_dir: Path) -> dict:
    """Rows of the overview with done and filled-in state, the next step and progress counts."""
    plan_dir = Path(plan_dir)
    overview = _read_overview(plan_dir)
    state = _state(plan_dir)
    matches = [(int(m.group("num")), m.group("label"), m.group("file"), m.group("done"))
               for m in ROW.finditer(overview.get("text", ""))]
    legacy = not matches
    if legacy:  # saved before progress tracking: no table yet, nothing ticked
        matches = [(n, label, file, "") for n, (label, file) in STEP_FILES.items()]
    rows = []
    for number, label, file, done in matches:
        path = plan_dir / file
        exists = path.exists()
        original = state.get("files", {}).get(file)
        if not exists or not original:
            filled = None  # missing, or saved before tracking: unknown
        else:
            filled = digest(path.read_text(encoding="utf-8")) != original
        rows.append({"step": number, "label": f"{number}. {label}", "file": file, "exists": exists,
                     "filled": filled, "done": bool(TICKED.search(done.strip()))})
    next_row = next((r for r in rows if not r["done"]), None)
    return {"name": plan_dir.name, "path": str(plan_dir),
            "type": state.get("type") or overview.get("type", ""),
            "category": state.get("category") or overview.get("category", ""),
            "request": state.get("request") or overview.get("request", ""),
            "rows": rows, "next": next_row, "done": bool(rows) and next_row is None, "legacy": legacy,
            "decisions": _table_rows(plan_dir / "DECISION-LOG.md"),
            "findings": _findings(plan_dir / "05-FINDINGS.md")}


def _table_rows(path: Path) -> int:
    """Log rows with something written after the row number and date."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    count = 0
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 3 and cells[0].isdigit() and any(cells[2:-1]):
            count += 1
    return count


def _findings(path: Path) -> int:
    """Findings whose Insight line was filled in."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return len(re.findall(r"^- \*\*Insight:\*\*[ \t]*\S", text, flags=re.M))


# ============ MARKING STEPS ============
def step_number(step: str) -> int:
    """'2', 'decompose' or '2. Disaggregate' -> 2."""
    s = str(step).strip().lower()
    m = re.match(r"(\d+)", s)
    if m:
        if 1 <= int(m.group(1)) <= 7:
            return int(m.group(1))
        raise ValueError(f"unknown step {step!r}; use 1-7 or a step name ({CANONICAL})")
    for name, number in STEP_NAMES.items():
        if s.startswith(name):
            return number
    raise ValueError(f"unknown step {step!r}; use 1-7 or a step name ({CANONICAL})")


def progress_table(done=()) -> str:
    """The progress table of 00-OVERVIEW.md; `done` holds the ticked step numbers."""
    lines = ["| Step | File | Done? |", "|---|---|---|"]
    for number, (name, file) in STEP_FILES.items():
        lines.append(f"| {number}. {name} | [{file}](./{file}) | {'☑' if number in done else UNTICKED} |")
    return "\n".join(lines)


def mark(plan_dir: Path, step: str, done: bool = True) -> str:
    """Tick (or untick) the overview row of `step`; returns the row label.

    An overview saved before progress tracking gets the table appended first.
    """
    number = step_number(step)
    path = Path(plan_dir) / OVERVIEW
    text = path.read_text(encoding="utf-8")
    if not ROW.search(text):
        text = text.rstrip("\n") + "\n\n## Progress\n\n" + progress_table() + "\n"
    for m in ROW.finditer(text):
        if int(m.group("num")) == number:
            start, end = m.span("done")
            path.write_text(text[:start] + (" ☑ " if done else f" {UNTICKED} ") + text[end:], encoding="utf-8")
            return f"{number}. {m.group('label')}"
    raise ValueError(f"step {number} has no row in {path}")


# ============ FORMATTING ============
def format_status(status: dict, steps: dict = None, others: list = (), command: str = "search.py") -> str:
    """Markdown progress report.

    steps: {step number: step dict from advisor.load_steps()} for the next step's guidance;
    command: how to run search.py from where the user is.
    """
    out = [f"## Workspace: {status['name']}", ""]
    if status["type"] or status["category"]:
        out.append(f"**Problem:** {status['type'] or '?'} | **Context:** {status['category'] or '?'}")
    if status["request"]:
        request = " ".join(status["request"].split())
        out.append(f"**Request:** {request if len(request) <= 300 else request[:300].rsplit(' ', 1)[0] + ' …'}")
    out += [f"**Folder:** `{status['path']}`", "", "| Step | File | Filled in | Done? |", "|---|---|---|---|"]
    for r in status["rows"]:
        filled = {True: "yes", False: "not yet", None: "?" if r["exists"] else "missing"}[r["filled"]]
        out.append(f"| {r['label']} | `{r['file']}` | {filled} | {'☑' if r['done'] else '☐'} |")
    extras = []
    if status["findings"]:
        extras.append(f"{status['findings']} findings recorded")
    if status["decisions"]:
        extras.append(f"{status['decisions']} entries in the decision log")
    if extras:
        out += ["", "Progress: " + "; ".join(extras) + "."]
    if status["legacy"]:
        out += ["", "This workspace was saved before progress tracking; `--done` adds the progress table "
                "to 00-OVERVIEW.md."]
    out.append("")
    nxt = status["next"]
    if status["done"]:
        out.append("**All steps are done.** Deliver the recommendation (07-RECOMMENDATION.md), or start a new "
                   "plan for follow-up work.")
    elif nxt:
        out.append(f"### Next: {nxt['label']}  (`{nxt['file']}`)")
        s = (steps or {}).get(nxt["step"])
        if s:
            out += ["", s["description"], f"- **Do:** {s['activities']}",
                    f"- **Done when (quality gate):** {s['gate']}", f"- **Pitfalls:** {s['pitfalls']}"]
        out += ["", "Read the files of the steps already done first: they hold the definition, tree and "
                "evidence so far. When the quality gate is met and written into the step's file, tick it:",
                f"`{command} --done {nxt['step']} -p {status['name']}`"]
    if others:
        out += ["", "Other workspaces: " + ", ".join(f"`{o}`" for o in others)]
    return "\n".join(out) + "\n"
