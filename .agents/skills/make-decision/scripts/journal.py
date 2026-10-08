#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Journal - decision journal entries in <project>/.decisions/.

Each entry records the decision, its options, framework, confidence and a
review date; --update appends the actual outcome and a reflection without
touching what the user already wrote. User text is never used as a regex
replacement string and cannot add headings, so it cannot corrupt an entry.
"""

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from core import default_output_dir, slugify

JOURNAL_DIR = ".decisions"
DEFAULT_REVIEW_DAYS = 30
_UNITS = {"d": 1, "w": 7, "m": 30, "y": 365}


class JournalError(ValueError):
    """A journal operation that cannot be done (no entry, ambiguous id, ...)."""


def parse_duration(text: str) -> int:
    """'14d', '2w', '3m', '1y' or '30' -> days.

    Raises:
        ValueError: anything else.
    """
    m = re.fullmatch(r"\s*(\d+)\s*([dwmy]?)\s*", str(text).lower())
    if not m or int(m.group(1)) < 1:
        raise ValueError(f"use a duration like 14d, 2w or 3m (got {text!r})")
    return int(m.group(1)) * _UNITS[m.group(2) or "d"]


def journal_dir(output_dir: str = None) -> Path:
    return (Path(output_dir) if output_dir else default_output_dir()) / JOURNAL_DIR


def _safe(text: str) -> str:
    """User text made safe to put inside an entry: no line can start a heading."""
    lines = str(text).replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    return "\n".join("\\" + ln.lstrip() if ln.lstrip().startswith("#") else ln for ln in lines)


def _one_line(text: str) -> str:
    return " ".join(_safe(text).split())


# ============ CREATE ============
def create_journal(statement: str, project_name: str = None, output_dir: str = None,
                   decision_type: str = "", framework: str = "", options: list = None,
                   criteria: list = None, confidence: int = None,
                   review_days: int = DEFAULT_REVIEW_DAYS, today: date = None) -> str:
    """Write a new journal entry and return its path.

    criteria: [{'name', 'weight'}]; confidence: 0-100 or None (left for the user).
    The file name is the date plus an ASCII slug of the statement, so it is the
    same on every OS whatever Unicode normalization the text arrived in.
    """
    statement = _one_line(statement)
    if not statement:
        raise JournalError("decision statement is empty")
    if confidence is not None and not 0 <= confidence <= 100:
        raise JournalError("confidence must be between 0 and 100")
    today = today or date.today()
    folder = journal_dir(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{today.isoformat()}-{slugify(statement)}"
    path = folder / f"{name}.md"
    if path.exists():
        path = folder / f"{name}-{datetime.now().strftime('%H%M%S')}.md"
    review_by = today + timedelta(days=review_days)

    option_lines = [f"{i}. {_one_line(o)}" for i, o in enumerate(options or [], 1)] or ["1. ", "2. ", "3. "]
    criteria_lines = [f"- {c['name']} ({c['weight']})" for c in criteria or []] or ["- "]
    conf = f"{confidence}%" if confidence is not None else "__% (how likely is it that this works out?)"
    content = f"""# Decision Journal: {statement}

## Metadata
- **Date:** {today.isoformat()}
- **Project:** {_one_line(project_name) if project_name else 'N/A'}
- **Decision Type:** {decision_type or 'N/A'}
- **Framework:** {framework or 'N/A'}
- **Confidence:** {conf}
- **Review by:** {review_by.isoformat()}
- **Status:** Created

## Decision
{statement}

## Options
{chr(10).join(option_lines)}

## Evaluation Criteria
{chr(10).join(criteria_lines)}

## Hypothesis (Day One Answer)
<!-- Your best guess before the analysis -->

## Expected Outcomes
<!-- What you expect to happen, and by when. Make it checkable on the review date. -->

## Kill Criteria
<!-- Signals that would make you reverse or revisit this decision -->

## Rationale
<!-- Why this option over the others? -->

## Actual Outcome
<!-- Filled in at review time: search.py --journal --update <id> --outcome "..." -->

## Reflection
<!-- How did the prediction compare to reality? What would you do differently? -->
"""
    path.write_text(content, encoding="utf-8")
    return str(path)


# ============ READ ============
def _field(text: str, name: str) -> str:
    m = re.search(r"^\s*-?\s*\*\*%s:\*\*\s*(.*)$" % re.escape(name), text, re.M)
    return m.group(1).strip() if m else ""


def parse_entry(path: Path) -> dict:
    """Metadata of an entry (works for entries written before review dates existed)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        text = ""
    title = re.search(r"^# Decision Journal:\s*(.+)$", text, re.M)
    meta = {"file": Path(path).name, "path": str(path), "decision": title.group(1).strip() if title else "",
            "date": _field(text, "Date"), "status": (_field(text, "Status") or "Created").split()[0],
            "review_by": _field(text, "Review by"), "confidence": "?"}
    confidence = _field(text, "Confidence")
    if confidence and not confidence.startswith("__"):
        meta["confidence"] = confidence.split()[0]
    else:
        legacy = re.search(r"## Confidence Level\n(?:<!--.*?-->\n)?\s*(\S+)", text)
        if legacy and not confidence:
            meta["confidence"] = legacy.group(1)
    outcome = _section(text.split("\n"), "Actual Outcome")
    if outcome and any(ln.strip() and not ln.strip().startswith("<!--")
                       for ln in text.split("\n")[outcome[0] + 1:outcome[1]]):
        meta["status"] = "Reviewed"
    return meta


