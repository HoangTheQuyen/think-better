#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Pro Search - BM25 search engine for structured problem-solving.
Usage: python search.py "<query>" [--domain <domain>] [--max-results 3]
       python search.py "<query>" --plan [-p "Project Name"]
       python search.py "<query>" --plan --persist [-p "Project Name"]

Domains: steps, problem-types, decomposition, prioritization, analysis, biases,
         communication, heuristics, team

The --plan flag generates a comprehensive problem-solving plan by searching
across all domains and applying reasoning rules to recommend the best approach.
"""

import argparse
import sys
import io
from core import CSV_CONFIG, MAX_RESULTS, search
from advisor import generate_solving_plan

# Force UTF-8 for stdout/stderr to handle Unicode on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Problem Solving Pro Search")
    parser.add_argument("query", help="Problem description or search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Plan generation
    parser.add_argument("--plan", action="store_true", help="Generate comprehensive problem-solving plan")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name for plan output")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format")
    # Persistence
    parser.add_argument("--persist", action="store_true", help="Save plan to solving-plans/ directory")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory for persisted files")

    args = parser.parse_args()

    # Validate query is not empty
    if not args.query.strip():
        print("Error: Query is required. Describe the problem you want to solve.", file=sys.stderr)
        sys.exit(1)

    # Plan generation takes priority
    if args.plan:
        result = generate_solving_plan(
            args.query,
            args.project_name,
            args.format,
            persist=args.persist,
            output_dir=args.output_dir
        )
        print(result)

        if args.persist:
            project_slug = args.project_name.lower().replace(' ', '-') if args.project_name else "default"
            print("\n" + "=" * 60)
            print(f"  Plan persisted to solving-plans/{project_slug}/")
            print(f"    PLAN.md (Problem-Solving Plan)")
            print("=" * 60)
    # Domain search
    elif args.domain:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    # Auto-detect domain
    else:
        result = search(args.query, max_results=args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
