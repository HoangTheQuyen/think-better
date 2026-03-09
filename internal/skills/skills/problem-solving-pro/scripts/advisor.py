#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Pro Advisor - Generates comprehensive problem-solving plans
by aggregating multi-domain search results and applying reasoning rules.

Usage:
    from advisor import generate_solving_plan
    result = generate_solving_plan("revenue declining 20%", "Revenue Recovery")

    # With persistence
    result = generate_solving_plan("revenue declining 20%", "Revenue Recovery", persist=True)
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from core import search, DATA_DIR


# ============ CONFIGURATION ============
REASONING_FILE = "reasoning.csv"

SEARCH_CONFIG = {
    "problem-types": {"max_results": 1},
    "decomposition": {"max_results": 3},
    "analysis": {"max_results": 3},
    "prioritization": {"max_results": 2},
    "communication": {"max_results": 2},
    "heuristics": {"max_results": 3},
    "biases": {"max_results": 2},
    "team": {"max_results": 2},
    "steps": {"max_results": 7}
}


# ============ ADVISOR ENGINE ============
class ProblemSolvingAdvisor:
    """Generates problem-solving plans from aggregated knowledge base searches."""

    def __init__(self):
        self.reasoning_data = self._load_reasoning()

    def _load_reasoning(self) -> list:
        """Load reasoning rules from CSV."""
        filepath = DATA_DIR / REASONING_FILE
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _multi_domain_search(self, query: str, focus_domains: list = None) -> dict:
        """Execute searches across multiple domains."""
        results = {}
        for domain, config in SEARCH_CONFIG.items():
            if focus_domains and domain not in focus_domains:
                continue
            results[domain] = search(query, domain, config["max_results"])
        return results

    def _find_reasoning_rule(self, category: str) -> dict:
        """Find matching reasoning rule for a problem category."""
        category_lower = category.lower()

        # Try exact match first
        for rule in self.reasoning_data:
            if rule.get("Problem_Category", "").lower() == category_lower:
                return rule

        # Try partial match
        for rule in self.reasoning_data:
            cat = rule.get("Problem_Category", "").lower()
            if cat in category_lower or category_lower in cat:
                return rule

        # Try keyword match
        for rule in self.reasoning_data:
            cat = rule.get("Problem_Category", "").lower()
            keywords = cat.replace("/", " ").replace("-", " ").split()
            if any(kw in category_lower for kw in keywords if len(kw) > 3):
                return rule

        return {}

    def _apply_reasoning(self, category: str) -> dict:
        """Apply reasoning rules to identify best approach."""
        rule = self._find_reasoning_rule(category)

        if not rule:
            return {
                "steps_focus": "Define > Disaggregate > Prioritize > Analyze > Synthesize > Communicate",
                "decomposition_style": ["Issue Tree"],
                "analysis_priority": ["Benchmarking", "Root Cause Analysis"],
                "communication_style": ["Pyramid Principle"],
                "key_heuristics": ["First Principles", "Pareto 80/20"],
                "decision_rules": {},
                "anti_patterns": "",
                "severity": "MEDIUM"
            }

        # Parse decision rules JSON
        decision_rules = {}
        try:
            decision_rules = json.loads(rule.get("Decision_Rules", "{}"))
        except json.JSONDecodeError:
            pass

        return {
            "steps_focus": rule.get("Recommended_Steps_Focus", ""),
            "decomposition_style": [s.strip() for s in rule.get("Decomposition_Style", "").split("+")],
            "analysis_priority": [s.strip() for s in rule.get("Analysis_Priority", "").split("+")],
            "communication_style": [s.strip() for s in rule.get("Communication_Style", "").split("+")],
            "key_heuristics": [s.strip() for s in rule.get("Key_Heuristics", "").split(";")],
            "decision_rules": decision_rules,
            "anti_patterns": rule.get("Anti_Patterns", ""),
            "severity": rule.get("Severity", "MEDIUM")
        }

    def _select_best_match(self, results: list, priority_keywords: list) -> dict:
        """Select best matching result based on priority keywords."""
        if not results:
            return {}
        if not priority_keywords:
            return results[0]

        scored = []
        for result in results:
            result_str = str(result).lower()
            score = 0
            for kw in priority_keywords:
                kw_lower = kw.lower().strip()
                if kw_lower in result_str:
                    score += 1
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else results[0]

    def _extract_results(self, search_result: dict) -> list:
        """Extract results list from search result dict."""
        return search_result.get("results", [])

    def generate(self, query: str, project_name: str = None) -> dict:
        """Generate comprehensive problem-solving plan."""
        # Step 1: Classify the problem type
        type_result = search(query, "problem-types", 1)
        type_results = type_result.get("results", [])
        category = "General"
        problem_type_info = {}
        if type_results:
            category = type_results[0].get("Problem Type", "General")
            problem_type_info = type_results[0]

        # Step 2: Get reasoning rules for this category
        reasoning = self._apply_reasoning(category)

        # Step 3: Multi-domain search
        search_results = self._multi_domain_search(query)
        search_results["problem-types"] = type_result

        # Step 4: Select best matches per domain
        decomp_results = self._extract_results(search_results.get("decomposition", {}))
        analysis_results = self._extract_results(search_results.get("analysis", {}))
        prioritization_results = self._extract_results(search_results.get("prioritization", {}))
        comm_results = self._extract_results(search_results.get("communication", {}))
        heuristic_results = self._extract_results(search_results.get("heuristics", {}))
        bias_results = self._extract_results(search_results.get("biases", {}))
        team_results = self._extract_results(search_results.get("team", {}))
        steps_results = self._extract_results(search_results.get("steps", {}))

        best_decomp = self._select_best_match(decomp_results, reasoning.get("decomposition_style", []))
        best_analysis = self._select_best_match(analysis_results, reasoning.get("analysis_priority", []))
        best_prioritization = prioritization_results[0] if prioritization_results else {}
        best_comm = self._select_best_match(comm_results, reasoning.get("communication_style", []))

        return {
            "project_name": project_name or query.upper(),
            "problem_category": category,
            "problem_type": {
                "name": problem_type_info.get("Problem Type", category),
                "complexity": problem_type_info.get("Complexity", "Medium"),
                "characteristics": problem_type_info.get("Characteristics", ""),
                "recommended_approach": problem_type_info.get("Recommended Approach", ""),
                "time_frame": problem_type_info.get("Time Frame", ""),
                "team_size": problem_type_info.get("Team Size", "")
            },
            "methodology": {
                "steps_focus": reasoning.get("steps_focus", ""),
                "steps_detail": steps_results[:3]
            },
            "decomposition": {
                "primary": best_decomp.get("Framework", "Issue Tree"),
                "type": best_decomp.get("Type", ""),
                "structure": best_decomp.get("Structure Pattern", ""),
                "mece_test": best_decomp.get("MECE Test", ""),
                "alternatives": [r.get("Framework", "") for r in decomp_results[1:3]]
            },
            "prioritization": {
                "technique": best_prioritization.get("Technique", "Impact-Feasibility Matrix"),
                "how_to": best_prioritization.get("How to Apply", ""),
                "output": best_prioritization.get("Output Format", "")
            },
            "analysis": {
                "primary_tool": best_analysis.get("Tool", "Benchmarking"),
                "how_to": best_analysis.get("How to Apply", ""),
                "data_needed": best_analysis.get("Data Requirements", ""),
                "alternatives": [r.get("Tool", "") for r in analysis_results[1:3]]
            },
            "communication": {
                "pattern": best_comm.get("Pattern", "Pyramid Principle"),
                "structure": best_comm.get("Structure", ""),
                "audience": best_comm.get("Audience", "")
            },
            "mental_models": [
                {"name": h.get("Mental Model", ""), "application": h.get("Application to Problem Solving", "")}
                for h in heuristic_results[:3]
            ],
            "bias_warnings": [
                {"bias": b.get("Bias", ""), "debiasing": b.get("Debiasing Strategy", "")}
                for b in bias_results[:2]
            ],
            "team_recommendations": [
                {"pattern": t.get("Pattern", ""), "how": t.get("How to Facilitate", "")}
                for t in team_results[:2]
            ],
            "anti_patterns": reasoning.get("anti_patterns", ""),
            "decision_rules": reasoning.get("decision_rules", {}),
            "severity": reasoning.get("severity", "MEDIUM")
        }


