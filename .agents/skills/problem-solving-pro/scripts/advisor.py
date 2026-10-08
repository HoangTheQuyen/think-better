#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Pro Advisor - Generates problem-solving plans by combining the
problem type, the reasoning rule for the business context, and multi-domain search.

Usage:
    from advisor import generate_solving_plan
    result = generate_solving_plan("revenue declining 20%", "Revenue Recovery")

    # With persistence
    result = generate_solving_plan("revenue declining 20%", "Revenue Recovery", persist=True)
"""

import json
import unicodedata
from datetime import datetime
from pathlib import Path
from core import (
    search, load_reasoning, classify_category, classify_problem_type, problem_type_names, category_names,
    resolve_choice, slugify, default_output_dir, save_docs, find_record, split_names, _load_csv,
    pad_display, wrap_display, DATA_DIR, CSV_CONFIG,
)
from workspace import prepare_folder, progress_table, record_state


# ============ CONFIGURATION ============
SEARCH_CONFIG = {
    "decomposition": {"max_results": 3},
    "analysis": {"max_results": 3},
    "prioritization": {"max_results": 2},
    "communication": {"max_results": 2},
    "heuristics": {"max_results": 3},
    "biases": {"max_results": 2},
    "team": {"max_results": 2},
}

# What each depth shows. quick is a one-screen scan; deep adds alternatives, more
# mental models and biases, pitfalls per step; executive adds an executive summary
# (SCR), key risks and the decision needed on top of deep.
DEPTH_CONFIG = {
    "quick": {"multiplier": 0.5, "alternatives": 0, "models": 2, "biases": 2, "team": 0,
              "steps": False, "details": False, "checklist": False, "executive": False},
    "standard": {"multiplier": 1.0, "alternatives": 2, "models": 3, "biases": 3, "team": 2,
                 "steps": True, "details": False, "checklist": True, "executive": False},
    "deep": {"multiplier": 1.7, "alternatives": 4, "models": 5, "biases": 4, "team": 3,
             "steps": True, "details": True, "checklist": True, "executive": False},
    "executive": {"multiplier": 2.5, "alternatives": 4, "models": 5, "biases": 4, "team": 3,
                  "steps": True, "details": True, "checklist": True, "executive": True},
}

VALID_DEPTHS = list(DEPTH_CONFIG.keys())

DEFAULT_RULE = {
    "steps_focus": "Define > Disaggregate > Prioritize > Analyze > Synthesize > Communicate",
    "decomposition_style": ["Issue Tree"],
    "analysis_priority": ["Benchmarking", "Root Cause Analysis"],
    "communication_style": ["Pyramid Principle"],
    "key_heuristics": ["First Principles Thinking", "Pareto Principle"],
    "key_biases": ["Confirmation Bias", "Anchoring"],
    "decision_rules": {},
    "anti_patterns": "",
    "severity": "MEDIUM",
}
DEFAULT_TEAM = ["Hypothesis-Driven Teamwork", "Red Team / Devils Advocate", "Progress Sharing (Frequent Checkpoints)"]
REQUEST_PREVIEW = 600


def _short_name(text: str, limit: int = 60) -> str:
    """First `limit` characters of text, cut at a word boundary."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut or text[:limit]


def _preview(text: str, limit: int = REQUEST_PREVIEW) -> str:
    """The request on one line, shortened for display (the full text is kept in saved files)."""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else _short_name(text, limit) + " …"


def load_steps() -> list:
    """The 7 steps in order, as dicts."""
    rows = _load_csv(DATA_DIR / CSV_CONFIG["steps"]["file"])
    return [{
        "number": i, "name": r.get("Step", ""), "phase": r.get("Phase", ""),
        "description": r.get("Description", ""), "activities": r.get("Key Activities", ""),
        "pitfalls": r.get("Common Pitfalls", ""), "outputs": r.get("Output Artifacts", ""),
        "time": r.get("Time Allocation", ""), "gate": r.get("Quality Gate", ""), "tips": r.get("Tips", ""),
    } for i, r in enumerate(rows, 1)]


def _interleave(*lists) -> list:
    """[a1, b1, a2, b2, ...] without duplicates."""
    out = []
    for i in range(max((len(x) for x in lists), default=0)):
        for x in lists:
            if i < len(x) and x[i] not in out:
                out.append(x[i])
    return out


