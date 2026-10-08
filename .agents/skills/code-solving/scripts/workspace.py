#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving Workspace - progress of a saved step-by-step workspace
(coding-plans/<name>/), so work can resume in a later session: which gates
are met, which files were filled in, and the next step with its gate.

A gate is met when its row in 00-OVERVIEW.md is ticked (☑, ✅, [x], x, yes,
done); `--done <step>` ticks it. Whether a file was filled in is judged
against the content it was generated with, recorded in .workspace.json.
"""

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

PLANS_DIR = "coding-plans"
STATE_FILE = ".workspace.json"
OVERVIEW = "00-OVERVIEW.md"

# | 3-4. Prioritize & Plan | [03-PLAN.md](./03-PLAN.md) | ☐ |
ROW = re.compile(r"^\|\s*(?P<nums>\d(?:-\d)?)\.\s*(?P<label>[^|]+?)\s*\|\s*\[[^\]]*\]\(\./(?P<file>[^)]+)\)\s*\|"
                 r"(?P<gate>[^|\n]*)\|\s*$", re.M)
TICKED = re.compile(r"☑|✅|✔|\[x\]|^\s*(x|yes|done|met)\s*$", re.I)
UNTICKED = "☐"
STEP_NAMES = {"define": 1, "decompose": 2, "prioritize": 3, "plan": 4, "execute": 5, "verify": 6,
              "communicate": 7}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_state(plan_dir: Path, plan: dict, written: dict) -> None:
    """Remember what each written file looked like when generated, to tell later if it was filled in."""
    path = Path(plan_dir) / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state.setdefault("created", datetime.now().strftime("%Y-%m-%d %H:%M"))
    state.update({"type": plan["task"]["type"], "request": plan["query"],
                  "project_name": plan["project_name"]})
    files = state.setdefault("files", {})
    files.update({name: digest(content) for name, content in written.items()})
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ============ FINDING WORKSPACES ============
def list_workspaces(base: Path) -> list:
    """Workspace folders under base/coding-plans, most recently changed first."""
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
        return next((d for d in spaces if name in (d.name, _slug(d.name))), None)
    words = set(re.findall(r"\w{3,}", text.lower()))
    if words:
        def score(d):
            about = d.name.replace("-", " ") + " " + _read_overview(d).get("request", "")
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
    task = re.search(r"\*\*Task:\*\*\s*(?P<name>.+?)\s*\(`(?P<type>[\w-]+)`\)", text)
    request = re.search(r"\*\*Request:\*\*\s*(.*)", text)
    return {"text": text, "type": task.group("type") if task else "", "task": task.group("name") if task else "",
            "request": request.group(1).strip() if request else ""}


# ============ STATUS ============
def _numbers(nums: str) -> list:
    if "-" in nums:
        lo, hi = nums.split("-")
        return list(range(int(lo), int(hi) + 1))
    return [int(nums)]


def workspace_status(plan_dir: Path) -> dict:
    """Rows of the overview with gate and file state, the next step and checklist counts."""
    plan_dir = Path(plan_dir)
    overview = _read_overview(plan_dir)
    try:
        state = json.loads((plan_dir / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    rows = []
    for m in ROW.finditer(overview.get("text", "")):
        path = plan_dir / m.group("file")
        exists = path.exists()
        content = path.read_text(encoding="utf-8") if exists else ""
        original = state.get("files", {}).get(m.group("file"))
        if not exists:
            filled = None
        elif original:
            filled = digest(content) != original
        else:
            filled = None  # created before progress tracking: unknown
        rows.append({"steps": _numbers(m.group("nums")), "label": f"{m.group('nums')}. {m.group('label')}",
                     "file": m.group("file"), "exists": exists, "filled": filled,
                     "met": bool(TICKED.search(m.group("gate").strip()))})
    next_row = next((r for r in rows if not r["met"]), None)
    verify = _checkboxes(plan_dir / "05-VERIFY.md")
    log_rows = _table_rows(plan_dir / "04-LOG.md")
    return {"name": plan_dir.name, "path": str(plan_dir), "type": overview.get("type") or state.get("type", ""),
            "task": overview.get("task", ""), "request": overview.get("request") or state.get("request", ""),
            "rows": rows, "next": next_row, "done": bool(rows) and next_row is None,
            "verify": verify, "log_rows": log_rows}


def _checkboxes(path: Path) -> tuple:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return (0, 0)
    boxes = re.findall(r"^\s*[-*] \[( |x|X)\]", text, flags=re.M)
    return (sum(1 for b in boxes if b.lower() == "x"), len(boxes))


def _table_rows(path: Path) -> int:
    """Log rows with something written after the row number."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    count = 0
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 2 and cells[0].isdigit() and any(cells[2:]):
            count += 1
    return count


