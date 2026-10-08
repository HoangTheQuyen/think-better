#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Pro Search - BM25 search engine for structured problem-solving.
Usage: python search.py --stdin --plan [--type Diagnostic] [--category "Business Performance"] <<'THINK_BETTER_EOF_7f3a'
       <problem>                                # problem text on stdin, never parsed by the shell
       THINK_BETTER_EOF_7f3a
       python search.py "<problem>" --plan [--depth quick|standard|deep|executive] [-f ascii|markdown] [--json]
       python search.py "<problem>" --plan --persist [--step-docs] [-p "Project Name"] [-o dir] [--force]
       python search.py --status [-p name]       # progress of a saved workspace and the next step
       python search.py --done <step> -p name    # tick a step in the workspace (--undone reopens it)
       python search.py "<query>" [--domain <domain>] [-n 3] [--json]

Domains: steps, problem-types, decomposition, prioritization, analysis, biases,
         communication, heuristics, team

The --plan flag generates a problem-solving plan: it classifies the problem,
applies the reasoning rule for its context and searches every domain. Depth
changes what the plan contains.

The three skills share these spellings: -p/--project-name/--project, -n/--max-results/--results.
Exit codes: 0 ok, 1 no saved workspace (or a file error), 2 bad input (empty text, unknown value).
"""

import argparse
import io
import json
import sys
from pathlib import Path

from core import (CSV_CONFIG, MAX_RESULTS, search, problem_type_names, category_names, read_stdin_query,
                  default_output_dir, slugify)
from workspace import format_status, list_workspaces, mark, pick_workspace, workspace_status
from advisor import ProblemSolvingAdvisor, generate_solving_plan, load_steps, save_plan, VALID_DEPTHS

# Force UTF-8 for stdout/stderr to handle Unicode on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def positive_int(value):
    """argparse type: an integer >= 1."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be 1 or more, got {value}")
    return number


def format_output(result):
    """Format results for AI consumption (token-optimized)."""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    output.append(f"## Problem Solving Pro Search Results")
    output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 400:
                value_str = value_str[:400] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


def show_status(args) -> int:
    """--status / --done / --undone on a saved workspace."""
    base = args.output_dir or default_output_dir()
    name = slugify(args.project_name) if args.project_name else ""
    plan_dir = pick_workspace(base, args.query, name)
    if plan_dir is None:
        spaces = [d.name for d in list_workspaces(base)]
        if name and spaces:
            print(f"No workspace named {name!r}. Saved workspaces: {', '.join(spaces)}", file=sys.stderr)
        else:
            print("No saved workspace in solving-plans/. Create one with --plan --persist --step-docs -p <name>.",
                  file=sys.stderr)
        return 1
    note = sys.stderr if args.json else sys.stdout  # keep --json output parseable
    if args.done:
        print(f"Done: {mark(plan_dir, args.done, True)}\n", file=note)
    if args.undone:
        print(f"Reopened: {mark(plan_dir, args.undone, False)}\n", file=note)
    status = workspace_status(plan_dir)
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0
    others = [d.name for d in list_workspaces(base) if d != plan_dir]
    script = Path(__file__).resolve()
    try:
        script = script.relative_to(Path.cwd().resolve())
    except ValueError:
        pass
    steps = {s["number"]: s for s in load_steps()}
    print(format_status(status, steps, others, f"python3 {script.as_posix()}"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Problem Solving Pro Search")
    parser.add_argument("query", nargs="?", default="", help="Problem description or search query")
    parser.add_argument("--stdin", action="store_true",
                        help="Read the problem from stdin (safe for text with quotes, backticks or $)")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--max-results", "--results", "-n", dest="max_results", type=positive_int,
                        default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON (search results, the plan, or --status)")
    # Plan generation
    parser.add_argument("--plan", action="store_true", help="Generate comprehensive problem-solving plan")
    parser.add_argument("--project-name", "--project", "-p", dest="project_name", type=str, default=None,
                        help="Name for the saved plan / workspace")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format")
    # Persistence
    parser.add_argument("--persist", action="store_true", help="Save plan to solving-plans/ directory")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory for persisted files")
    # Depth
    parser.add_argument("--depth", choices=VALID_DEPTHS, default="standard",
                        help="quick: short scan; standard; deep: alternatives, more mental models and pitfalls; "
                             "executive: deep plus an executive summary, risks and the decision needed")
    # Step-by-step docs
    parser.add_argument("--step-docs", action="store_true", help="With --persist, create separate markdown files per step")
    parser.add_argument("--force", action="store_true", help="With --persist, replace files that already exist")
    # Classification overrides (the AI usually knows better than keyword matching)
    parser.add_argument("--type", "-t", dest="problem_type", default=None,
                        help="Problem type, skips auto-detection: " + ", ".join(problem_type_names()))
    parser.add_argument("--category", "-c", default=None,
                        help="Problem context, selects the reasoning rule: " + ", ".join(category_names()))
    # Resume
    parser.add_argument("--status", action="store_true",
                        help="Progress of a saved workspace (-p name, or the one the text matches, or the latest)")
    parser.add_argument("--done", metavar="STEP", help="Tick STEP (1-7 or a step name) in the workspace")
    parser.add_argument("--undone", metavar="STEP", help="Untick STEP in the workspace")

    args = parser.parse_args()
    if args.stdin:
        args.query = read_stdin_query()

    try:
        if args.status or args.done or args.undone:
            return show_status(args)

        if not args.query.strip():
            print("Error: describe the problem (as the query or on stdin with --stdin).", file=sys.stderr)
            return 2

        if args.plan:
            if args.json:
                plan = ProblemSolvingAdvisor().generate(args.query, args.project_name, args.depth,
                                                        args.problem_type, args.category)
                if args.persist:
                    plan["saved"] = save_plan(plan, args.output_dir, args.step_docs, args.force)
                print(json.dumps(plan, indent=2, ensure_ascii=False))
            else:
                print(generate_solving_plan(args.query, args.project_name, args.format, persist=args.persist,
                                            output_dir=args.output_dir, depth=args.depth, step_docs=args.step_docs,
                                            problem_type=args.problem_type, category=args.category,
                                            force=args.force))
            return 0

        result = search(args.query, args.domain, args.max_results)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_output(result))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
