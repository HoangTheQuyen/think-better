#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving - structured plans for coding tasks.

Usage:
    python3 search.py "<task>" --plan [--type debug] [--depth quick|standard|deep|executive] [-f markdown|ascii]
    python3 search.py "<task>" --plan --persist [--step-docs] [-p "name"] [-o dir]
    python3 search.py --detect                      # the project's own test/lint/build commands
    python3 search.py "<keywords>" [--domain <domain>] [-n 3] [--json]

Task types: debug, feature, refactor, performance, flaky-test, incident, migration, review
Domains:    steps, task-types, debugging, changes, testing, principles, biases, review, artifacts
"""

import argparse
import io
import json
import sys

from core import CSV_CONFIG, MAX_RESULTS, detect_project_commands, search, task_type_names
from advisor import CodeSolvingAdvisor, VALID_DEPTHS, generate_code_plan

# Force UTF-8 output (Windows consoles default to a legacy code page)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def format_results(result: dict) -> str:
    out = [f"## Code Solving: {result['domain']}",
           f"**Query:** {result['query']} | **Found:** {result['count']}", ""]
    for i, row in enumerate(result["results"], 1):
        out.append(f"### {i}. {next(iter(row.values()))}")
        for key, value in list(row.items())[1:]:
            out.append(f"- **{key}:** {value}")
        out.append("")
    if not result["results"]:
        out.append("No matches. Try other keywords or another --domain.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Code Solving: 7-step plans with evidence gates for coding tasks")
    parser.add_argument("query", nargs="?", default="", help="Task description or search keywords")
    parser.add_argument("--plan", action="store_true", help="Generate a step-by-step plan")
    parser.add_argument("--type", "-t", dest="task_type", default=None,
                        help="Task type, skips auto-detection: " + ", ".join(task_type_names()))
    parser.add_argument("--depth", choices=VALID_DEPTHS, default="standard", help="Plan depth (default: standard)")
    parser.add_argument("--format", "-f", choices=["markdown", "ascii"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--persist", action="store_true", help="Save the plan under coding-plans/")
    parser.add_argument("--step-docs", action="store_true", help="With --persist, write one file per step")
    parser.add_argument("--project-name", "-p", default=None, help="Name for the saved plan")
    parser.add_argument("--output-dir", "-o", default=None, help="Where to save (default: project root)")
    parser.add_argument("--project-dir", default=None, help="Project to inspect for commands (default: project root)")
    parser.add_argument("--detect", action="store_true", help="List the project's test/lint/build commands")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG), help="Search one knowledge domain")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max search results")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    try:
        if args.detect:
            commands = detect_project_commands(args.project_dir)
            if args.json:
                print(json.dumps([{"purpose": p, "command": c, "source": s} for p, c, s in commands], indent=2))
            elif commands:
                for purpose, command, source in commands:
                    print(f"{purpose:10} {command:32} ({source})")
            else:
                print("No test/lint/build configuration detected.")
            return 0

        if not args.query.strip():
            parser.print_help()
            return 1

        if args.plan:
            if args.json:
                plan = CodeSolvingAdvisor().generate(args.query, args.project_name, args.depth,
                                                     args.task_type, args.project_dir)
                print(json.dumps(plan, indent=2, ensure_ascii=False))
            else:
                print(generate_code_plan(args.query, args.project_name, args.format, args.persist,
                                         args.output_dir, args.depth, args.step_docs,
                                         args.task_type, args.project_dir))
            return 0

        result = search(args.query, args.domain, args.max_results)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_results(result))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
