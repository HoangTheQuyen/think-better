#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Workspace - progress of a saved step-by-step decision workspace
(decision-plans/<name>/), so the work can resume in a later session: which
steps are done, which files were filled in, and what to do next.

A step is done when its row in 00-OVERVIEW.md is ticked (☑, ✅, [x], x, yes,
done); `--done <step>` ticks it. Whether a file was filled in is judged
against the content it was generated with, recorded in .workspace.json.
"""

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

PLANS_DIR = "decision-plans"
STATE_FILE = ".workspace.json"
OVERVIEW = "00-OVERVIEW.md"
UNTICKED = "☐"

STEPS = [
    {"number": 1, "label": "Classify the decision", "file": "01-DECISION-TYPE.md",
     "todo": "Write the one-sentence decision statement, the decision owner and the deadline; "
             "confirm the decision type and whether it is a one-way or two-way door.",
     "done_when": "Decision statement, owner and deadline are written in 01-DECISION-TYPE.md."},
    {"number": 2, "label": "Apply the framework", "file": "02-FRAMEWORK.md",
     "todo": "Follow the framework's steps for this decision and note where you deviate.",
     "done_when": "Each framework step has a note for this decision."},
    {"number": 3, "label": "Define criteria", "file": "03-CRITERIA.md",
     "todo": "Agree on at most 5 criteria and their weights BEFORE scoring any option.",
     "done_when": "Criteria table filled in, weights sum to 100, agreed by whoever decides."},
    {"number": 4, "label": "Analyze", "file": "04-ANALYSIS.md",
     "todo": "List the key assumptions and test the riskiest ones with the analysis techniques.",
     "done_when": "Each key assumption has evidence or a test result."},
    {"number": 5, "label": "Evaluate the options", "file": "05-OPTIONS.md",
     "todo": "Score every option on every criterion, then run --matrix with --scores for the weighted "
             "totals, the winner and the smallest weight change that flips it.",
     "done_when": "Matrix filled in; winner and flip point recorded."},
    {"number": 6, "label": "Decide", "file": "06-DECISION.md",
     "todo": "Write the decision and rationale, run the pre-mortem, set kill criteria and a review date, "
             "then log it with --journal.",
     "done_when": "Decision, pre-mortem, kill criteria and review date are written; journal entry created."},
]
STEP_NAMES = {"classify": 1, "type": 1, "statement": 1, "framework": 2, "criteria": 3, "analysis": 4,
              "analyze": 4, "assumptions": 4, "options": 5, "evaluate": 5, "score": 5, "matrix": 5,
              "decide": 6, "decision": 6}

# | 3. Define criteria | [03-CRITERIA.md](./03-CRITERIA.md) | ☐ |
ROW = re.compile(r"^\|\s*(?P<num>\d)\.\s*(?P<label>[^|]+?)\s*\|\s*\[[^\]]*\]\(\./(?P<file>[^)]+)\)\s*\|"
                 r"(?P<mark>[^|\n]*)\|\s*$", re.M)
TICKED = re.compile(r"☑|✅|✔|\[x\]|^\s*(x|yes|done)\s*$", re.I)


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
    state.update({"request": plan.get("request", ""), "project_name": plan.get("project_name", ""),
                  "type": plan["decision_type"]["name"], "criteria": plan["criteria"]["domain"],
                  "options": plan.get("options", []), "depth": plan.get("depth", "standard")})
    state.setdefault("files", {}).update({name: digest(content) for name, content in written.items()})
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _state(plan_dir: Path) -> dict:
    try:
        return json.loads((Path(plan_dir) / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ============ FINDING WORKSPACES ============
def list_workspaces(base) -> list:
    """Workspace folders under base/decision-plans, most recently changed first."""
    root = Path(base) / PLANS_DIR
    if not root.is_dir():
        return []
    found = []
    for d in root.iterdir():
        if d.is_dir() and (d / OVERVIEW).exists():
            latest = max(f.stat().st_mtime for f in d.iterdir() if f.is_file())
            found.append((latest, d))
    return [d for _, d in sorted(found, key=lambda x: x[0], reverse=True)]


def pick_workspace(base, text: str = "", name: str = ""):
    """The workspace named exactly, else the one whose name and request share most words with
    text, else the most recently changed. None when there is none."""
    spaces = list_workspaces(base)
    if not spaces:
        return None
    if name:
        return next((d for d in spaces if name in (d.name, _slug(d.name))), None)
    words = set(re.findall(r"\w{3,}", str(text).lower()))
    if words:
        def score(d):
            about = d.name.replace("-", " ") + " " + _state(d).get("request", "")
            return len(words & set(re.findall(r"\w{3,}", about.lower())))
        best = max(spaces, key=score)
        if score(best):
            return best
    return spaces[0]


# ============ STATUS ============
def workspace_status(plan_dir) -> dict:
    """Rows of the overview with their done mark and file state, and the next open step."""
    plan_dir = Path(plan_dir)
    try:
        text = (plan_dir / OVERVIEW).read_text(encoding="utf-8")
    except OSError:
        text = ""
    state = _state(plan_dir)
    rows = []
    for m in ROW.finditer(text):
        path = plan_dir / m.group("file")
        exists = path.exists()
        original = state.get("files", {}).get(m.group("file"))
        if not exists or not original:
            filled = None
        else:
            filled = digest(path.read_text(encoding="utf-8")) != original
        rows.append({"step": int(m.group("num")), "label": f"{m.group('num')}. {m.group('label')}",
                     "file": m.group("file"), "exists": exists, "filled": filled,
                     "done": bool(TICKED.search(m.group("mark").strip()))})
    next_row = next((r for r in rows if not r["done"]), None)
    request = state.get("request", "")
    if not request:
        found = re.search(r"\*\*Request:\*\*\s*(.*)", text)
        request = found.group(1).strip() if found else ""
    return {"name": plan_dir.name, "path": str(plan_dir), "request": request,
            "type": state.get("type", ""), "criteria": state.get("criteria", ""),
            "options": state.get("options", []), "rows": rows, "next": next_row,
            "done": bool(rows) and next_row is None}


# ============ MARKING STEPS ============
def step_number(step: str) -> int:
    """'3', 'criteria' or '3. Define criteria' -> 3."""
    s = str(step).strip().lower()
    m = re.match(r"(\d)", s)
    if m and 1 <= int(m.group(1)) <= len(STEPS):
        return int(m.group(1))
    for name, number in STEP_NAMES.items():
        if s.startswith(name):
            return number
    raise ValueError(f"unknown step {step!r}; use 1-{len(STEPS)} or a step name ({', '.join(STEP_NAMES)})")


def mark(plan_dir, step: str, done: bool = True) -> str:
    """Tick (or untick) the overview row of `step`; returns the row label."""
    number = step_number(step)
    path = Path(plan_dir) / OVERVIEW
    text = path.read_text(encoding="utf-8")
    for m in ROW.finditer(text):
        if int(m.group("num")) == number:
            start, end = m.span("mark")
            path.write_text(text[:start] + (" ☑ " if done else f" {UNTICKED} ") + text[end:], encoding="utf-8")
            return f"{m.group('num')}. {m.group('label')}"
    raise ValueError(f"step {number} has no row in {path}")


# ============ FORMATTING ============
def format_status(status: dict, others: list = (), command: str = "search.py") -> str:
    """Markdown progress report with the next step's guidance."""
    out = [f"## Decision workspace: {status['name']}", ""]
    if status["request"]:
        out.append(f"**Request:** {status['request']}")
    if status["type"]:
        out.append(f"**Decision type:** {status['type']}  |  **Criteria:** {status['criteria']}")
    if status["options"]:
        out.append("**Options:** " + " | ".join(status["options"]))
    out += [f"**Folder:** `{status['path']}`", "", "| Step | File | Filled in | Done? |", "|---|---|---|---|"]
    for r in status["rows"]:
        filled = {True: "yes", False: "not yet", None: "?" if r["exists"] else "missing"}[r["filled"]]
        out.append(f"| {r['label']} | `{r['file']}` | {filled} | {'☑' if r['done'] else UNTICKED} |")
    out.append("")
    nxt = status["next"]
    if status["done"]:
        out.append("**All steps are done.** Log the decision with `--journal` (with `--confidence` and "
                   "`--review-in`) if you have not, and revisit it on the review date.")
    elif not status["rows"]:
        out.append("No step table found in 00-OVERVIEW.md.")
    else:
        step = STEPS[nxt["step"] - 1]
        out += [f"### Next: {nxt['label']}  (`{nxt['file']}`)", "", step["todo"],
                f"- **Done when:** {step['done_when']}", "",
                "Read the files of the finished steps first: they hold the decisions so far. Then tick it:",
                f"`{command} --done {nxt['step']} -p {status['name']}`"]
    if others:
        out += ["", "Other workspaces: " + ", ".join(f"`{o}`" for o in others)]
    return "\n".join(out) + "\n"


