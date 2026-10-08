#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Search - CLI for the decision-making knowledge base.

Usage:
    python search.py --stdin --plan [--type "Binary Choice"] [--depth quick|standard|deep|executive] <<'TASK'
    <decision, exactly as the user wrote it>
    TASK
    python search.py --stdin --plan --persist [--step-docs] [-p "name"] [-o dir] [--force] <<'TASK' ...
    python search.py --stdin --plan --json <<'TASK' ...          # the plan as JSON
    python search.py --status [-p name]                          # progress of a saved workspace
    python search.py --done <step> -p name                       # tick a step (1-6 or its name)
    python search.py --stdin --matrix [-c "Cost:3,Speed:2"] [--scores "A:4,3;B:5,2"] [-f markdown] <<'TASK'
    <the options, e.g. React vs Vue>
    TASK
    python search.py --stdin --journal [--confidence 70] [--review-in 14d] [--options "A, B"] <<'TASK'
    <decision statement>
    TASK
    python search.py --journal --review [--due]
    python search.py --journal --update "<id>" --outcome "<text>"   (or the outcome on stdin with --stdin)
    python search.py "<keywords>" [--domain <domain>] [-n 3] [--json]

Domains: frameworks, types, biases, analysis, criteria, facilitation
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

from core import CSV_CONFIG, DOMAIN_KEYWORDS, MAX_RESULTS, default_output_dir, read_stdin_query, search, \
    search_domain, slugify
from advisor import DecisionAdvisor, VALID_DEPTHS, build_matrix, format_matrix, generate_decision_plan
import journal
from workspace import format_status, list_workspaces, mark, pick_workspace, workspace_status

