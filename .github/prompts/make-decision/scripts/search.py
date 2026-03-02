#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Search - CLI for decision-making knowledge base.

Usage:
    python search.py "<query>" --plan [-p "Project"] [-f ascii|markdown] [--persist]
    python search.py "<query>" --domain <domain> [-n 3]
    python search.py "<query>" [-n 3]
    python search.py --journal "<decision_statement>" [-p "Project"]
    python search.py --journal --review
    python search.py --journal --update "<id>" --outcome "<text>"
    python search.py --matrix "<options>" [-c "criteria1,criteria2,..."]

Domains: frameworks, types, biases, analysis, criteria, facilitation
"""

import argparse
import sys
import io
from core import CSV_CONFIG, MAX_RESULTS, search, search_domain, DOMAIN_KEYWORDS
from advisor import DecisionAdvisor, generate_decision_plan

# Force UTF-8 for stdout/stderr on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


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
        # Get first value as primary identifier
        first_key = list(row.keys())[0]
        first_val = row[first_key]

        # Get category if present
        cat = row.get("Category", row.get("_domain", ""))
        cat_str = f" ({cat})" if cat else ""

        output.append(f"[{i}] {first_val}{cat_str}")

        for key, value in row.items():
            if key == first_key or key == "_domain":
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
    all_keywords = DOMAIN_KEYWORDS if not domain else {domain: DOMAIN_KEYWORDS.get(domain, [])}

    for d, keywords in all_keywords.items():
        for kw in keywords:
            # Suggest keywords that share some words with the query
            query_words = set(query.lower().split())
            kw_words = set(kw.lower().split())
            if query_words & kw_words:
                suggestions.add(kw)
            elif any(qw[:4] in kw for qw in query_words if len(qw) >= 4):
                suggestions.add(kw)

    return list(suggestions)[:5]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make-Decision: Decision-making knowledge base search and plan generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="Decision description or search query")

    # Plan generation
    parser.add_argument("--plan", action="store_true", help="Generate comprehensive decision-making plan")
    parser.add_argument("--project", "-p", type=str, default=None, help="Project name for output")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format (default: ascii)")
    parser.add_argument("--persist", action="store_true", help="Save plan to decision-plans/ directory")

    # Domain search
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search specific domain")
    parser.add_argument("--results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")

    # Decision journal
    parser.add_argument("--journal", nargs="?", const=True, default=None, help="Decision journal: create entry or use with --review/--update")
    parser.add_argument("--review", action="store_true", help="Review past decision journal entries")
    parser.add_argument("--update", type=str, default=None, help="Update journal entry by ID")
    parser.add_argument("--outcome", type=str, default=None, help="Actual outcome text for journal update")

    # Comparison matrix
    parser.add_argument("--matrix", type=str, default=None, help="Generate comparison matrix for options")
    parser.add_argument("--criteria", "-c", type=str, default=None, help="Custom criteria (comma-separated)")

    # JSON output
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    advisor = DecisionAdvisor(args.query or "")

    try:
        # === PLAN GENERATION ===
        if args.plan:
            if not args.query:
                print("Error: Query is required for --plan. Describe the decision.", file=sys.stderr)
                sys.exit(1)
            result = generate_decision_plan(
                args.query,
                args.project,
                args.format,
                persist=args.persist,
            )
            print(result)
            if args.persist:
                slug = (args.project or args.query[:30]).lower().replace(" ", "-")
                print(f"\n{'=' * 60}")
                print(f"  Plan persisted to decision-plans/{slug}/")
                print(f"    PLAN.md (Decision-Making Plan)")
                print(f"{'=' * 60}")

        # === JOURNAL ===
        elif args.journal is not None:
            # --journal --review
            if args.review:
                print(advisor.review_journals())

            # --journal --update "<id>" --outcome "<text>"
            elif args.update:
                if not args.outcome:
                    print("Error: --outcome is required with --update.", file=sys.stderr)
                    sys.exit(1)
                result = advisor.update_journal(args.update, args.outcome)
                print(result)

            # --journal "<decision_statement>"
            else:
                statement = args.journal if isinstance(args.journal, str) and args.journal is not True else args.query
                if not statement or statement is True:
                    print("Error: Decision statement required. Use: --journal \"statement\" or provide a query.", file=sys.stderr)
                    sys.exit(1)
                path = advisor.create_journal(statement, args.project)
                print(f"Decision journal created: {path}")

        # === MATRIX ===
        elif args.matrix:
            result = advisor.generate_matrix(args.matrix, args.criteria)
            print(result)

        # === DOMAIN SEARCH ===
        elif args.domain:
            if not args.query:
                print("Error: Query is required for domain search.", file=sys.stderr)
                sys.exit(1)
            result = search_domain(args.query, args.domain, args.results)
            if args.json:
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_domain_output(result))

        # === AUTO-DOMAIN SEARCH ===
        elif args.query:
            result = search(args.query, max_results=args.results)
            if args.json:
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_domain_output(result))

        # === NO INPUT ===
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