# ============ ADVISOR ENGINE ============
class ProblemSolvingAdvisor:
    """Generates problem-solving plans from aggregated knowledge base searches."""

    def __init__(self):
        self.reasoning_data = load_reasoning()

    def _multi_domain_search(self, query: str, depth: str = "standard") -> dict:
        """Execute searches across multiple domains, scaled by depth."""
        multiplier = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])["multiplier"]
        return {domain: search(query, domain, max(1, int(config["max_results"] * multiplier)))
                for domain, config in SEARCH_CONFIG.items()}

    def _find_reasoning_rule(self, category: str) -> dict:
        """Find the reasoning rule for a problem category (exact, then partial match)."""
        category_lower = category.lower()
        for rule in self.reasoning_data:
            if rule.get("Problem_Category", "").lower() == category_lower:
                return rule
        for rule in self.reasoning_data:
            cat = rule.get("Problem_Category", "").lower()
            if cat in category_lower or category_lower in cat:
                return rule
        for rule in self.reasoning_data:
            keywords = rule.get("Problem_Category", "").lower().replace("/", " ").replace("-", " ").split()
            if any(kw in category_lower for kw in keywords if len(kw) > 3):
                return rule
        return {}

    def _apply_reasoning(self, category: str) -> dict:
        """The reasoning rule for the category, parsed; generic defaults when there is none."""
        rule = self._find_reasoning_rule(category) if category else {}
        if not rule:
            return dict(DEFAULT_RULE)
        try:
            decision_rules = json.loads(rule.get("Decision_Rules", "") or "{}")
        except json.JSONDecodeError:
            decision_rules = {}
        return {
            "steps_focus": rule.get("Recommended_Steps_Focus", ""),
            "decomposition_style": split_names(rule.get("Decomposition_Style", "")),
            "analysis_priority": split_names(rule.get("Analysis_Priority", "")),
            "communication_style": split_names(rule.get("Communication_Style", "")),
            "key_heuristics": split_names(rule.get("Key_Heuristics", "")),
            "key_biases": split_names(rule.get("Key_Biases", "")),
            "decision_rules": decision_rules,
            "anti_patterns": rule.get("Anti_Patterns", ""),
            "severity": rule.get("Severity", "MEDIUM"),
        }

    @staticmethod
    def _pick_named(domain: str, names: list, results: list) -> dict:
        """The first of `names` that is a record of the domain; else the top search result."""
        for name in names:
            row = find_record(domain, name)
            if row:
                return row
        return results[0] if results else {}

    @staticmethod
    def _pick_many(domain: str, names: list, results: list, limit: int) -> list:
        """Records named first (in order), then search results, up to limit, no duplicates."""
        name_col = {"heuristics": "Mental Model", "biases": "Bias", "team": "Pattern"}[domain]
        out, seen = [], set()
        for row in [find_record(domain, n) for n in names] + list(results):
            key = row.get(name_col) if row else None
            if key and key not in seen:
                seen.add(key)
                out.append(row)
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _alternatives(results: list, name_col: str, primary: str, limit: int) -> list:
        return [r.get(name_col, "") for r in results if r.get(name_col) and r.get(name_col) != primary][:limit]

    def generate(self, query: str, project_name: str = None, depth: str = "standard",
                 problem_type: str = None, category: str = None) -> dict:
        """Build the plan dict.

        Args:
            query: Problem description (any length)
            project_name: Optional project name (default: the start of the query)
            depth: quick, standard, deep, or executive
            problem_type: Problem type (e.g. "Diagnostic"); auto-detected if None
            category: Reasoning category (e.g. "Business Performance"); auto-detected if None

        Raises:
            ValueError: if depth, problem_type or category is not a known value.
        """
        if depth not in DEPTH_CONFIG:
            raise ValueError(f"unknown depth {depth!r}; choose one of: {', '.join(VALID_DEPTHS)}")
        cfg = DEPTH_CONFIG[depth]
        query = unicodedata.normalize("NFC", str(query)).strip()

        # Step 1: Problem type (how the problem is shaped) — explicit beats auto-detect
        if problem_type:
            name = resolve_choice(problem_type, problem_type_names(), "problem type")
            rows = _load_csv(DATA_DIR / CSV_CONFIG["problem-types"]["file"])
            type_info = next(r for r in rows if r["Problem Type"] == name)
            type_source = "explicit"
        else:
            type_info = classify_problem_type(query)
            type_source = type_info.pop("_source", "default") if type_info else "default"
        type_name = type_info.get("Problem Type", "General")

        # Step 2: Category (business context) selects the reasoning rule
        if category:
            category = resolve_choice(category, category_names(), "category")
            category_source = "explicit"
        else:
            category = classify_category(query)
            category_source = "auto" if category else "default"
        reasoning = self._apply_reasoning(category)

        # Step 3: Multi-domain search (scaled by depth)
        found = {d: r.get("results", []) for d, r in self._multi_domain_search(query, depth).items()}

        # Step 4: the category rule decides first, the problem type's own
        # recommendations next, keyword search ranking last.
        type_approach = split_names(type_info.get("Recommended Approach", ""), ";")
        type_analysis = split_names(type_info.get("Analysis Methods", ""), ";")
        type_decomp = split_names(type_info.get("Decomposition Style", ""), ";")
        rule_decomp = reasoning["decomposition_style"] if category else []
        rule_analysis = reasoning["analysis_priority"] if category else []
        rule_comm = reasoning["communication_style"] if category else []

        best_decomp = self._pick_named("decomposition", rule_decomp + type_decomp + type_approach + ["Issue Tree"],
                                       found["decomposition"])
        best_analysis = self._pick_named("analysis", rule_analysis + type_approach + type_analysis + ["Benchmarking"],
                                         found["analysis"])
        best_prior = self._pick_named("prioritization", rule_decomp + rule_analysis + type_analysis
                                      + ["Impact-Feasibility Matrix"], found["prioritization"])
        best_comm = self._pick_named("communication", rule_comm + ["Pyramid Principle"], found["communication"])

        model_names = _interleave(reasoning["key_heuristics"], split_names(type_info.get("Mental Models", ""), ";"))
        bias_names = _interleave(reasoning["key_biases"], split_names(type_info.get("Key Biases", ""), ";"))
        models = self._pick_many("heuristics", model_names, found["heuristics"], cfg["models"])
        biases = self._pick_many("biases", bias_names, found["biases"], cfg["biases"])
        team = self._pick_many("team", [], found["team"] + [find_record("team", n) for n in DEFAULT_TEAM],
                               cfg["team"]) if cfg["team"] else []

        decomp_alts = [find_record("decomposition", n).get("Framework") for n in rule_decomp + type_decomp]
        decomp_alts += [r.get("Framework") for r in found["decomposition"]]
        analysis_alts = [find_record("analysis", n).get("Tool") for n in rule_analysis + type_analysis]
        analysis_alts += [r.get("Tool") for r in found["analysis"]]

        def alternatives(names, primary):
            out = []
            for n in names:
                if n and n != primary and n not in out:
                    out.append(n)
            return out[:cfg["alternatives"]]

        plan = {
            "query": query,
            "depth": depth,
            "project_name": project_name or _short_name(query) or "plan",
            "problem_category": category or "General",
            "classification": {
                "type_source": type_source,
                "category_source": category_source,
                "rule_applied": bool(category),
            },
            "problem_type": {
                "name": type_name,
                "complexity": type_info.get("Complexity", "Medium"),
                "characteristics": type_info.get("Characteristics", ""),
                "recommended_approach": type_info.get("Recommended Approach", ""),
                "common_mistakes": type_info.get("Common Mistakes", ""),
                "time_frame": type_info.get("Time Frame", ""),
                "team_size": type_info.get("Team Size", ""),
            },
            "methodology": {
                "steps_focus": reasoning["steps_focus"],
                "steps": load_steps(),
            },
            "decomposition": {
                "primary": best_decomp.get("Framework", "Issue Tree"),
                "type": best_decomp.get("Type", ""),
                "description": best_decomp.get("Description", ""),
                "structure": best_decomp.get("Structure Pattern", ""),
                "example": best_decomp.get("Example Application", ""),
                "mece_test": best_decomp.get("MECE Test", ""),
                "mistakes": best_decomp.get("Common Mistakes", ""),
                "alternatives": alternatives(decomp_alts, best_decomp.get("Framework")),
            },
            "prioritization": {
                "technique": best_prior.get("Technique", "Impact-Feasibility Matrix"),
                "how_to": best_prior.get("How to Apply", ""),
                "output": best_prior.get("Output Format", ""),
                "pitfalls": best_prior.get("Pitfalls", ""),
            },
            "analysis": {
                "primary_tool": best_analysis.get("Tool", "Benchmarking"),
                "how_to": best_analysis.get("How to Apply", ""),
                "data_needed": best_analysis.get("Data Requirements", ""),
                "strengths": best_analysis.get("Strengths", ""),
                "limitations": best_analysis.get("Limitations", ""),
                "alternatives": alternatives(analysis_alts, best_analysis.get("Tool")),
            },
            "communication": {
                "pattern": best_comm.get("Pattern", "Pyramid Principle (Answer First)"),
                "structure": best_comm.get("Structure", ""),
                "audience": best_comm.get("Audience", ""),
            },
            "mental_models": [
                {"name": h.get("Mental Model", ""), "application": h.get("Application to Problem Solving", ""),
                 "description": h.get("Description", ""), "danger": h.get("Danger Zone", "")}
                for h in models
            ],
            "bias_warnings": [
                {"bias": b.get("Bias", ""), "debiasing": b.get("Debiasing Strategy", ""),
                 "detect": b.get("How to Detect", ""), "severity": b.get("Severity", "")}
                for b in biases
            ],
            "team_recommendations": [
                {"pattern": t.get("Pattern", ""), "how": t.get("How to Facilitate", "")} for t in team
            ],
            "anti_patterns": reasoning["anti_patterns"],
            "decision_rules": reasoning["decision_rules"],
            "severity": reasoning["severity"],
        }
        plan["hints"] = fallback_hints(plan)
        return plan