# ============ OUTPUT FORMATTERS ============
BOX_WIDTH = 90

def format_ascii_box(plan: dict) -> str:
    """Format problem-solving plan as ASCII box."""
    project = plan.get("project_name", "PROJECT")
    problem = plan.get("problem_type", {})
    methodology = plan.get("methodology", {})
    decomp = plan.get("decomposition", {})
    prioritization = plan.get("prioritization", {})
    analysis = plan.get("analysis", {})
    comm = plan.get("communication", {})
    models = plan.get("mental_models", [])
    biases = plan.get("bias_warnings", [])
    team = plan.get("team_recommendations", [])
    anti_patterns = plan.get("anti_patterns", "")

    def wrap_text(text: str, prefix: str, width: int) -> list:
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = prefix
        for word in words:
            if len(current_line) + len(word) + 1 <= width - 2:
                current_line += (" " if current_line != prefix else "") + word
            else:
                if current_line != prefix:
                    lines.append(current_line)
                current_line = prefix + word
        if current_line != prefix:
            lines.append(current_line)
        return lines

    lines = []
    w = BOX_WIDTH - 1

    lines.append("+" + "=" * w + "+")
    lines.append(f"|  PROBLEM-SOLVING PLAN: {project}".ljust(BOX_WIDTH) + "|")
    lines.append("+" + "=" * w + "+")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Problem Classification
    lines.append(f"|  PROBLEM TYPE: {problem.get('name', '')}".ljust(BOX_WIDTH) + "|")
    lines.append(f"|     Complexity: {problem.get('complexity', '')}".ljust(BOX_WIDTH) + "|")
    if problem.get("time_frame"):
        lines.append(f"|     Time Frame: {problem.get('time_frame', '')}".ljust(BOX_WIDTH) + "|")
    if problem.get("team_size"):
        lines.append(f"|     Recommended Team: {problem.get('team_size', '')}".ljust(BOX_WIDTH) + "|")
    if problem.get("recommended_approach"):
        for line in wrap_text(f"Approach: {problem.get('recommended_approach', '')}", "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Methodology
    lines.append("|  RECOMMENDED PROCESS:".ljust(BOX_WIDTH) + "|")
    if methodology.get("steps_focus"):
        for line in wrap_text(methodology.get("steps_focus", ""), "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Decomposition
    lines.append(f"|  DECOMPOSITION: {decomp.get('primary', '')}".ljust(BOX_WIDTH) + "|")
    if decomp.get("structure"):
        for line in wrap_text(f"Structure: {decomp.get('structure', '')}", "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    if decomp.get("mece_test"):
        for line in wrap_text(f"MECE Test: {decomp.get('mece_test', '')}", "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    if decomp.get("alternatives"):
        alts = [a for a in decomp["alternatives"] if a]
        if alts:
            lines.append(f"|     Alternatives: {', '.join(alts)}".ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Prioritization
    lines.append(f"|  PRIORITIZATION: {prioritization.get('technique', '')}".ljust(BOX_WIDTH) + "|")
    if prioritization.get("how_to"):
        for line in wrap_text(prioritization.get("how_to", ""), "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Analysis
    lines.append(f"|  PRIMARY ANALYSIS: {analysis.get('primary_tool', '')}".ljust(BOX_WIDTH) + "|")
    if analysis.get("data_needed"):
        for line in wrap_text(f"Data Needed: {analysis.get('data_needed', '')}", "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    if analysis.get("alternatives"):
        alts = [a for a in analysis["alternatives"] if a]
        if alts:
            lines.append(f"|     Also Consider: {', '.join(alts)}".ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Communication
    lines.append(f"|  COMMUNICATION: {comm.get('pattern', '')}".ljust(BOX_WIDTH) + "|")
    if comm.get("structure"):
        for line in wrap_text(f"Structure: {comm.get('structure', '')}", "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
    if comm.get("audience"):
        lines.append(f"|     Audience: {comm.get('audience', '')}".ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    # Mental Models
    if models:
        lines.append("|  KEY MENTAL MODELS:".ljust(BOX_WIDTH) + "|")
        for m in models:
            if m.get("name"):
                lines.append(f"|     - {m['name']}".ljust(BOX_WIDTH) + "|")
        lines.append("|" + " " * BOX_WIDTH + "|")

    # Bias Warnings
    if biases:
        lines.append("|  BIAS WARNINGS:".ljust(BOX_WIDTH) + "|")
        for b in biases:
            if b.get("bias"):
                lines.append(f"|     ! {b['bias']}".ljust(BOX_WIDTH) + "|")
                if b.get("debiasing"):
                    for line in wrap_text(f"  Remedy: {b['debiasing']}", "|       ", BOX_WIDTH):
                        lines.append(line.ljust(BOX_WIDTH) + "|")
        lines.append("|" + " " * BOX_WIDTH + "|")

    # Anti-patterns
    if anti_patterns:
        lines.append("|  AVOID (Anti-patterns):".ljust(BOX_WIDTH) + "|")
        for line in wrap_text(anti_patterns, "|     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "|")
        lines.append("|" + " " * BOX_WIDTH + "|")

    # Checklist
    lines.append("|  PROBLEM-SOLVING CHECKLIST:".ljust(BOX_WIDTH) + "|")
    checklist_items = [
        "[ ] Problem statement is specific, bounded, and measurable",
        "[ ] Logic tree is MECE (Mutually Exclusive, Collectively Exhaustive)",
        "[ ] Top 2-3 priority issues identified (80/20 applied)",
        "[ ] Each priority issue has a testable hypothesis",
        "[ ] Analyses are linked to specific hypotheses",
        "[ ] Day 1 answer stated with confidence level",
        "[ ] Findings pass the 'so what?' test",
        "[ ] Recommendation leads the communication (answer first)",
        "[ ] Counterarguments addressed directly",
        "[ ] Next steps are specific with owners and dates"
    ]
    for item in checklist_items:
        lines.append(f"|     {item}".ljust(BOX_WIDTH) + "|")
    lines.append("|" + " " * BOX_WIDTH + "|")

    lines.append("+" + "=" * w + "+")

    return "\n".join(lines)


def format_markdown(plan: dict) -> str:
    """Format problem-solving plan as markdown."""
    project = plan.get("project_name", "PROJECT")
    problem = plan.get("problem_type", {})
    methodology = plan.get("methodology", {})
    decomp = plan.get("decomposition", {})
    prioritization = plan.get("prioritization", {})
    analysis = plan.get("analysis", {})
    comm = plan.get("communication", {})
    models = plan.get("mental_models", [])
    biases = plan.get("bias_warnings", [])
    team = plan.get("team_recommendations", [])
    anti_patterns = plan.get("anti_patterns", "")

    lines = []
    lines.append(f"## Problem-Solving Plan: {project}")
    lines.append("")

    lines.append("### Problem Classification")
    lines.append(f"- **Type:** {problem.get('name', '')}")
    lines.append(f"- **Complexity:** {problem.get('complexity', '')}")
    if problem.get("time_frame"):
        lines.append(f"- **Time Frame:** {problem.get('time_frame', '')}")
    if problem.get("team_size"):
        lines.append(f"- **Recommended Team:** {problem.get('team_size', '')}")
    if problem.get("recommended_approach"):
        lines.append(f"- **Approach:** {problem.get('recommended_approach', '')}")
    lines.append("")

    lines.append("### Recommended Process")
    if methodology.get("steps_focus"):
        lines.append(f"{methodology['steps_focus']}")
    lines.append("")

    lines.append("### Decomposition Framework")
    lines.append(f"- **Primary:** {decomp.get('primary', '')}")
    if decomp.get("structure"):
        lines.append(f"- **Structure:** {decomp.get('structure', '')}")
    if decomp.get("mece_test"):
        lines.append(f"- **MECE Test:** {decomp.get('mece_test', '')}")
    if decomp.get("alternatives"):
        alts = [a for a in decomp["alternatives"] if a]
        if alts:
            lines.append(f"- **Alternatives:** {', '.join(alts)}")
    lines.append("")

    lines.append("### Prioritization")
    lines.append(f"- **Technique:** {prioritization.get('technique', '')}")
    if prioritization.get("how_to"):
        lines.append(f"- **How:** {prioritization.get('how_to', '')}")
    lines.append("")

    lines.append("### Analysis Toolkit")
    lines.append(f"- **Primary:** {analysis.get('primary_tool', '')}")
    if analysis.get("data_needed"):
        lines.append(f"- **Data Needed:** {analysis.get('data_needed', '')}")
    if analysis.get("alternatives"):
        alts = [a for a in analysis["alternatives"] if a]
        if alts:
            lines.append(f"- **Also Consider:** {', '.join(alts)}")
    lines.append("")

    lines.append("### Communication Strategy")
    lines.append(f"- **Pattern:** {comm.get('pattern', '')}")
    if comm.get("structure"):
        lines.append(f"- **Structure:** {comm.get('structure', '')}")
    if comm.get("audience"):
        lines.append(f"- **Audience:** {comm.get('audience', '')}")
    lines.append("")

    if models:
        lines.append("### Key Mental Models")
        for m in models:
            if m.get("name"):
                lines.append(f"- **{m['name']}**: {m.get('application', '')}")
        lines.append("")

    if biases:
        lines.append("### Bias Warnings")
        for b in biases:
            if b.get("bias"):
                lines.append(f"- **{b['bias']}**: {b.get('debiasing', '')}")
        lines.append("")

    if team:
        lines.append("### Team Recommendations")
        for t in team:
            if t.get("pattern"):
                lines.append(f"- **{t['pattern']}**: {t.get('how', '')}")
        lines.append("")

    if anti_patterns:
        lines.append("### Avoid (Anti-patterns)")
        lines.append(f"{anti_patterns}")
        lines.append("")

    lines.append("### Problem-Solving Checklist")
    checklist = [
        "Problem statement is specific, bounded, and measurable",
        "Logic tree is MECE",
        "Top 2-3 priority issues identified (80/20 applied)",
        "Each priority issue has a testable hypothesis",
        "Analyses linked to specific hypotheses",
        "Day 1 answer stated with confidence level",
        "Findings pass the 'so what?' test",
        "Recommendation leads the communication",
        "Counterarguments addressed",
        "Next steps specific with owners and dates"
    ]
    for item in checklist:
        lines.append(f"- [ ] {item}")
    lines.append("")

    return "\n".join(lines)


def persist_plan(plan: dict, output_dir: str = None):
    """Save problem-solving plan to file."""
    project_slug = plan.get("project_name", "default").lower().replace(" ", "-")
    base_dir = Path(output_dir) if output_dir else Path.cwd()
    plan_dir = base_dir / "solving-plans" / project_slug

    plan_dir.mkdir(parents=True, exist_ok=True)

    # Write plan
    plan_path = plan_dir / "PLAN.md"
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(format_markdown(plan))
        f.write(f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    return str(plan_path)


# ============ PUBLIC API ============
def generate_solving_plan(query: str, project_name: str = None, output_format: str = "ascii",
                          persist: bool = False, output_dir: str = None) -> str:
    """Generate a comprehensive problem-solving plan.

    Args:
        query: Problem description
        project_name: Optional project name
        output_format: 'ascii' or 'markdown'
        persist: Whether to save to file
        output_dir: Output directory for persistence

    Returns:
        Formatted problem-solving plan
    """
    advisor = ProblemSolvingAdvisor()
    plan = advisor.generate(query, project_name)

    if output_format == "markdown":
        result = format_markdown(plan)
    else:
        result = format_ascii_box(plan)

    if persist:
        path = persist_plan(plan, output_dir)
        result += f"\n\nPlan saved to: {path}"

    return result