def _date(text: str):
    try:
        return datetime.strptime(str(text)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def list_entries(output_dir: str = None) -> list:
    """All entries, newest decision date first (file time breaks ties and fills in missing dates)."""
    folder = journal_dir(output_dir)
    if not folder.is_dir():
        return []
    entries = []
    for path in folder.glob("*.md"):
        meta = parse_entry(path)
        when = _date(meta["date"]) or datetime.fromtimestamp(path.stat().st_mtime).date()
        entries.append((when, path.stat().st_mtime, meta))
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)
    return [meta for _, _, meta in entries]


def review_journals(output_dir: str = None, due: bool = False, today: date = None) -> str:
    """The entries as a numbered list; with due, only those past their review date and not yet reviewed."""
    today = today or date.today()
    entries = list_entries(output_dir)
    if not entries:
        return "No decision journal entries found. Create one with --journal."
    if due:
        entries = [e for e in entries if e["status"] != "Reviewed" and _date(e["review_by"])
                   and _date(e["review_by"]) <= today]
        entries.sort(key=lambda e: e["review_by"])
        if not entries:
            return "No decision journal entries are due for review."
        out = [f"=== DECISIONS DUE FOR REVIEW: {len(entries)} ===", ""]
    else:
        out = [f"=== DECISION JOURNAL: {len(entries)} {'entry' if len(entries) == 1 else 'entries'} ===", ""]
    for i, e in enumerate(entries, 1):
        review = e["review_by"] or "-"
        when = _date(e["review_by"])
        if when and e["status"] != "Reviewed" and when <= today:
            late = (today - when).days
            review += " (due today)" if late == 0 else f" (overdue {late} day{'s' if late != 1 else ''})"
        out.append(f"[{i}] {e['date']} | {e['decision']} | Confidence: {e['confidence']} | "
                   f"Review by: {review} | Status: {e['status']}")
        out.append(f"    File: {e['file']}")
    if due:
        out += ["", "Record what happened: search.py --journal --update <file> --outcome \"...\""]
    return "\n".join(out)


# ============ UPDATE ============
def find_entry(journal_id: str, output_dir: str = None) -> Path:
    """The one entry whose file name matches journal_id (exact name first, then a substring).

    Raises:
        JournalError: no journal folder, no match, or several matches.
    """
    folder = journal_dir(output_dir)
    if not folder.is_dir():
        raise JournalError(f"no {JOURNAL_DIR}/ folder in {folder.parent}; create an entry with --journal first")
    wanted = str(journal_id).strip()
    if wanted.endswith(".md"):
        wanted = wanted[:-3]
    if not wanted:
        raise JournalError("journal id is empty")
    files = sorted(folder.glob("*.md"))
    exact = [f for f in files if f.stem == wanted]
    if exact:
        return exact[0]
    keys = {wanted.lower(), slugify(wanted)}
    matches = [f for f in files if any(k and k in f.stem.lower() for k in keys)]
    if not matches:
        raise JournalError(f"no journal entry matches {journal_id!r} in {folder}")
    if len(matches) > 1:
        names = "\n".join(f"  - {m.name}" for m in matches)
        raise JournalError(f"{len(matches)} journal entries match {journal_id!r}; use more of the name:\n{names}")
    return matches[0]


def _section(lines: list, title: str):
    """(heading index, end index) of '## title' in lines, or None. The section ends at the next '## '."""
    for i, line in enumerate(lines):
        if line.strip() == f"## {title}":
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    return i, j
            return i, len(lines)
    return None


def _append_to_section(lines: list, title: str, block: list) -> list:
    """Add block at the end of a section (creating the section at the end if missing)."""
    found = _section(lines, title)
    if not found:
        while lines and not lines[-1].strip():
            lines.pop()
        return lines + ["", f"## {title}"] + block + [""]
    start, end = found
    insert = end
    while insert > start + 1 and not lines[insert - 1].strip():
        insert -= 1
    return lines[:insert] + block + ([""] if end < len(lines) else []) + lines[end:]


def update_journal(journal_id: str, outcome: str, output_dir: str = None, today: date = None) -> str:
    """Append the actual outcome and a reflection prompt to an entry; returns a summary.

    Nothing the user wrote is replaced: the outcome is added to 'Actual Outcome'
    and a dated review block to the end of 'Reflection'.

    Raises:
        JournalError: see find_entry; an empty outcome.
    """
    outcome = _safe(outcome)
    if not outcome:
        raise JournalError("--outcome is empty")
    path = find_entry(journal_id, output_dir)
    today = (today or date.today()).isoformat()
    meta = parse_entry(path)
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")

    for i, line in enumerate(lines):
        if re.match(r"^\s*-?\s*\*\*Status:\*\*", line):
            prefix = line[: line.index("**Status:**")]
            lines[i] = f"{prefix}**Status:** Reviewed {today}"
            break

    outcome_lines = outcome.split("\n")
    entry = [f"- **{today}:** {outcome_lines[0]}"] + [f"  {ln}" for ln in outcome_lines[1:]]
    lines = _append_to_section(lines, "Actual Outcome", entry)

    reflection = [
        f"### Review {today}",
        f"- **What happened:** {outcome_lines[0]}",
        f"- **Confidence at the time:** {meta['confidence']}",
        "- Was the hypothesis right? Why or why not?",
        "- Which signals did you miss, and which kill criteria fired?",
        "- Would a different framework have led to a better decision?",
        "- What will you do differently next time?",
    ]
    lines = _append_to_section(lines, "Reflection", reflection)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    return f"Updated: {path}\n\n" + "\n".join(reflection)