# ============ RENDERING ============
def _first(text: str, n: int = 2, sep: str = ";") -> str:
    """The first n items of a 'a; b; c' list, joined back."""
    return "; ".join(split_names(text, sep)[:n])


def _sentence(text: str) -> str:
    """The first sentence of text."""
    text = str(text).strip()
    cut = text.find(". ")
    return text if cut < 0 else text[:cut + 1]


def _rule_text(key: str, value: str) -> str:
    """'if_revenue_problem', 'decompose-price-x-volume' -> 'If revenue problem: decompose price x volume'."""
    cond = key.replace("_", " ").strip()
    cond = cond[3:] if cond.lower().startswith("if ") else cond
    return f"If {cond}: {str(value).replace('-', ' ')}"


def fallback_hints(plan: dict) -> list:
    """What to tell the AI when auto-detection found nothing (or only a weak match)."""
    cls = plan["classification"]
    hints = []
    if cls["type_source"] == "default":
        hints.append("No problem type matched clearly. Re-run with `--type` "
                     f"({', '.join(problem_type_names())}).")
    elif cls["type_source"] == "text":
        hints.append(f"The problem type ({plan['problem_type']['name']}) is a weak guess: no keyword matched. "
                     f"If it is wrong, re-run with `--type` ({', '.join(problem_type_names())}).")
    if cls["category_source"] == "default":
        names = ", ".join(f'"{c}"' for c in category_names())
        hints.append("No context matched clearly, so generic defaults are used. "
                     f"Re-run with `--category` ({names}).")
    return hints


