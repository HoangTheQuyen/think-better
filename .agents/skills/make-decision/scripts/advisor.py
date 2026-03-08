#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Advisor - Generates comprehensive decision-making plans,
comparison matrices, and decision journal entries.

Usage:
    from advisor import DecisionAdvisor
    advisor = DecisionAdvisor("choosing between AWS and Azure", search_fn=search)
    plan = advisor.generate()
    print(advisor.format_ascii_box(plan))
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from core import search, search_domain, load_csv, DATA_DIR


# ============ DECISION ADVISOR ============
class DecisionAdvisor:
    """Generates decision plans, journals, and comparison matrices."""

    def __init__(self, query: str = "", search_fn=None):
        self.query = query
        self.search_fn = search_fn or search

    # ---- Classification (T013) ----
    def classify_decision_type(self) -> dict:
        """Classify the decision type from natural language description."""
        result = search_domain(self.query, "types", 1)
        results = result.get("results", [])
        if results:
            return results[0]
        return {
            "Decision Type": "Multi-Option Selection",
            "Characteristics": "Multiple options requiring structured evaluation",
            "Recommended Frameworks": "Weighted Criteria Matrix, Pros-Cons-Fixes Analysis",
            "Analysis Methods": "Relative Value Scoring, Sensitivity Analysis",
            "Common Pitfalls": "Choice overload without clear criteria",
            "Warning Signs": "",
            "Example Scenarios": "",
        }

    # ---- Plan Generation (T014) ----
    def generate(self, project_name: str = None) -> dict:
        """Generate a comprehensive decision-making plan."""
        # Step 1: Classify the decision type
        dtype = self.classify_decision_type()
        type_name = dtype.get("Decision Type", "General")

        # Step 2: Search frameworks
        fw_result = search_domain(self.query, "frameworks", 3)
        frameworks = fw_result.get("results", [])

        # Step 3: Search biases
        bias_result = search_domain(self.query, "biases", 3)
        biases = bias_result.get("results", [])

        # Step 4: Search analysis techniques
        analysis_result = search_domain(self.query, "analysis", 3)
        analysis = analysis_result.get("results", [])

        # Step 5: Search criteria templates
        criteria_result = search_domain(self.query, "criteria", 2)
        criteria = criteria_result.get("results", [])

        # Step 6: Search facilitation techniques
        facil_result = search_domain(self.query, "facilitation", 2)
        facilitation = facil_result.get("results", [])

        # Select best framework based on recommended frameworks for this type
        rec_frameworks = dtype.get("Recommended Frameworks", "")
        best_framework = self._select_best_match(frameworks, rec_frameworks)

        # Select best analysis based on recommended methods for this type
        rec_analysis = dtype.get("Analysis Methods", "")
        best_analysis = self._select_best_match(analysis, rec_analysis)

        return {
            "project_name": project_name or self.query[:60],
            "decision_type": {
                "name": type_name,
                "characteristics": dtype.get("Characteristics", ""),
                "recommended_frameworks": dtype.get("Recommended Frameworks", ""),
                "analysis_methods": dtype.get("Analysis Methods", ""),
                "common_pitfalls": dtype.get("Common Pitfalls", ""),
                "warning_signs": dtype.get("Warning Signs", ""),
            },
            "framework": {
                "name": best_framework.get("Framework", "Weighted Criteria Matrix"),
                "category": best_framework.get("Category", ""),
                "description": best_framework.get("Description", ""),
                "steps": best_framework.get("Steps", ""),
                "strengths": best_framework.get("Strengths", ""),
                "limitations": best_framework.get("Limitations", ""),
                "complexity": best_framework.get("Complexity", "Medium"),
                "alternatives": [f.get("Framework", "") for f in frameworks[1:3]],
            },
            "criteria": {
                "domain": criteria[0].get("Domain", "") if criteria else "",
                "criteria_list": criteria[0].get("Criteria", "") if criteria else "",
                "weights": criteria[0].get("Default Weights", "") if criteria else "",
                "measurement": criteria[0].get("Measurement Guidance", "") if criteria else "",
                "mistakes": criteria[0].get("Common Mistakes", "") if criteria else "",
            },
            "analysis_techniques": [
                {
                    "technique": a.get("Technique", ""),
                    "when": a.get("When to Use", ""),
                    "output": a.get("Output Format", ""),
                }
                for a in analysis[:3]
            ],
            "bias_warnings": [
                {
                    "bias": b.get("Bias", ""),
                    "impact": b.get("Impact on Decisions", ""),
                    "debiasing": b.get("Debiasing Strategy", ""),
                    "severity": b.get("Severity", "Medium"),
                }
                for b in biases[:3]
            ],
            "facilitation": [
                {
                    "technique": f.get("Technique", ""),
                    "when": f.get("When to Use", ""),
                    "group_size": f.get("Group Size", ""),
                    "time": f.get("Time Required", ""),
                }
                for f in facilitation[:2]
            ],
            "anti_patterns": dtype.get("Common Pitfalls", ""),
        }

    def _select_best_match(self, results: list, priority_str: str) -> dict:
        """Select the best match from results based on priority keywords."""
        if not results:
            return {}
        if not priority_str:
            return results[0]

        priority_lower = priority_str.lower()
        for r in results:
            name = list(r.values())[0] if r else ""
            if name.lower() in priority_lower or any(
                word in priority_lower for word in name.lower().split() if len(word) > 3
            ):
                return r
        return results[0]

    # ---- ASCII Box Formatter (T015) ----
    def format_ascii_box(self, plan: dict) -> str:
        """Format the decision plan as an ASCII box."""
        W = 90
        sep = "+" + "=" * (W - 1) + "+"
        thin_sep = "+" + "-" * (W - 1) + "+"

        def pad(text: str) -> str:
            return f"|  {text}".ljust(W) + "|"

        def blank():
            return "|" + " " * W + "|"

        def wrap(text: str, prefix: str = "  ", width: int = W - 4) -> list:
            if not text:
                return []
            words = text.split()
            lines = []
            current = prefix
            for word in words:
                if len(current) + len(word) + 1 <= width:
                    current += (" " if current != prefix else "") + word
                else:
                    if current != prefix:
                        lines.append(current)
                    current = prefix + word
            if current != prefix:
                lines.append(current)
            return lines

        out = []
        project = plan.get("project_name", "DECISION")
        dt = plan.get("decision_type", {})
        fw = plan.get("framework", {})
        crit = plan.get("criteria", {})
        techniques = plan.get("analysis_techniques", [])
        biases = plan.get("bias_warnings", [])
        facil = plan.get("facilitation", [])
        anti = plan.get("anti_patterns", "")

        # Header
        out.append(sep)
        out.append(pad(f"DECISION-MAKING PLAN: {project}"))
        out.append(sep)
        out.append(blank())

        # Decision Type
        out.append(pad(f"DECISION TYPE: {dt.get('name', '')}"))
        if dt.get("characteristics"):
            for line in wrap(dt["characteristics"], "     "):
                out.append(pad(line))
        if dt.get("warning_signs"):
            for line in wrap(f"Watch for: {dt['warning_signs']}", "     "):
                out.append(pad(line))
        out.append(blank())

        # Framework
        out.append(thin_sep)
        out.append(pad(f"RECOMMENDED FRAMEWORK: {fw.get('name', '')} ({fw.get('complexity', '')} complexity)"))
        if fw.get("description"):
            for line in wrap(fw["description"], "     "):
                out.append(pad(line))
        if fw.get("steps"):
            out.append(pad("   Steps:"))
            for line in wrap(fw["steps"], "     "):
                out.append(pad(line))
        if fw.get("alternatives"):
            alts = [a for a in fw["alternatives"] if a]
            if alts:
                out.append(pad(f"   Alternatives: {', '.join(alts)}"))
        out.append(blank())

        # Criteria
        if crit.get("criteria_list"):
            out.append(thin_sep)
            out.append(pad(f"EVALUATION CRITERIA ({crit.get('domain', 'General')})"))
            criteria_items = [c.strip() for c in crit["criteria_list"].split(",")]
            weight_items = [w.strip() for w in crit.get("weights", "").split(",")]
            for i, c in enumerate(criteria_items):
                w = weight_items[i] if i < len(weight_items) else "?"
                out.append(pad(f"   - {c} (weight: {w})"))
            if crit.get("measurement"):
                out.append(pad("   Scoring Guide:"))
                for line in wrap(crit["measurement"], "     "):
                    out.append(pad(line))
            out.append(blank())

        # Analysis
        if techniques:
            out.append(thin_sep)
            out.append(pad("ANALYSIS TECHNIQUES"))
            for i, t in enumerate(techniques, 1):
                out.append(pad(f"   {i}. {t.get('technique', '')}"))
                if t.get("when"):
                    for line in wrap(t["when"], "      "):
                        out.append(pad(line))
            out.append(blank())

        # Bias Warnings
        if biases:
            out.append(thin_sep)
            out.append(pad("BIAS WARNINGS"))
            for b in biases:
                out.append(pad(f"   ! {b.get('bias', '')} [{b.get('severity', '')}]"))
                if b.get("impact"):
                    for line in wrap(b["impact"], "     "):
                        out.append(pad(line))
                if b.get("debiasing"):
                    for line in wrap(f"Remedy: {b['debiasing']}", "     "):
                        out.append(pad(line))
            out.append(blank())

        # Facilitation
        if facil:
            out.append(thin_sep)
            out.append(pad("GROUP FACILITATION"))
            for f in facil:
                out.append(pad(f"   {f.get('technique', '')} ({f.get('group_size', '')} people, {f.get('time', '')})"))
                if f.get("when"):
                    for line in wrap(f["when"], "     "):
                        out.append(pad(line))
            out.append(blank())

        # Anti-patterns
        if anti:
            out.append(thin_sep)
            out.append(pad("ANTI-PATTERNS TO AVOID"))
            for line in wrap(anti, "   x "):
                out.append(pad(line))
            out.append(blank())

        # Checklist
        out.append(thin_sep)
        out.append(pad("DECISION CHECKLIST"))
        checklist = [
            "Problem clearly defined and bounded",
            "Options exhaustively listed (MECE)",
            "Criteria defined BEFORE evaluating options",
            "Key assumptions identified and tested",
            "Sensitivity analysis on critical assumptions",
            "Bias check completed (review warnings above)",
            "Stakeholders aligned on criteria and process",
            "Decision documented (create a journal entry)",
        ]
        for item in checklist:
            out.append(pad(f"   [ ] {item}"))
        out.append(blank())

        out.append(sep)
        return "\n".join(out)

    # ---- Markdown Formatter (T016) ----
    def format_markdown(self, plan: dict) -> str:
        """Format the decision plan as Markdown."""
        out = []
        project = plan.get("project_name", "DECISION")
        dt = plan.get("decision_type", {})
        fw = plan.get("framework", {})
        crit = plan.get("criteria", {})
        techniques = plan.get("analysis_techniques", [])
        biases = plan.get("bias_warnings", [])
        facil = plan.get("facilitation", [])
        anti = plan.get("anti_patterns", "")

        out.append(f"# Decision-Making Plan: {project}")
        out.append("")

        out.append("## Decision Type")
        out.append(f"- **Type:** {dt.get('name', '')}")
        out.append(f"- **Characteristics:** {dt.get('characteristics', '')}")
        if dt.get("warning_signs"):
            out.append(f"- **Watch for:** {dt['warning_signs']}")
        out.append("")

        out.append("## Recommended Framework")
        out.append(f"- **Framework:** {fw.get('name', '')} ({fw.get('complexity', '')} complexity)")
        out.append(f"- **Description:** {fw.get('description', '')}")
        if fw.get("steps"):
            out.append(f"- **Steps:** {fw['steps']}")
        if fw.get("strengths"):
            out.append(f"- **Strengths:** {fw['strengths']}")
        if fw.get("limitations"):
            out.append(f"- **Limitations:** {fw['limitations']}")
        if fw.get("alternatives"):
            alts = [a for a in fw["alternatives"] if a]
            if alts:
                out.append(f"- **Alternatives:** {', '.join(alts)}")
        out.append("")

        if crit.get("criteria_list"):
            out.append(f"## Evaluation Criteria ({crit.get('domain', 'General')})")
            criteria_items = [c.strip() for c in crit["criteria_list"].split(",")]
            weight_items = [w.strip() for w in crit.get("weights", "").split(",")]
            for i, c in enumerate(criteria_items):
                w = weight_items[i] if i < len(weight_items) else "?"
                out.append(f"- **{c}** (weight: {w})")
            if crit.get("measurement"):
                out.append(f"\n**Scoring Guide:** {crit['measurement']}")
            out.append("")

        if techniques:
            out.append("## Analysis Techniques")
            for t in techniques:
                out.append(f"- **{t.get('technique', '')}**: {t.get('when', '')}")
            out.append("")

        if biases:
            out.append("## Bias Warnings")
            for b in biases:
                out.append(f"- **{b.get('bias', '')}** [{b.get('severity', '')}]: {b.get('impact', '')}")
                out.append(f"  - *Remedy:* {b.get('debiasing', '')}")
            out.append("")

        if facil:
            out.append("## Group Facilitation")
            for f in facil:
                out.append(f"- **{f.get('technique', '')}** ({f.get('group_size', '')} people, {f.get('time', '')})")
                out.append(f"  - {f.get('when', '')}")
            out.append("")

        if anti:
            out.append("## Anti-Patterns to Avoid")
            out.append(f"{anti}")
            out.append("")

        out.append("## Decision Checklist")
        checklist = [
            "Problem clearly defined and bounded",
            "Options exhaustively listed (MECE)",
            "Criteria defined BEFORE evaluating options",
            "Key assumptions identified and tested",
            "Sensitivity analysis on critical assumptions",
            "Bias check completed",
            "Stakeholders aligned on criteria and process",
            "Decision documented (create a journal entry)",
        ]
        for item in checklist:
            out.append(f"- [ ] {item}")
        out.append("")

        return "\n".join(out)

    # ---- Persist Plan (T019) ----
    def persist_plan(self, plan: dict, output_dir: str = None) -> str:
        """Save the decision plan as a markdown file."""
        project = plan.get("project_name", "default")
        slug = re.sub(r'[^\w\s-]', '', project.lower()).strip()
        slug = re.sub(r'[\s]+', '-', slug)[:50]

        base = Path(output_dir) if output_dir else Path.cwd()
        plan_dir = base / "decision-plans" / slug
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_path = plan_dir / "PLAN.md"
        content = self.format_markdown(plan)
        content += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"

        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(plan_path)

    # ---- Decision Journal (T023, T025, T027) ----
    def create_journal(self, decision_statement: str, project_name: str = None) -> str:
        """Create a decision journal entry as a markdown file in .decisions/."""
        decisions_dir = Path.cwd() / ".decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = re.sub(r'[^\w\s-]', '', decision_statement.lower()).strip()
        slug = re.sub(r'[\s]+', '-', slug)[:50]
        filename = f"{date_str}-{slug}.md"

        filepath = decisions_dir / filename
        # Handle duplicate filenames
        if filepath.exists():
            ts = datetime.now().strftime("%H%M%S")
            filename = f"{date_str}-{slug}-{ts}.md"
            filepath = decisions_dir / filename
            import sys
            print(f"Warning: similar journal exists, using {filename}", file=sys.stderr)

        # Generate plan context for the journal
        self.query = decision_statement
        dtype = self.classify_decision_type()

        content = f"""# Decision Journal: {decision_statement}

## Metadata
- **Date:** {date_str}
- **Project:** {project_name or 'N/A'}
- **Decision Type:** {dtype.get('Decision Type', 'General')}
- **Status:** Created

## Hypothesis (Day One Answer)
<!-- What is your initial best guess before deep analysis? -->


## Options
<!-- List all options being considered -->
1. 
2. 
3. 

## Evaluation Criteria
<!-- What criteria will you use to evaluate options? -->
- 

## Expected Outcomes
<!-- What do you expect will happen if you choose your preferred option? -->


## Confidence Level
<!-- High / Medium / Low — and why -->
Medium

## Framework Applied
<!-- Which decision framework did you use? -->


## Analysis Summary
<!-- Key findings from your analysis -->


## Rationale
<!-- Why did you choose this option? -->


## Actual Outcome
<!-- Fill in later: What actually happened? -->


## Reflection
<!-- Fill in later: How did the prediction compare to reality? What would you do differently? -->

"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return str(filepath)

    def review_journals(self) -> str:
        """Review all decision journal entries in .decisions/."""
        decisions_dir = Path.cwd() / ".decisions"
        if not decisions_dir.exists():
            return "No decision journal entries found. Create one with --journal."

        entries = sorted(decisions_dir.glob("*.md"), reverse=True)
        if not entries:
            return "No decision journal entries found. Create one with --journal."

        out = [f"=== DECISION JOURNAL: {len(entries)} entries ===", ""]

        for i, entry in enumerate(entries, 1):
            meta = self._parse_journal_meta(entry)
            status = meta.get("status", "Created")
            confidence = meta.get("confidence", "?")
            decision = meta.get("decision", entry.stem)
            date = meta.get("date", "")
            out.append(f"[{i}] {date} | {decision} | Confidence: {confidence} | Status: {status}")
            out.append(f"    File: {entry.name}")

        return "\n".join(out)

    def _parse_journal_meta(self, filepath: Path) -> dict:
        """Parse metadata from a journal markdown file."""
        meta = {"decision": "", "date": "", "confidence": "?", "status": "Created"}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse title
            title_match = re.search(r'^# Decision Journal:\s*(.+)', content, re.MULTILINE)
            if title_match:
                meta["decision"] = title_match.group(1).strip()

            # Parse date
            date_match = re.search(r'\*\*Date:\*\*\s*(.+)', content)
            if date_match:
                meta["date"] = date_match.group(1).strip()

            # Parse confidence
            conf_match = re.search(r'## Confidence Level\n.*?\n(\w+)', content, re.DOTALL)
            if conf_match:
                meta["confidence"] = conf_match.group(1).strip()

            # Parse status
            status_match = re.search(r'\*\*Status:\*\*\s*(.+)', content)
            if status_match:
                meta["status"] = status_match.group(1).strip()

            # Check if outcome is filled
            outcome_match = re.search(r'## Actual Outcome\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if outcome_match and outcome_match.group(1).strip() and not outcome_match.group(1).strip().startswith('<!--'):
                meta["status"] = "Reviewed"

        except Exception:
            pass
        return meta

    def update_journal(self, journal_id: str, outcome: str) -> str:
        """Update a journal entry with actual outcome and generate reflection prompt."""
        decisions_dir = Path.cwd() / ".decisions"
        if not decisions_dir.exists():
            return "Error: No .decisions/ directory found."

        # Find the journal file
        matches = list(decisions_dir.glob(f"*{journal_id}*"))
        if not matches:
            return f"Error: No journal found matching '{journal_id}'"
        if len(matches) > 1:
            files = "\n".join(f"  - {m.name}" for m in matches)
            return f"Multiple matches found. Be more specific:\n{files}"

        filepath = matches[0]

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Update status
        content = re.sub(
            r'(\*\*Status:\*\*)\s*\w+',
            r'\1 Reviewed',
            content
        )

        # Update actual outcome
        content = re.sub(
            r'(## Actual Outcome\n).*?(?=\n## )',
            f'\\1{outcome}\n\n',
            content,
            flags=re.DOTALL,
        )

        # Generate reflection prompt
        meta = self._parse_journal_meta(filepath)
        reflection_prompt = (
            f"\n## Reflection\n"
            f"<!-- Compare your prediction vs reality -->\n"
            f"**What happened:** {outcome}\n"
            f"**Original confidence:** {meta.get('confidence', '?')}\n"
            f"\n"
            f"Questions to consider:\n"
            f"- Was your hypothesis correct? Why or why not?\n"
            f"- What signals did you miss?\n"
            f"- Would a different framework have led to a better decision?\n"
            f"- What will you do differently next time?\n"
        )

        # Replace reflection section
        content = re.sub(
            r'(## Reflection\n).*',
            reflection_prompt.lstrip("\\n"),
            content,
            flags=re.DOTALL,
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Updated: {filepath}\n\n{reflection_prompt}"

    # ---- Comparison Matrix (T029) ----
    def generate_matrix(self, description: str, custom_criteria: str = None) -> str:
        """Generate a comparison matrix from options description."""
        # Parse options from description
        options = self._parse_options(description)
        if len(options) < 2:
            options = [f"Option A", f"Option B"]

        # Get criteria
        if custom_criteria:
            criteria_items = [c.strip() for c in custom_criteria.split(",")]
            weights = [str(100 // len(criteria_items))] * len(criteria_items)
            # Adjust last weight to sum to 100
            remainder = 100 - (100 // len(criteria_items)) * len(criteria_items)
            weights[-1] = str(int(weights[-1]) + remainder)
            measurement = ""
        else:
            # Auto-suggest from criteria templates
            crit_result = search_domain(description, "criteria", 1)
            crit_results = crit_result.get("results", [])
            if crit_results:
                template = crit_results[0]
                criteria_items = [c.strip() for c in template.get("Criteria", "").split(",")]
                weights = [w.strip() for w in template.get("Default Weights", "").split(",")]
                measurement = template.get("Measurement Guidance", "")
            else:
                criteria_items = ["Quality", "Cost", "Feasibility", "Strategic Fit", "Risk"]
                weights = ["25", "20", "20", "20", "15"]
                measurement = ""

        # Build matrix output
        out = []
        out.append("=== COMPARISON MATRIX ===")
        out.append(f"Decision: {description}")
        out.append("")

        # Header row
        header = "              "
        for i, c in enumerate(criteria_items):
            w = weights[i] if i < len(weights) else "?"
            col = f"| {c} (w:{w}) "
            header += col.ljust(22)
        header += "| TOTAL"
        out.append(header)
        out.append("-" * len(header))

        # Option rows
        for opt in options:
            row = f"{opt[:14]}".ljust(14)
            for _ in criteria_items:
                row += f"|     ? / 5         "
            row += "|   ?"
            out.append(row)

        out.append("")
        out.append("Scoring Guide:")
        if measurement:
            # Split measurement into per-criterion guidance
            for line in measurement.split(". "):
                line = line.strip()
                if line:
                    out.append(f"  {line}.")
        else:
            for c in criteria_items:
                out.append(f"  {c}: 5=excellent, 4=good, 3=adequate, 2=poor, 1=unacceptable")

        out.append("")
        out.append("Instructions: Fill in scores (1-5) for each cell, then calculate weighted totals.")
        out.append(f"Formula: Total = sum(score_i * weight_i / 100) for each option")

        return "\n".join(out)

    def _parse_options(self, description: str) -> list:
        """Extract options from a description like 'Compare X vs Y vs Z for CRM' or 'A or B'."""
        # Try "vs" separator
        if " vs " in description.lower():
            parts = re.split(r'\s+vs\.?\s+', description, flags=re.IGNORECASE)
            # Clean up first part (remove "Compare" etc.)
            parts[0] = re.sub(r'^(?:compare|choose|pick|select|evaluate)\s+', '', parts[0], flags=re.IGNORECASE).strip()
            # Clean up last part (remove trailing "for X" context)
            parts[-1] = re.sub(r'\s+(?:for|as|in|to)\s+.+$', '', parts[-1], flags=re.IGNORECASE).strip()
            return [p.strip() for p in parts if p.strip()]

        # Try "or" separator
        if " or " in description.lower():
            parts = re.split(r'\s+or\s+', description, flags=re.IGNORECASE)
            parts[0] = re.sub(r'^(?:compare|choose|pick|select|evaluate)\s+', '', parts[0], flags=re.IGNORECASE).strip()
            parts[-1] = re.sub(r'\s+(?:for|as|in|to)\s+.+$', '', parts[-1], flags=re.IGNORECASE).strip()
            return [p.strip() for p in parts if p.strip()]

        # Try comma-separated
        if "," in description:
            parts = description.split(",")
            parts[0] = re.sub(r'^(?:compare|choose|pick|select|evaluate)\s+', '', parts[0], flags=re.IGNORECASE).strip()
            return [p.strip() for p in parts if p.strip()]

        return []


# ============ PUBLIC API ============
def generate_decision_plan(query: str, project_name: str = None, output_format: str = "ascii",
                           persist: bool = False, output_dir: str = None) -> str:
    """Generate a comprehensive decision-making plan.

    Args:
        query: Decision description
        project_name: Optional project name
        output_format: 'ascii' or 'markdown'
        persist: Whether to save to file
        output_dir: Output directory for persistence

    Returns:
        Formatted decision plan
    """
    advisor = DecisionAdvisor(query)
    plan = advisor.generate(project_name)

    if output_format == "markdown":
        result = advisor.format_markdown(plan)
    else:
        result = advisor.format_ascii_box(plan)

    if persist:
        path = advisor.persist_plan(plan, output_dir)
        result += f"\n\nPlan saved to: {path}"

    return result