# Force UTF-8 for stdout/stderr on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def positive_int(value):
    """argparse type: an integer >= 1."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be 1 or more, got {value}")
    return number


def percent(value):
    """argparse type: 0-100, a trailing % allowed."""
    try:
        number = int(str(value).strip().rstrip("%"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be a number from 0 to 100, got {value}") from None
    if not 0 <= number <= 100:
        raise argparse.ArgumentTypeError(f"must be from 0 to 100, got {value}")
    return number


def duration(value):
    """argparse type: 14d, 2w, 3m, 1y or a number of days."""
    try:
        return journal.parse_duration(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None


def format_domain_output(result):
    """Format domain search results for display."""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    domain = result.get("domain", "auto")
    query = result.get("query", "")
    count = result.get("count", 0)

    if domain == "auto":
        detected = result.get("detected_domains", [])
        output.append(f"=== AUTO-SEARCH | Query: \"{query}\" | Domains: {', '.join(detected)} | Results: {count} ===")
    else:
        output.append(f"=== DOMAIN: {domain} | Query: \"{query}\" | Results: {count} ===")
    output.append("")

    if count == 0:
        output.append("No results found.")
        suggestions = _suggest_terms(query, domain)
        if suggestions:
            output.append(f"Try: {', '.join(suggestions)}")
        return "\n".join(output)

    for i, row in enumerate(result["results"], 1):
        first_key = list(row.keys())[0]
        cat = row.get("Category", row.get("_domain", ""))
        output.append(f"[{i}] {row[first_key]}{f' ({cat})' if cat else ''}")
        for key, value in row.items():
            if key in (first_key, "_domain"):
                continue
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"    {key}: {value_str}")
        output.append("")
    return "\n".join(output)


def _suggest_terms(query, domain=None):
    """Suggest alternative search terms when no results found."""
    suggestions = set()
    all_keywords = DOMAIN_KEYWORDS if not domain or domain == "auto" else {domain: DOMAIN_KEYWORDS.get(domain, [])}
    query_words = set(query.lower().split())
    for keywords in all_keywords.values():
        for kw in keywords:
            if query_words & set(kw.lower().split()) or any(qw[:4] in kw for qw in query_words if len(qw) >= 4):
                suggestions.add(kw)
    return sorted(suggestions)[:5]


def _script_command() -> str:
    script = Path(__file__).resolve()
    try:
        script = script.relative_to(Path.cwd().resolve())
    except ValueError:
        pass
    return f"python3 {script.as_posix()}"


def show_status(args) -> int:
    """--status / --done / --undone on a saved decision workspace."""
    base = args.output_dir or default_output_dir()
    name = slugify(args.project) if args.project else ""
    plan_dir = pick_workspace(base, args.query, name)
    if plan_dir is None:
        spaces = [d.name for d in list_workspaces(base)]
        if name and spaces:
            print(f"No workspace named {name!r}. Saved workspaces: {', '.join(spaces)}", file=sys.stderr)
        else:
            print("No saved workspace in decision-plans/. Create one with --plan --persist --step-docs -p <name>.",
                  file=sys.stderr)
        return 1
    if args.done:
        print(f"Done: {mark(plan_dir, args.done, True)}\n")
    if args.undone:
        print(f"Reopened: {mark(plan_dir, args.undone, False)}\n")
    status = workspace_status(plan_dir)
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        others = [d.name for d in list_workspaces(base) if d != plan_dir]
        print(format_status(status, others, _script_command()))
    return 0


def run_journal(args) -> int:
    if args.review:
        if args.json:
            entries = journal.list_entries(args.output_dir)
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            print(journal.review_journals(args.output_dir, due=args.due))
        return 0
    if args.update:
        outcome = args.outcome if args.outcome is not None else (args.query if args.stdin else "")
        if not str(outcome).strip():
            print("Error: --outcome is required with --update (or pass the outcome on stdin with --stdin).",
                  file=sys.stderr)
            return 1
        print(journal.update_journal(args.update, outcome, args.output_dir))
        return 0
    statement = args.journal if isinstance(args.journal, str) else args.query
    if not str(statement or "").strip():
        print("Error: decision statement required. Use: --journal \"statement\" or --stdin --journal.",
              file=sys.stderr)
        return 1
    options = [o.strip() for o in re.split(r"[,;\n]", args.options) if o.strip()] if args.options else None
    path = DecisionAdvisor().create_journal(statement, args.project, args.output_dir, options=options,
                                            framework=args.framework, confidence=args.confidence,
                                            review_days=args.review_in)
    print(f"Decision journal created: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Make-Decision: decision plans, weighted matrices, workspaces and a decision journal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="Decision description or search keywords")
    parser.add_argument("--stdin", action="store_true",
                        help="Read the decision (or matrix options, journal statement, outcome) from stdin; "
                             "safe for text with quotes, backticks or $")

    # Plan generation
    parser.add_argument("--plan", action="store_true", help="Generate a decision-making plan")
    parser.add_argument("--project", "-p", type=str, default=None, help="Project / workspace name")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii",
                        help="Output format for --plan and --matrix (default: ascii)")
    parser.add_argument("--persist", action="store_true", help="Save the plan under decision-plans/")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Where plans, workspaces and journals go (default: project root)")
    parser.add_argument("--depth", choices=VALID_DEPTHS, default="standard",
                        help="quick (essentials), standard, deep (pre-mortem, sensitivity, information to gather) "
                             "or executive (recommendation-first brief) (default: standard)")
    parser.add_argument("--step-docs", action="store_true", help="With --persist, one markdown file per step")
    parser.add_argument("--force", action="store_true", help="With --persist, replace files that already exist")
    parser.add_argument("--type", "-t", dest="decision_type", default=None,
                        help="Decision type, skips auto-detection: " + ", ".join(DecisionAdvisor.decision_type_names()))

    # Workspace progress
    parser.add_argument("--status", action="store_true",
                        help="Progress of a saved workspace (-p name, or the one the text matches, or the latest)")
    parser.add_argument("--done", metavar="STEP", help="Mark STEP (1-6 or a step name) done in the workspace")
    parser.add_argument("--undone", metavar="STEP", help="Reopen STEP in the workspace")

    # Domain search
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search one knowledge domain")
    parser.add_argument("--results", "-n", type=positive_int, default=MAX_RESULTS, help="Max results (default: 3)")

    # Decision journal
    parser.add_argument("--journal", nargs="?", const=True, default=None,
                        help="Create a journal entry (statement as value, as the query or on stdin); "
                             "with --review or --update, manage entries")
    parser.add_argument("--review", action="store_true", help="List journal entries, newest first")
    parser.add_argument("--due", action="store_true", help="With --review, only entries past their review date")
    parser.add_argument("--update", type=str, default=None, help="Journal entry to update (part of its file name)")
    parser.add_argument("--outcome", type=str, default=None, help="What actually happened, for --update")
    parser.add_argument("--confidence", type=percent, default=None, help="Your confidence in the decision, 0-100")
    parser.add_argument("--framework", type=str, default=None,
                        help="Framework you applied (default: the one recommended for the decision)")
    parser.add_argument("--options", type=str, default=None, help="Options you considered, comma-separated")
    parser.add_argument("--review-in", type=duration, default=journal.DEFAULT_REVIEW_DAYS,
                        help="When to review the decision: 14d, 2w, 3m (default: 30d)")

    # Comparison matrix
    parser.add_argument("--matrix", nargs="?", const="", default=None,
                        help="Comparison matrix for the options (as value, as the query or on stdin)")
    parser.add_argument("--criteria", "-c", type=str, default=None,
                        help="Criteria with optional weights: \"Cost:3,Speed:2,Risk:1\"")
    parser.add_argument("--scores", type=str, default=None,
                        help="Scores per option, one per criterion: \"React:4,3,5;Vue:5,4,3\"")

    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    if args.stdin:
        args.query = read_stdin_query()

    try:
        if args.status or args.done or args.undone:
            return show_status(args)

        if args.plan:
            if not args.query.strip():
                print("Error: describe the decision for --plan (as the query or on stdin with --stdin).",
                      file=sys.stderr)
                return 1
            print(generate_decision_plan(args.query, args.project, "json" if args.json else args.format,
                                         persist=args.persist, output_dir=args.output_dir, depth=args.depth,
                                         step_docs=args.step_docs, decision_type=args.decision_type,
                                         force=args.force))
            return 0

        if args.journal is not None or args.review or args.update:
            return run_journal(args)

        if args.matrix is not None:
            description = args.matrix if args.matrix.strip() else args.query
            if not description.strip() and not args.scores:
                print("Error: give the options for --matrix (\"A vs B\", as the query or on stdin).",
                      file=sys.stderr)
                return 1
            matrix = build_matrix(description, args.criteria, args.scores)
            if args.json:
                print(json.dumps(matrix, indent=2, ensure_ascii=False))
            else:
                print(format_matrix(matrix, args.format))
            return 0

        if args.domain:
            if not args.query.strip():
                print("Error: Query is required for domain search.", file=sys.stderr)
                return 1
            result = search_domain(args.query, args.domain, args.results)
        elif args.query.strip():
            result = search(args.query, max_results=args.results)
        else:
            parser.print_help()
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_domain_output(result))
        return 0

    except (ValueError, OSError) as e:  # ValueError includes journal.JournalError
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