def _source(src: str) -> str:
    return {"explicit": "set by you", "auto": "auto-detected", "text": "weak guess", "default": "no match"}.get(src, src)


def _sections(plan: dict) -> list:
    """The plan as (heading, [lines]) pairs, lines in light markdown. Depth decides what is in it."""
    cfg = DEPTH_CONFIG[plan["depth"]]
    problem, cls = plan["problem_type"], plan["classification"]
    decomp, prior, analysis, comm = plan["decomposition"], plan["prioritization"], plan["analysis"], plan["communication"]
    out = []

    head = [f"**Request:** {_preview(plan['query'])}"] if plan.get("query") else []
    head += [f"> {h}" for h in plan.get("hints", fallback_hints(plan))]
    out.append(("", head))

    if cfg["executive"]:
        out.append(("Executive Summary (SCR)", _executive_summary(plan)))

    lines = [f"- **Type:** {problem['name']} ({_source(cls['type_source'])}), complexity {problem['complexity']}",
             f"- **Context:** {plan['problem_category']} ({_source(cls['category_source'])}), "
             f"stakes {plan.get('severity', 'MEDIUM')}"]
    if plan["depth"] != "quick":
        if problem.get("time_frame"):
            lines.append(f"- **Time frame:** {problem['time_frame']}; **team:** {problem.get('team_size') or 'n/a'}")
        if problem.get("recommended_approach"):
            lines.append(f"- **Approach:** {problem['recommended_approach']}")
    if cfg["details"] and problem.get("common_mistakes"):
        lines.append(f"- **Common mistakes with this type:** {problem['common_mistakes']}")
    out.append(("Problem Classification", lines))

    out.append(("Recommended Process", [plan["methodology"]["steps_focus"]]))

    if cfg["steps"]:
        lines = []
        for s in plan["methodology"]["steps"]:
            acts = s["activities"] if cfg["details"] else _first(s["activities"], 3)
            lines.append(f"{s['number']}. **{s['name']}** ({s['time']}): {acts}")
            lines.append(f"   - Done when: {s['gate']}")
            if cfg["details"]:
                lines.append(f"   - Pitfalls: {s['pitfalls']}")
        out.append(("The 7 Steps", lines))

    lines = [f"- **Structure:** {decomp['structure']}"] if decomp.get("structure") else []
    if plan["depth"] != "quick" and decomp.get("mece_test"):
        lines.append(f"- **MECE test:** {decomp['mece_test']}")
    if cfg["details"] and decomp.get("example"):
        lines.append(f"- **Example:** {decomp['example']}")
    if cfg["details"] and decomp.get("mistakes"):
        lines.append(f"- **Mistakes:** {decomp['mistakes']}")
    if decomp.get("alternatives"):
        lines.append(f"- **Alternatives:** {', '.join(decomp['alternatives'])}")
    out.append((f"Decomposition: {decomp['primary']}", lines))

    if plan["depth"] != "quick":
        lines = [f"- **How:** {prior['how_to']}"] if prior.get("how_to") else []
        if cfg["details"] and prior.get("output"):
            lines.append(f"- **Output:** {prior['output']}")
        if cfg["details"] and prior.get("pitfalls"):
            lines.append(f"- **Pitfalls:** {prior['pitfalls']}")
        out.append((f"Prioritization: {prior['technique']}", lines))

    lines = []
    if cfg["details"] and analysis.get("how_to"):
        lines.append(f"- **How:** {analysis['how_to']}")
    if analysis.get("data_needed"):
        data = analysis["data_needed"] if plan["depth"] != "quick" else _first(analysis["data_needed"], 3)
        lines.append(f"- **Data needed:** {data}")
    if cfg["details"] and analysis.get("strengths"):
        lines.append(f"- **Strengths:** {analysis['strengths']}")
        lines.append(f"- **Limitations:** {analysis['limitations']}")
    if analysis.get("alternatives"):
        lines.append(f"- **Also consider:** {', '.join(analysis['alternatives'])}")
    out.append((f"Analysis: {analysis['primary_tool']}", lines))

    if plan["depth"] != "quick" and plan.get("decision_rules"):
        out.append(("Decision Rules", ["Pick the branch that fits the situation:"]
                    + [f"- {_rule_text(k, v)}" for k, v in plan["decision_rules"].items()]))

    if plan["depth"] != "quick":
        lines = [f"- **Structure:** {comm['structure']}"] if comm.get("structure") else []
        if comm.get("audience"):
            lines.append(f"- **Audience:** {comm['audience']}")
        out.append((f"Communication: {comm['pattern']}", lines))

    models = plan.get("mental_models", [])
    if models:
        lines = []
        for m in models:
            what = m["description"] if plan["depth"] != "quick" else _sentence(m["description"])
            lines.append(f"- **{m['name']}**: {what}")
            if cfg["details"] and m.get("application"):
                lines.append(f"  - Helps: {m['application']}")
            if cfg["details"] and m.get("danger"):
                lines.append(f"  - Danger zone: {m['danger']}")
        out.append(("Mental Models", lines))

    biases = plan.get("bias_warnings", [])
    if biases:
        lines = []
        for b in biases:
            remedy = b["debiasing"] if plan["depth"] != "quick" else _first(b["debiasing"], 1)
            lines.append(f"- **{b['bias']}**: {remedy}")
            if cfg["details"] and b.get("detect"):
                lines.append(f"  - Warning signs: {b['detect']}")
        out.append(("Bias Warnings", lines))

    team = plan.get("team_recommendations", [])
    if team:
        out.append(("Team", [f"- **{t['pattern']}**: {t['how'] if cfg['details'] else _first(t['how'], 2)}"
                             for t in team]))

    if plan.get("anti_patterns"):
        anti = plan["anti_patterns"] if plan["depth"] != "quick" else _first(plan["anti_patterns"], 3)
        out.append(("Avoid", [anti]))

    if cfg["executive"]:
        out.append(("Key Risks", _key_risks(plan)))
        out.append(("Decision Needed", _decision_needed(plan)))

    if cfg["checklist"]:
        out.append(("Problem-Solving Checklist", [f"- [ ] {item}" for item in CHECKLIST]))
    else:
        out.append(("First Move", [
            "Write the problem as one specific, measurable sentence and your best-guess answer (Day 1 answer); "
            "then check the two branches most likely to prove it wrong."]))
    return out