def _saved_identity(plan_dir: Path) -> tuple:
    """(request, decision type) of the plan saved in plan_dir; empty strings when there is none."""
    state = _state(plan_dir)
    request, kind = state.get("request", ""), state.get("type", "")
    if not request:
        try:
            text = (Path(plan_dir) / OVERVIEW).read_text(encoding="utf-8")
        except OSError:
            text = ""
        found = re.search(r"\*\*Request:\*\*\s*(.*)", text)
        request = found.group(1).strip() if found else ""
        found = re.search(r"\*\*Decision type:\*\*\s*([^|\n]+?)\s*(?:\||$)", text, re.M)
        kind = found.group(1).strip() if found else ""
    return request, kind


# ============ SAVING INTO AN EXISTING FOLDER ============
def _same_text(saved: str, new: str) -> bool:
    """Whether a saved request is the new one (the overview may hold only its start, ending in '…')."""
    def norm(text):
        return " ".join(unicodedata.normalize("NFC", str(text)).split())
    saved, new = norm(saved), norm(new)
    if saved.endswith("…"):
        return new.startswith(saved.rstrip("…").rstrip())
    return saved == new


def prepare_folder(plan_dir: Path, request: str, type_name: str, new_files=(), force: bool = False) -> list:
    """Check that plan_dir may take this plan before anything is written; returns the files removed.

    A folder that already holds a plan for another request or type is
    refused unless force is set, so two plans never mix in one workspace
    (the overview and .workspace.json would disagree). With force, the old
    plan's generated files that were never edited and that the new plan
    does not write are removed, and progress tracking starts over.

    Raises:
        ValueError: the folder holds a different plan and force is not set.
    """
    plan_dir = Path(plan_dir)
    saved_request, saved_type = _saved_identity(plan_dir)
    if not saved_request and not saved_type:
        return []
    same_request = not saved_request or _same_text(saved_request, request)
    same_type = not saved_type or saved_type.lower() == str(type_name).lower()
    if same_request and same_type:
        return []
    if not force:
        what = f"{saved_type}: " if saved_type else ""
        shown = " ".join(str(saved_request).split())
        shown = shown if len(shown) <= 80 else shown[:79].rstrip() + "…"
        raise ValueError(f"workspace '{plan_dir.name}' already holds another plan ({what}\"{shown}\"); "
                         f"pick another name with -p, or add --force to replace that plan")
    removed = []
    state = _state(plan_dir)
    for name, original in state.get("files", {}).items():
        path = plan_dir / name
        if name in new_files or not path.is_file():
            continue
        try:
            untouched = digest(path.read_text(encoding="utf-8")) == original
        except (OSError, UnicodeDecodeError):
            untouched = False
        if untouched:
            path.unlink()
            removed.append(name)
    try:
        (plan_dir / STATE_FILE).unlink()
    except OSError:
        pass
    return removed


def _slug(text: str) -> str:
    """The folder name a project name gets today (accents folded), for folders saved before that."""
    text = unicodedata.normalize("NFKD", str(text).replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[\s_-]+", "-", re.sub(r"[^\w\s-]", " ", text)).strip("-")[:50].strip("-")