# ============ MARKING GATES ============
def step_number(step: str) -> int:
    """'2', 'decompose' or '2. Decompose' -> 2."""
    s = str(step).strip().lower()
    m = re.match(r"(\d)", s)
    if m and 1 <= int(m.group(1)) <= 7:
        return int(m.group(1))
    for name, number in STEP_NAMES.items():
        if s.startswith(name):
            return number
    raise ValueError(f"unknown step {step!r}; use 1-7 or a step name ({', '.join(STEP_NAMES)})")


def mark(plan_dir: Path, step: str, done: bool = True) -> str:
    """Tick (or untick) the overview row that holds `step`; returns the row label."""
    number = step_number(step)
    path = Path(plan_dir) / OVERVIEW
    text = path.read_text(encoding="utf-8")
    for m in ROW.finditer(text):
        if number in _numbers(m.group("nums")):
            mark_text = " ☑ " if done else f" {UNTICKED} "
            start, end = m.span("gate")
            path.write_text(text[:start] + mark_text + text[end:], encoding="utf-8")
            return f"{m.group('nums')}. {m.group('label')}"
    raise ValueError(f"step {number} has no row in {path}")


# ============ FORMATTING ============
def format_status(status: dict, steps: dict = None, others: list = (), command: str = "search.py") -> str:
    """Markdown progress report.

    steps: {step number: plan step dict} for the next step's guidance;
    command: how to run search.py from where the user is.
    """
    out = [f"## Workspace: {status['name']}", ""]
    out.append(f"**Task:** {status['task']} (`{status['type']}`)" if status["type"] else "")
    if status["request"]:
        out.append(f"**Request:** {status['request']}")
    out += [f"**Folder:** `{status['path']}`", "", "| Step | File | Filled in | Gate met |", "|---|---|---|---|"]
    for r in status["rows"]:
        filled = {True: "yes", False: "not yet", None: "?" if r["exists"] else "missing"}[r["filled"]]
        out.append(f"| {r['label']} | `{r['file']}` | {filled} | {'☑' if r['met'] else '☐'} |")
    done, total = status["verify"]
    extras = []
    if status["log_rows"]:
        extras.append(f"{status['log_rows']} entries in the Execute log")
    if total:
        extras.append(f"Verify checklist {done}/{total}")
    if extras:
        out += ["", "Progress: " + "; ".join(extras) + "."]
    out.append("")
    nxt = status["next"]
    if status["done"]:
        out.append("**All gates are met.** Finish with the hand-off, or start a new plan for follow-up work.")
    elif not status["rows"]:
        out.append("No step table found in 00-OVERVIEW.md.")
    elif nxt:
        out.append(f"### Next: {nxt['label']}  (`{nxt['file']}`)")
        for number in nxt["steps"]:
            s = (steps or {}).get(number)
            if s:
                out += ["", f"**{s['name']}:** {s['guidance']}", f"- **Gate:** {s['gate']}",
                        f"- **Evidence:** {s['evidence']}"]
        out += ["", "Read the earlier files first: they hold the decisions and evidence so far. "
                "When the gate is met with real evidence, tick it:",
                f"`{command} --done {nxt['steps'][-1]} -p {status['name']}`"]
    if others:
        out += ["", "Other workspaces: " + ", ".join(f"`{o}`" for o in others)]
    return "\n".join(line for line in out if line is not None) + "\n"


def _state(plan_dir: Path) -> dict:
    try:
        return json.loads((Path(plan_dir) / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _saved_identity(plan_dir: Path) -> tuple:
    """(request, task type) of the plan saved in plan_dir; empty strings when there is none."""
    state, overview = _state(plan_dir), _read_overview(plan_dir)
    return (state.get("request") or overview.get("request", ""),
            state.get("type") or overview.get("type", ""))


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