CHECKLIST = [
    "Problem statement is specific, bounded, and measurable",
    "Logic tree is MECE",
    "Top 2-3 priority issues identified (80/20 applied)",
    "Each priority issue has a testable hypothesis",
    "Analyses linked to specific hypotheses",
    "Day 1 answer stated with confidence level",
    "Findings pass the 'so what?' test",
    "Recommendation leads the communication",
    "Counterarguments addressed",
    "Next steps specific with owners and dates",
]


def _executive_summary(plan: dict) -> list:
    problem = plan["problem_type"]
    decomp, analysis, comm = plan["decomposition"], plan["analysis"], plan["communication"]
    traits = _first(problem.get("characteristics", ""), 2)
    trap = _first(plan.get("anti_patterns", "") or problem.get("common_mistakes", ""), 1)
    return [
        f"- **Situation:** \"{_preview(plan['query'], 240)}\": a {problem['name'].lower()} problem "
        f"in {plan['problem_category']}, stakes {plan.get('severity', 'MEDIUM')}.",
        f"- **Complication:** {traits}." + (f" The usual trap: {trap.lower()}." if trap else ""),
        f"- **Resolution (approach):** {plan['methodology']['steps_focus']}. Break it down with {decomp['primary']}, "
        f"test the top hypotheses with {analysis['primary_tool']}, present with {comm['pattern']}.",
        "- Replace the approach with the answer once the analysis is done: lead with the recommendation, "
        "then the three reasons, then the ask.",
    ]


def _key_risks(plan: dict) -> list:
    risks = split_names(plan.get("anti_patterns", ""), ";")[:3]
    risks += split_names(plan["problem_type"].get("common_mistakes", ""), ";")[:2]
    lines = [f"- {r}" for r in risks]
    lines += [f"- {b['bias']} in the team's judgment: {_first(b['debiasing'], 1)}"
              for b in plan.get("bias_warnings", [])[:2]]
    return lines


def _decision_needed(plan: dict) -> list:
    lines = ["- Agree the problem statement, the success metric and the deadline.",
             f"- Fund the {plan['analysis']['primary_tool']} work and name its owner "
             f"({plan['problem_type'].get('team_size') or 'a small team'}, {(plan['problem_type'].get('time_frame') or 'time-boxed').lower()})."]
    rules = plan.get("decision_rules") or {}
    if rules:
        lines.append("- Confirm which situation applies, because it sets the first analysis: "
                     + "; ".join(_rule_text(k, v) for k, v in rules.items()) + ".")
    lines.append("- Set the checkpoint where leadership sees the Day 1 answer and decides go / change course / stop.")
    return lines


def format_markdown(plan: dict) -> str:
    """Format problem-solving plan as markdown."""
    depth = plan.get("depth", "standard")
    label = f" [{depth.upper()}]" if depth != "standard" else ""
    out = [f"## Problem-Solving Plan: {plan['project_name']}{label}", ""]
    for heading, lines in _sections(plan):
        if heading:
            out.append(f"### {heading}")
        out += [line for line in lines if line is not None]
        out.append("")
    return "\n".join(out)


BOX_WIDTH = 90


def format_ascii_box(plan: dict) -> str:
    """Format problem-solving plan as an ASCII box; every line is BOX_WIDTH terminal columns wide."""
    inner = BOX_WIDTH - 4
    depth = plan.get("depth", "standard")
    label = f" [{depth.upper()}]" if depth != "standard" else ""

    def row(text=""):
        # Columns, not characters: combining marks take none, wide characters take two
        return f"| {pad_display(text, inner)} |"

    def wrapped(text, indent=""):
        text = text.replace("**", "").replace("`", "")
        lead = len(text) - len(text.lstrip())
        first = " " * lead
        return [row(line) for line in wrap_display(text.strip(), inner, first, first + "  " + indent)] or [row()]

    border = "+" + "=" * (BOX_WIDTH - 2) + "+"
    lines = [border]
    lines += wrapped(f"PROBLEM-SOLVING PLAN: {plan['project_name']}{label}")
    lines.append(border)
    for heading, body in _sections(plan):
        lines.append(row())
        if heading:
            lines += wrapped(heading.upper())
        for text in body:
            lines += wrapped(text)
    lines += [row(), border]
    return "\n".join(lines)


# ============ PERSISTENCE ============
def _plan_dir(plan: dict, output_dir: str = None) -> Path:
    base = Path(output_dir) if output_dir else default_output_dir()
    plan_dir = base / "solving-plans" / slugify(plan.get("project_name", "default"))
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


def persist_plan(plan: dict, output_dir: str = None, force: bool = False):
    """Save the plan as PLAN.md; returns (path, written). An existing PLAN.md is kept unless force."""
    plan_dir = _plan_dir(plan, output_dir)
    prepare_folder(plan_dir, plan["query"], plan["problem_type"]["name"], ["PLAN.md"], force)
    content = format_markdown(plan)
    if len(" ".join(plan["query"].split())) > REQUEST_PREVIEW:
        content += "\n### Full Request\n\n" + _quote(plan["query"]) + "\n"
    content += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    written, _ = save_docs(plan_dir, {"PLAN.md": content}, force)
    return str(plan_dir / "PLAN.md"), bool(written)


def _quote(text: str) -> str:
    return "\n".join(f"> {line}".rstrip() for line in str(text).splitlines()) or ">"


def _guide(step: dict) -> str:
    return (f"> {step['description']}\n>\n> **Do:** {step['activities']}\n>\n"
            f"> **Done when:** {step['gate']}\n>\n> **Tip:** {_first(step['tips'], 2)}")


def persist_step_by_step(plan: dict, output_dir: str = None, force: bool = False):
    """Save the plan as one markdown file per step; returns (dir, written, kept).

    Files that already exist hold the user's notes and are kept unless force is set.
    """
    plan_dir = _plan_dir(plan, output_dir)
    project = plan["project_name"]
    problem = plan["problem_type"]
    decomp, prior, analysis, comm = plan["decomposition"], plan["prioritization"], plan["analysis"], plan["communication"]
    steps = {s["number"]: s for s in plan["methodology"]["steps"]}
    models, biases = plan.get("mental_models", []), plan.get("bias_warnings", [])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    docs = {}

    docs["00-OVERVIEW.md"] = f"""# Problem-Solving Plan: {project}

**Problem:** {problem['name']} | **Context:** {plan['problem_category']} | **Depth:** {plan['depth']} | **Generated:** {ts}
**Request:** {_preview(plan['query'], 300)}

Work the steps in order. Tick a step's **Done?** box only when its quality gate is met
(the AI does this with `search.py --done <step>`); `/solve.resume` continues at the first open step.

{progress_table()}

Also: [BIAS-WARNINGS.md](./BIAS-WARNINGS.md) (biases and mental models to watch),
[DECISION-LOG.md](./DECISION-LOG.md) (decisions made along the way).

## Problem Classification
- **Type:** {problem['name']} ({_source(plan['classification']['type_source'])}), complexity {problem['complexity']}
- **Context:** {plan['problem_category']} ({_source(plan['classification']['category_source'])}), stakes {plan.get('severity', 'MEDIUM')}
- **Time frame:** {problem.get('time_frame') or 'n/a'}; **team:** {problem.get('team_size') or 'n/a'}
- **Approach:** {problem.get('recommended_approach') or 'n/a'}
- **Recommended process:** {plan['methodology']['steps_focus']}
"""

    docs["01-PROBLEM-DEFINITION.md"] = f"""# Step 1: Define the Problem

{_guide(steps[1])}

## Request (as given)
{_quote(plan['query'])}

## Problem Statement
<!-- Rewrite the request as one specific, bounded, measurable sentence -->

**Type:** {problem['name']}
**Characteristics:** {problem.get('characteristics', '')}

## Success Criteria
<!-- What does "solved" look like? -->
- [ ] Criterion 1:
- [ ] Criterion 2:
- [ ] Criterion 3:

## Scope Boundaries
- **In scope:**
- **Out of scope:**

## Stakeholders
| Stakeholder | Role | Interest Level |
|-------------|------|---------------|
| | | |
"""

    alts = ", ".join(decomp.get("alternatives", [])) or "n/a"
    docs["02-DECOMPOSITION.md"] = f"""# Step 2: Decompose the Problem

{_guide(steps[2])}

## Primary Framework: {decomp['primary']}
{decomp.get('description', '')}

**Structure:** {decomp.get('structure', '')}

**MECE test:** {decomp.get('mece_test', '')}

**Alternatives:** {alts}

## Your Decomposition
<!-- Build your logic tree here -->
```
Root Problem
├── Branch 1: [describe]
│   ├── Sub-branch 1a
│   └── Sub-branch 1b
├── Branch 2: [describe]
│   ├── Sub-branch 2a
│   └── Sub-branch 2b
└── Branch 3: [describe]
    ├── Sub-branch 3a
    └── Sub-branch 3b
```

## MECE Validation
- [ ] Branches are mutually exclusive (no overlap)
- [ ] Branches are collectively exhaustive (nothing missing)
- [ ] Each leaf is specific enough to analyze
"""

    docs["03-PRIORITIZATION.md"] = f"""# Step 3: Prioritize Issues

{_guide(steps[3])}

## Technique: {prior['technique']}
**How to apply:** {prior.get('how_to', '')}

**Expected output:** {prior.get('output', '')}

## Priority Matrix
| Branch | Impact (1-5) | Feasibility (1-5) | Priority |
|--------|-------------|-------------------|----------|
| | | | |
| | | | |
| | | | |

## Top 3 Priority Issues
1. **Issue:**
   - Why it matters:
   - Hypothesis:
2. **Issue:**
   - Why it matters:
   - Hypothesis:
3. **Issue:**
   - Why it matters:
   - Hypothesis:
"""

    analysis_alts = ", ".join(analysis.get("alternatives", [])) or "n/a"
    rules = "\n".join(f"- {_rule_text(k, v)}" for k, v in (plan.get("decision_rules") or {}).items())
    docs["04-ANALYSIS-PLAN.md"] = f"""# Step 4: Analysis Plan

{_guide(steps[4])}

## Primary Tool: {analysis['primary_tool']}
**How to apply:** {analysis.get('how_to', '')}

**Data requirements:** {analysis.get('data_needed', '')}

**Also consider:** {analysis_alts}
{chr(10) + "## Decision Rules" + chr(10) + rules + chr(10) if rules else ""}
## Workplan
| Priority Issue | Hypothesis | Analysis Method | Data Source | Owner | Deadline |
|---------------|-----------|----------------|-------------|-------|----------|
| | | | | | |
| | | | | | |
| | | | | | |
"""

    finding = """### Finding {n}
- **Branch:**
- **Data:**
- **Insight:**
- **So what?**
- **Confidence:** High / Medium / Low
"""
    docs["05-FINDINGS.md"] = f"""# Step 5: Findings

{_guide(steps[5])}

## Analysis Results

{chr(10).join(finding.format(n=n) for n in (1, 2, 3))}
## Surprises / Unexpected Results
<!-- Document anything that challenged your hypothesis -->
"""

    docs["06-SYNTHESIS.md"] = f"""# Step 6: Synthesis

{_guide(steps[6])}

## Communication Pattern: {comm['pattern']}
**Structure:** {comm.get('structure', '')}
**Audience:** {comm.get('audience', '')}

## Governing Thought
<!-- One sentence that answers the original problem -->

## Key Themes
### Theme 1: [Name]
- Supporting findings:
- So what:

### Theme 2: [Name]
- Supporting findings:
- So what:

### Theme 3: [Name]
- Supporting findings:
- So what:

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| | | | |
"""

    docs["07-RECOMMENDATION.md"] = f"""# Step 7: Recommendation

{_guide(steps[7])}

## Executive Summary
<!-- Situation, complication, resolution: the problem, why it matters now, what to do -->

## Recommendation
<!-- Clear, actionable recommendation -->

## Supporting Arguments
1. **Argument 1:**
   - Evidence:
2. **Argument 2:**
   - Evidence:
3. **Argument 3:**
   - Evidence:

## Counterarguments Addressed
- **Objection:**
  **Response:**

## Next Steps
| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| | | | |
| | | | |
"""

    bias_content = "# Bias Warnings\n\nThese cognitive biases are most likely to affect this analysis.\n\n"
    for i, b in enumerate(biases, 1):
        bias_content += f"## {i}. {b.get('bias', 'Unknown')}\n"
        if b.get("detect"):
            bias_content += f"**Warning signs:** {b['detect']}\n\n"
        bias_content += f"**Remedy:** {b.get('debiasing', 'N/A')}\n\n"
    if plan.get("anti_patterns"):
        bias_content += f"## Anti-Patterns to Avoid\n{plan['anti_patterns']}\n\n"
    if models:
        bias_content += "## Recommended Mental Models\n"
        for m in models:
            bias_content += f"- **{m['name']}**: {m.get('application', '')}\n"
    docs["BIAS-WARNINGS.md"] = bias_content

    docs["DECISION-LOG.md"] = f"""# Decision Log: {project}

| # | Date | Decision | Rationale | Confidence | Status |
|---|------|----------|-----------|------------|--------|
| 1 | {ts[:10]} | | | | Open |
"""

    prepare_folder(plan_dir, plan["query"], problem["name"], docs, force)
    written, kept = save_docs(plan_dir, docs, force)
    record_state(plan_dir, plan, {name: docs[name] for name in written})
    return str(plan_dir), written, kept


# ============ NEXT-STEP SUGGESTIONS ============
NEXT_STEPS = {
    "quick": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve` | Full standard analysis |
| `/solve.deep` | Deep analysis with alternatives & mental models |
| `/decide.quick` | Quick decision from this analysis |
""",
    "standard": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.deep` | Deeper analysis with more frameworks & mental models |
| `/solve.exec` | Executive summary for leadership |
| `/decide` | Compare options & make a decision |
| Add "save step-by-step" | Create a markdown workspace, one file per step |
""",
    "deep": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive summary for stakeholders |
| `/decide.deep` | Detailed option comparison from this analysis |
| Add "save step-by-step" | Create a markdown workspace, one file per step |
""",
    "executive": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.exec` | Executive-level decision from this analysis |
| Add "save step-by-step" | Create a full markdown workspace |
| `/decide` | Standard-depth option comparison |
""",
}
RESUME_STEP = "| `/solve.resume` | Continue this workspace later at the first open step |\n"


def next_steps_table(text: str, saved_step_docs: bool) -> str:
    """The Next Steps table, without the "save step-by-step" row once the workspace is saved."""
    if not saved_step_docs:
        return text
    return "".join(line for line in text.splitlines(True) if "save step-by-step" not in line)


# ============ PUBLIC API ============
def generate_solving_plan(query: str, project_name: str = None, output_format: str = "ascii",
                          persist: bool = False, output_dir: str = None,
                          depth: str = "standard", step_docs: bool = False,
                          problem_type: str = None, category: str = None,
                          force: bool = False) -> str:
    """Generate a formatted problem-solving plan; optionally save it.

    Args:
        query: Problem description
        project_name: Optional project name
        output_format: 'ascii' or 'markdown'
        persist: Whether to save to file
        output_dir: Output directory for persistence
        depth: Analysis depth - quick, standard, deep, or executive
        step_docs: If True with persist, create separate markdown files per step
        force: Replace files that already exist (default: keep them)
        problem_type: Problem type override (see --type)
        category: Reasoning category override (see --category)

    Raises:
        ValueError: for unknown depth, type or category.
    """
    plan = ProblemSolvingAdvisor().generate(query, project_name, depth=depth,
                                            problem_type=problem_type, category=category)
    result = format_markdown(plan) if output_format == "markdown" else format_ascii_box(plan)
    next_steps = NEXT_STEPS[depth]

    if persist:
        result += "\n" + save_report(plan, output_dir, step_docs, force)
        if step_docs:
            next_steps = next_steps_table(next_steps, True) + RESUME_STEP
    return result + next_steps


def save_plan(plan: dict, output_dir: str = None, step_docs: bool = False, force: bool = False) -> dict:
    """Persist the plan; returns {"path", "written", "kept"}."""
    if step_docs:
        plan_dir, written, kept = persist_step_by_step(plan, output_dir, force)
        return {"path": plan_dir, "written": written, "kept": kept}
    path, written = persist_plan(plan, output_dir, force)
    return {"path": path, "written": ["PLAN.md"] if written else [], "kept": [] if written else ["PLAN.md"]}


def save_report(plan: dict, output_dir: str = None, step_docs: bool = False, force: bool = False) -> str:
    """Persist the plan and describe what was written."""
    saved = save_plan(plan, output_dir, step_docs, force)
    if not step_docs:
        if saved["written"]:
            return f"\nPlan saved to: {saved['path']}"
        return f"\nKept the existing plan at {saved['path']} (add --force to replace it)."
    out = f"\nStep-by-step plan saved to: {saved['path']}/\n  Files created: {len(saved['written'])}"
    out += "".join(f"\n    {f}" for f in saved["written"])
    if saved["kept"]:
        out += f"\n  Kept {len(saved['kept'])} existing files with your notes (add --force to replace them):"
        out += "".join(f"\n    {f}" for f in saved["kept"])
    return out
