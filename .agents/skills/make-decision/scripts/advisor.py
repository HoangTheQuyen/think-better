#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Advisor - decision plans, weighted comparison matrices and the
step-by-step workspace.

Usage:
    from advisor import DecisionAdvisor
    advisor = DecisionAdvisor("React or Vue for our new project?")
    plan = advisor.generate(depth="standard")
    print(advisor.format_markdown(plan))
"""

import json
import re
import unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from core import (default_output_dir, display_width, find_row, fold, load_csv, match_tokens, pad_display,
                  query_grams, rank_by_signals, save_docs, search_domain, slugify, wrap_display)
import journal
import workspace

# ============ DEPTH CONFIGURATION ============
# How much each depth shows; the section layout per depth is in _sections().
DEPTH_CONFIG = {
    "quick": {"alternatives": 0, "analysis": 0, "biases": 2, "facilitation": 0, "criteria": 3},
    "standard": {"alternatives": 2, "analysis": 2, "biases": 3, "facilitation": 2, "criteria": 5},
    "deep": {"alternatives": 4, "analysis": 3, "biases": 5, "facilitation": 2, "criteria": 5},
    "executive": {"alternatives": 3, "analysis": 3, "biases": 4, "facilitation": 2, "criteria": 5},
}
VALID_DEPTHS = list(DEPTH_CONFIG.keys())

DEFAULT_TYPE = "Multi-Option Selection"
DEFAULT_CRITERIA = "General Decision"
# Spelled-out options count like this many keyword points for Binary / Multi-Option
OPTION_WEIGHT = 2
# On equal scores the more specific situation wins
TYPE_PRIORITY = ["Time-Pressured Decision", "Group / Stakeholder Decision", "Decision Under Uncertainty",
                 "Resource Allocation", "Strategic Direction", "Binary Choice", "Multi-Option Selection",
                 "Operational / Tactical"]

# ============ OPTIONS ============
# Patterns are written without accents: they run on a folded copy of the text
# (same length, see _fold_keep) so 'nên chọn' and 'nen chon' both match, and
# the options are cut from the original text with its accents.
_SEPARATORS = r"or|vs\.?|versus|hay la|hay|hoac la|hoac|so voi"
_OPENERS = re.compile(
    r"\b(?:(?:should|shall|do|can) (?:we|i|you|they)(?: (?:use|go with|choose|pick|select))?"
    r"|is it better to|would it be better to"
    r"|whether(?: to| we should| i should)?|torn between|between|decide(?: between)?|deciding(?: between)?"
    r"|choos(?:e|ing)(?: between)?|pick(?:ing)?(?: between)?|select|compare|comparing"
    r"|co nen dung|co nen chon|co nen|nen chon|nen dung|nen su dung|nen|chon giua|lua chon giua|phan van giua"
    r"|phan van|chon|giua|so sanh"
    r"|quyet dinh)\b", re.I)
_TRAILING_CONTEXT = re.compile(
    r"\s+(?:for|because|since|given|so that|after|before|cho|de|vi|sau khi|truoc khi|trong khi|khi|neu)\s+.*$",
    re.I)
_TRAILING_FILLER = re.compile(r"\s+(?:the nao|nhu the nao|ra sao|khong|nhi|nhe|then|instead)$", re.I)
_YES_NO = re.compile(r"^(?P<x>.+?)\s+(?:hay|or|hoac)\s+(?:khong|not|chua|no)$", re.I)
_VIETNAMESE = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")


def is_vietnamese(text: str) -> bool:
    return bool(_VIETNAMESE.search(str(text).lower()))


@lru_cache(maxsize=None)
def _fold_char(ch: str) -> str:
    base = fold(ch).lower()
    if len(base) == 1:
        return base
    low = ch.lower()
    return low if len(low) == 1 else ch


@lru_cache(maxsize=512)
def _fold_keep(text: str) -> str:
    """Lowercase accent-folded copy of text with the same length (one character per character)."""
    if text.isascii():
        return text.lower()
    return "".join(_fold_char(ch) for ch in text)


def _split(text: str, pattern) -> list:
    """Split the original text where pattern matches its folded copy."""
    folded, pieces, start = _fold_keep(text), [], 0
    for m in pattern.finditer(folded):
        pieces.append(text[start:m.start()])
        start = m.end()
    return pieces + [text[start:]]


def _sub_end(text: str, pattern) -> str:
    """Text with the part matching pattern (anchored at the end, on the folded copy) removed."""
    m = pattern.search(_fold_keep(text))
    return text[:m.start()] if m else text


def _not_option(text: str) -> str:
    return "Không (giữ nguyên hiện trạng)" if is_vietnamese(text) else "Not (keep things as they are)"


def _strip_opener(text: str, limit: int = None) -> tuple:
    """(text after the last question opener before limit, the opener) - 'should we', 'nên chọn', 'between'."""
    folded = _fold_keep(text)
    last = None
    for m in _OPENERS.finditer(folded[: len(text) if limit is None else limit]):
        last = m
    if not last or not text[last.end():].strip():
        return text, ""
    return text[last.end():].strip(), last.group(0).lower()


def _shape(word: str) -> str:
    if re.search(r"\d", word):
        return "number"
    if len(word) == 1 and word.isalpha():
        return "letter"
    return "word"


# Openers after which "A, B and C" lists the options ("choose between", "should we use", "nên chọn")
_CHOICE_OPENER = re.compile(r"between|choos|pick|select|compar|\buse\b|go with|chon|giua|so sanh|dung")
_LIST_ITEM = re.compile(r"^\s*(?:\d{1,2}[.)]|[-*•+]|[a-hA-H][.)])\s+(?P<item>\S.*?)\s*$")


def _list_options(lines: list) -> list:
    """The items of the first bulleted or numbered list ('1. AWS', '- GCP'), when they read like options."""
    items, started = [], False
    for line in lines:
        m = _LIST_ITEM.match(line)
        if m:
            started = True
            items.append(m.group("item").replace("**", "").strip().rstrip(".;,").strip())
        elif started and line.strip():
            break
    items = [i for i in items if i]
    if not 2 <= len(items) <= 8 or any(len(i.split()) > 8 for i in items):
        return []
    return list(dict.fromkeys(items))


def _options_in(sentence: str) -> list:
    s = sentence.strip().rstrip("?!.;:").strip()
    sep = re.compile(r"\s+(?:%s)\s+" % _SEPARATORS, re.I)
    listed = False
    # "Which CRM: Salesforce, HubSpot or Pipedrive" - the options follow the colon
    if ":" in s:
        head, tail = s.split(":", 1)
        if (sep.search(_fold_keep(tail)) or "," in tail) and len(head.split()) <= 12:
            s = tail.strip()
            listed = True
    # "renew it or not", "có ký hợp đồng hay không"
    yes_no = _YES_NO.match(_fold_keep(s))
    if yes_no:
        x, _ = _strip_opener(s[: yes_no.end("x")])
        x = _split(x, re.compile(r"\bco\b"))[-1].strip() or x
        return [x, _not_option(sentence)] if x else []

    first = sep.search(_fold_keep(s))
    s, opener = _strip_opener(s, first.start() if first else None)
    extra = []
    if opener.endswith(("between", "giua")):
        extra.append("and|va")
    if opener in ("compare", "comparing", "so sanh"):
        extra.append("with|voi|and|va")
    split = re.compile(r"\s+(?:%s)\s+" % "|".join([_SEPARATORS] + extra), re.I)
    chunks = [c for c in re.split(r"\s*[,;]\s*", s) if c.strip()]
    # "Salesforce, HubSpot and Pipedrive", "MISA, Fast và Bravo": the last item comes after and/và
    choice = listed or _CHOICE_OPENER.search(opener) or re.search(r"\b(?:which|nao)\b", _fold_keep(sentence))
    if len(chunks) >= 2 and choice:
        tail = _split(chunks[-1], re.compile(r"\s+(?:and|va|&)\s+", re.I))
        if len(tail) == 2 and all(t.strip() for t in tail):
            chunks = chunks[:-1] + tail
    pieces = [p.strip() for c in chunks for p in _split(c, split)]
    pieces = [_split(p, re.compile(r"^(?:or|and|vs\.?|versus|hay|hoac|va)\s+", re.I))[-1].strip() for p in pieces]
    pieces = [p for p in pieces if p]
    if len(pieces) < 2:
        return []
    if not split.search(_fold_keep(s)) and any(len(p.split()) > 3 for p in pieces):
        return []  # a comma list in prose ("marketing, sales and R&D"), not options
    last = _sub_end(_sub_end(pieces[-1], _TRAILING_CONTEXT), _TRAILING_FILLER).strip()
    pieces[-1] = last or pieces[-1]
    # "set the price at $29 or $49" -> "$29", "$49"; "đối tác A hay B" -> "A", "B"
    first_words, last_words = pieces[0].split(), pieces[-1].split()
    if (len(pieces) == 2 and len(first_words) - len(last_words) >= 3 and len(last_words) <= 2
            and _shape(first_words[-1]) == _shape(last_words[-1]) != "word"):
        pieces[0] = " ".join(first_words[-len(last_words):])
    options, seen = [], set()
    for p in pieces:
        p = p.strip(" \"'`")
        key = fold(p).lower()
        if p and key not in seen:
            seen.add(key)
            options.append(p)
    if len(options) < 2 or any(len(o.split()) > 8 for o in options):
        return []
    return options[:8]


def parse_options(text: str) -> list:
    """The alternatives a request spells out, in order; [] when it names none.

    'React or Vue for our new project?' -> ['React', 'Vue'];
    'Which CRM: Salesforce, HubSpot or Pipedrive' -> ['Salesforce', 'HubSpot', 'Pipedrive'];
    'nên chọn React hay Vue' -> ['React', 'Vue']; 'giữa A, B và C' -> ['A', 'B', 'C'].
    """
    text = unicodedata.normalize("NFC", str(text or ""))
    text = re.sub(r"\b(vs|versus)\.", r"\1", text, flags=re.I)
    lines = text.splitlines()
    # Options spelled out in prose win; then a bulleted or numbered list ("1. AWS\n2. GCP")
    prose = "\n".join(line for line in lines if not _LIST_ITEM.match(line))
    for part in (prose, None, text):
        if part is None:
            options = _list_options(lines)
            if options:
                return options
            continue
        for sentence in re.split(r"(?<=[?!])\s+|\.\s+|\n+", part):
            options = _options_in(sentence)
            if options:
                return options
    return []


def _mask_options(text: str, options: list) -> str:
    """text with option names that look like proper names ('Fast', 'MISA') blanked out, so a product
    called 'Fast' is never read as time pressure."""
    for option in options:
        words = option.split()
        if words and len(words) <= 3 and all(not w[0].isalpha() or w[0].isupper() for w in words):
            text = re.sub(r"(?<!\w)%s(?!\w)" % re.escape(option), " , ", text)
    return text


# ============ SMALL HELPERS ============
def split_names(cell: str) -> list:
    return [n.strip() for n in str(cell or "").split(",") if n.strip()]


def criteria_items(row: dict, limit: int = 5) -> list:
    """[{'name', 'weight', 'guide'}] of a criteria template row, heaviest first, weights summing to 100."""
    names = split_names(row.get("Criteria", ""))
    weights = []
    for w in split_names(row.get("Default Weights", "")):
        try:
            weights.append(float(w))
        except ValueError:
            weights.append(0.0)
    weights += [0.0] * (len(names) - len(weights))
    guides = []
    for part in re.split(r"(?<=\.)\s+(?=[A-Z][\w -]*:)", row.get("Measurement Guidance", "")):
        if ":" in part:
            key, text = part.split(":", 1)
            guides.append((key.strip().lower(), text.strip()))
    items = []
    for n, (name, weight) in enumerate(zip(names, weights)):
        if len(guides) == len(names):  # one guide per criterion, in the same order
            guide = guides[n][1]
        else:
            words = name.lower().split()
            guide = next((t for k, t in guides if k.split()[0] in words or k in name.lower()), "")
        items.append({"name": name, "weight": weight, "guide": guide})
    items = sorted(items, key=lambda x: -x["weight"])[:limit]
    total = sum(i["weight"] for i in items) or 1
    for item in items:
        item["weight"] = round(item["weight"] * 100 / total)
    drift = 100 - sum(i["weight"] for i in items)
    if items and drift:
        items[0]["weight"] += drift
    return items


def _numbered_steps(text: str) -> list:
    return [s.strip() for s in re.split(r"\s*\d+\.\s+", str(text or "")) if s.strip()]


def _first_line(text: str, limit: int = 60) -> str:
    line = next((ln.strip() for ln in str(text).splitlines() if ln.strip()), "")
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def _sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", str(text or "")) if s.strip()]


def _num(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".") if value != int(value) else str(int(value))


# ============ REVERSIBILITY ============
ONE_WAY = ["acquire", "acquisition", "merger", "sign the contract", "contract", "hire", "layoff", "buy a house",
           "buy a home", "mortgage", "relocate", "emigrate", "quit", "resign", "migrate", "migration", "rewrite",
           "pivot", "irreversible", "long-term", "restructure", "mua nhà", "nghỉ việc", "ký hợp đồng", "hợp đồng",
           "sáp nhập", "thâu tóm", "tái cấu trúc", "định cư", "cắt giảm", "du học", "tuyển"]
TWO_WAY = ["experiment", "pilot", "trial", "a/b", "prototype", "reversible", "try", "sprint", "tool",
           "feature flag", "test", "thử", "thí điểm", "dùng thử", "thử nghiệm", "tạm thời"]


def assess_reversibility(query: str, type_name: str) -> dict:
    """One-way door (hard to undo) or two-way door, from the request's words and the decision type."""
    grams, folded = query_grams(query)

    def hits(words):
        return [w for w in words if tuple(match_tokens(w, folded)) in grams]

    one, two = hits(ONE_WAY), hits(TWO_WAY)
    score = len(one) - len(two) + {"Strategic Direction": 1, "Operational / Tactical": -1}.get(type_name, 0)
    if score > 0:
        return {"door": "one-way", "signals": one,
                "label": "Likely a one-way door: hard or costly to undo",
                "advice": "Slow down: run the pre-mortem, test the riskiest assumption first and get the "
                          "decision owner's sign-off. Agree on kill criteria before committing."}
    if score < 0:
        return {"door": "two-way", "signals": two,
                "label": "Likely a two-way door: cheap to reverse",
                "advice": "Decide fast with the best information you have, set a review date and "
                          "iterate. Do not over-analyze."}
    return {"door": "unclear", "signals": [],
            "label": "Reversibility unclear",
            "advice": "Ask: what would it cost to undo this in 6 months? Cheap means decide fast and review; "
                      "expensive means treat it as a one-way door."}


# ============ DECISION ADVISOR ============
class DecisionAdvisor:
    """Generates decision plans, comparison matrices and step-by-step workspaces."""

    def __init__(self, query: str = "", search_fn=None, decision_type: str = None):
        self.query = unicodedata.normalize("NFC", str(query or "")).strip()
        self.search_fn = search_fn
        self.decision_type = decision_type

    @staticmethod
    def decision_type_names() -> list:
        """All decision types, for --type choices."""
        return [row["Decision Type"] for row in load_csv("types")]

    # ---- Classification ----
    def classify(self) -> dict:
        """{'row', 'source', 'matched'}: explicit --type, else keyword signals plus spelled-out options.

        source is 'explicit', 'keywords' or 'default' (nothing matched: say so and suggest --type).

        Raises:
            ValueError: if an explicit decision type is not a known value.
        """
        rows = load_csv("types")
        if self.decision_type:
            wanted = self.decision_type.strip().lower()
            for row in rows:
                if row["Decision Type"].lower() == wanted:
                    return {"row": row, "source": "explicit", "matched": []}
            raise ValueError(f"unknown decision type {self.decision_type!r}; choose one of: "
                             + ", ".join(r["Decision Type"] for r in rows))

        options = parse_options(self.query)
        text = _mask_options(self.query, options)
        scores = {row["Decision Type"]: [score, row, list(matched)]
                  for score, row, matched in rank_by_signals(text, "types")}
        if len(options) >= 2:
            name = "Binary Choice" if len(options) == 2 else "Multi-Option Selection"
            if name in scores:
                scores[name][0] += OPTION_WEIGHT
                scores[name][2].append(f"{len(options)} options")
        order = {name: i for i, name in enumerate(TYPE_PRIORITY)}
        best = max(scores.values(), key=lambda v: (v[0], -order.get(v[1]["Decision Type"], 99)))
        if best[0] > 0:
            return {"row": best[1], "source": "keywords", "matched": best[2]}
        default = next(r for r in rows if r["Decision Type"] == DEFAULT_TYPE)
        return {"row": default, "source": "default", "matched": []}

    def choose_criteria(self) -> dict:
        """{'row', 'source', 'matched'}: the criteria template whose signals the request matches best,
        else the General Decision template (source 'default')."""
        ranked = rank_by_signals(self.query, "criteria")
        score, row, matched = ranked[0]
        if score > 0:
            return {"row": row, "source": "keywords", "matched": matched}
        general = find_row("criteria", DEFAULT_CRITERIA)
        return {"row": general, "source": "default", "matched": []}

    # ---- Selection by name, search as the fallback ----
    def _named_rows(self, domain: str, names: list, limit: int, query_fallback: bool = True) -> list:
        """Rows named in `names` (in order), topped up with search hits for the request."""
        rows, seen = [], set()
        for name in names:
            row = find_row(domain, name)
            key = next(iter(row.values()), "") if row else ""
            if row and key not in seen:
                seen.add(key)
                rows.append(row)
        if query_fallback and len(rows) < limit:
            for row in search_domain(fold(self.query), domain, limit + len(rows)).get("results", []):
                key = next(iter(row.values()), "")
                if key not in seen:
                    seen.add(key)
                    full = find_row(domain, key) or row
                    rows.append(full)
        return rows[:limit]

    # ---- Plan Generation ----
    def generate(self, project_name: str = None, depth: str = "standard") -> dict:
        """Build the decision plan for this request at the given depth (quick/standard/deep/executive)."""
        if depth not in DEPTH_CONFIG:
            raise ValueError(f"unknown depth {depth!r}; choose one of: {', '.join(VALID_DEPTHS)}")
        cfg = DEPTH_CONFIG[depth]
        found = self.classify()
        dtype, type_name = found["row"], found["row"]["Decision Type"]
        crit = self.choose_criteria()
        options = parse_options(self.query)

        frameworks = self._named_rows("frameworks", split_names(dtype.get("Recommended Frameworks")),
                                      1 + max(cfg["alternatives"], 1))
        best = frameworks[0] if frameworks else {}
        analysis = self._named_rows("analysis", split_names(dtype.get("Analysis Methods")), cfg["analysis"])
        # The type's biases and the domain's, alternating, then whatever the request mentions
        type_biases, domain_biases = split_names(dtype.get("Key Biases")), split_names(crit["row"].get("Key Biases"))
        bias_names = []
        for i in range(max(len(type_biases), len(domain_biases))):
            bias_names += type_biases[i:i + 1] + domain_biases[i:i + 1]
        biases = self._named_rows("biases", bias_names, cfg["biases"])
        show_facilitation = cfg["facilitation"] and (depth != "standard" or type_name.startswith("Group"))
        facilitation = (self._named_rows("facilitation", split_names(dtype.get("Facilitation")),
                                         cfg["facilitation"]) if show_facilitation else [])
        items = criteria_items(crit["row"], cfg["criteria"])

        hint = ""
        if found["source"] == "default":
            hint = ("No decision type matched clearly. Re-run with `--type` ("
                    + ", ".join(self.decision_type_names()) + ").")
        criteria_note = ""
        if crit["source"] == "default":
            criteria_note = ("No domain template matched: these general criteria fit most decisions. "
                             "Replace them with what matters here (at most 5).")

        return {
            "request": self.query,
            "depth": depth,
            "project_name": project_name or _first_line(self.query) or "decision",
            "options": options,
            "classification_hint": hint,
            "decision_type": {
                "name": type_name,
                "source": found["source"],
                "matched": found["matched"],
                "characteristics": dtype.get("Characteristics", ""),
                "recommended_frameworks": dtype.get("Recommended Frameworks", ""),
                "analysis_methods": dtype.get("Analysis Methods", ""),
                "key_biases": dtype.get("Key Biases", ""),
                "common_pitfalls": dtype.get("Common Pitfalls", ""),
                "warning_signs": dtype.get("Warning Signs", ""),
            },
            "framework": {
                "name": best.get("Framework", "Weighted Criteria Matrix"),
                "category": best.get("Category", ""),
                "description": best.get("Description", ""),
                "steps": best.get("Steps", ""),
                "strengths": best.get("Strengths", ""),
                "limitations": best.get("Limitations", ""),
                "complexity": best.get("Complexity", "Medium"),
                "alternatives": [f.get("Framework", "") for f in frameworks[1:1 + cfg["alternatives"]]],
                "alternative_details": [{"name": f.get("Framework", ""), "description": f.get("Description", ""),
                                         "when": f.get("When to Use", "")}
                                        for f in frameworks[1:1 + cfg["alternatives"]]],
            },
            "criteria": {
                "domain": crit["row"].get("Domain", ""),
                "source": crit["source"],
                "matched": crit["matched"],
                "note": criteria_note,
                "items": items,
                "criteria_list": ", ".join(i["name"] for i in items),
                "weights": ", ".join(str(i["weight"]) for i in items),
                "measurement": crit["row"].get("Measurement Guidance", ""),
                "mistakes": crit["row"].get("Common Mistakes", ""),
            },
            "analysis_techniques": [
                {"technique": a.get("Technique", ""), "when": a.get("When to Use", ""),
                 "how": a.get("How to Apply", ""), "output": a.get("Output Format", "")}
                for a in analysis
            ],
            "bias_warnings": [
                {"bias": b.get("Bias", ""), "impact": b.get("Impact on Decisions", ""),
                 "detect": b.get("How to Detect", ""), "debiasing": b.get("Debiasing Strategy", ""),
                 "severity": b.get("Severity", "Medium")}
                for b in biases
            ],
            "facilitation": [
                {"technique": f.get("Technique", ""), "when": f.get("When to Use", ""),
                 "group_size": f.get("Group Size", ""), "time": f.get("Time Required", "")}
                for f in facilitation
            ],
            "reversibility": assess_reversibility(self.query, type_name),
            "anti_patterns": dtype.get("Common Pitfalls", ""),
        }

    # ---- Section builders (one layout per depth) ----
    @staticmethod
    def _header(plan: dict) -> list:
        dt = plan["decision_type"]
        lines = []
        request = [ln for ln in plan.get("request", "").splitlines() if ln.strip()]
        if len(request) == 1:
            lines.append(f"**Request:** {request[0]}")
        elif request:
            lines += ["**Request:**"] + [f"> {ln}" for ln in request]
        why = {"explicit": "set with --type", "default": "no clear match"}.get(
            dt.get("source"), "matched: " + ", ".join(dt.get("matched", [])))
        lines.append(f"**Decision type:** {dt['name']} ({why})")
        if plan.get("classification_hint"):
            lines.append(f"> {plan['classification_hint']}")
        options = plan.get("options") or []
        if options:
            lines.append("**Options:** " + " | ".join(options))
        else:
            lines.append("**Options:** not spelled out yet. List 2-5 real alternatives (include "
                         "\"do nothing\" or \"wait\") before scoring.")
        return lines

    @staticmethod
    def _criteria_table(plan: dict, guide: bool = True) -> list:
        items = plan["criteria"]["items"]
        if guide:
            lines = ["| Criterion | Weight | What a 5 looks like |", "|---|---|---|"]
            lines += [f"| {i['name']} | {i['weight']} | {i['guide']} |" for i in items]
        else:
            lines = ["| Criterion | Weight |", "|---|---|"]
            lines += [f"| {i['name']} | {i['weight']} |" for i in items]
        return lines

    @staticmethod
    def _matrix_hint(plan: dict) -> list:
        spec = ",".join(f"{i['name']}:{i['weight']}" for i in plan["criteria"]["items"])
        names = plan.get("options") or ["A", "B"]
        n = len(plan["criteria"]["items"])
        example = ";".join(f"{o}:{','.join(['?'] * n)}" for o in names[:3])
        return ["Score every option 1-5 on every criterion, then let the script total them, name the winner "
                "and find the smallest weight change that flips it:",
                f"`search.py --stdin --matrix -c \"{spec}\" --scores \"{example}\"` "
                "(the options go on stdin, as with --plan)."]

    def _sections(self, plan: dict) -> tuple:
        """(title, [(heading, lines)]) for the plan's depth."""
        depth = plan.get("depth", "standard")
        project = plan.get("project_name", "Decision")
        dt, fw, crit = plan["decision_type"], plan["framework"], plan["criteria"]
        rev = plan["reversibility"]
        steps = _numbered_steps(fw.get("steps"))
        biases, analysis, facil = plan["bias_warnings"], plan["analysis_techniques"], plan["facilitation"]
        head = self._header(plan)

        if depth == "quick":
            return f"Quick Decision: {project}", [
                ("", head),
                (f"Do This Now: {fw['name']}", [f"{i}. {s}" for i, s in enumerate(steps[:5], 1)]),
                ("Score Each Option On", [f"- **{i['name']}** (weight {i['weight']}): {i['guide']}"
                                          for i in crit["items"]]),
                ("Watch For", [f"- **{b['bias']}**: {b['debiasing']}" for b in biases]),
                ("Reversibility", [f"**{rev['label']}.** {rev['advice']}",
                                   "If this is a one-way door, re-run with `--depth deep`."]),
            ]

        criteria_lines = [f"> {crit['note']}"] if crit.get("note") else []
        criteria_heading = f"Evaluation Criteria ({crit['domain']})"
        bias_lines = []
        for b in biases:
            bias_lines.append(f"- **{b['bias']}** [{b['severity']}]: {b['impact']}")
            if depth == "deep" and b.get("detect"):
                bias_lines.append(f"  - *Detect:* {b['detect']}")
            bias_lines.append(f"  - *Remedy:* {b['debiasing']}")
        facil_lines = []
        for f in facil:
            facil_lines.append(f"- **{f['technique']}** ({f['group_size']} people, {f['time']}): {f['when']}")
        checklist = [f"- [ ] {c}" for c in (
            "Problem clearly defined and bounded", "Options exhaustively listed (MECE)",
            "Criteria and weights agreed BEFORE scoring options", "Key assumptions identified and tested",
            "Sensitivity checked: what weight change flips the winner?", "Bias check completed",
            "Stakeholders aligned on criteria and process", "Decision documented (create a journal entry)")]

        if depth == "executive":
            pitfalls = _sentences(plan.get("anti_patterns"))[:2]
            risks = ["| Risk | Why it matters | Mitigation |", "|---|---|---|"]
            for p in pitfalls:
                name, _, why = p.partition("—")
                why = why.strip() or f"A common pitfall in {dt['name']} decisions."
                risks.append(f"| {name.strip(' .')} | {why} | Name an owner and an early warning signal |")
            for b in [b for b in biases if b["severity"] == "High"][:2] or biases[:1]:
                risks.append(f"| {b['bias']} | {b['impact']} | {b['debiasing']} |")
            options = plan.get("options") or []
            return f"Executive Decision Brief: {project}", [
                ("", head),
                ("Recommendation", [
                    "Lead with the answer. Fill this in once the options are scored:",
                    "- **Recommendation:** _one sentence naming the option_",
                    "- **Why:** _three reasons, each tied to a criterion below_",
                    "- **Confidence:** _% and what would raise it_",
                    "- **Ask:** _the approval, budget or decision needed from the reader_"]),
                ("Decision Needed", [
                    f"- **Decision:** {_first_line(plan.get('request', ''), 140)}",
                    "- **Options:** " + (" | ".join(options) if options else "_to be listed (include do nothing)_"),
                    "- **Decision owner:** _name_  |  **Needed by:** _date_",
                    f"- **Decision type:** {dt['name']}",
                    f"- **Reversibility:** {rev['label']}"]),
                ("Key Risks", risks),
                ("Reversibility", [f"**{rev['label']}.** {rev['advice']}",
                                   "- **Cost to undo in 6 months:** _estimate_",
                                   "- **Kill criteria:** _the signals that would make us reverse course_"]),
                ("Criteria and Weights", self._criteria_table(plan, guide=False) + criteria_lines),
                ("What Would Change the Call", [
                    "- **Flip point:** the smallest weight change that flips the winner (`--matrix ... --scores`)",
                    "- **Critical assumptions:** _the two assumptions that, if false, reverse the recommendation_",
                    "- **Information that would help most:** _and what it costs to get it_"]),
                (f"Approach: {fw['name']}", [f"{i}. {s}" for i, s in enumerate(steps, 1)]
                 + ([f"Alternatives: {', '.join(fw['alternatives'])}"] if fw.get("alternatives") else [])),
                ("Bias Safeguards", [f"- **{b['bias']}**: {b['debiasing']}" for b in biases]),
                ("Analysis to Commission", [f"- **{a['technique']}**: {a['when']}" for a in analysis]),
                ("Facilitation", facil_lines),
            ]

        # standard and deep
        fw_lines = [f"**{fw['name']}** ({fw['complexity']} complexity): {fw['description']}"]
        fw_lines += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
        if depth == "deep":
            if fw.get("strengths"):
                fw_lines.append(f"- **Strengths:** {fw['strengths']}")
            if fw.get("limitations"):
                fw_lines.append(f"- **Limitations:** {fw['limitations']}")
            for alt in fw.get("alternative_details", []):
                fw_lines.append(f"- *Alternative:* **{alt['name']}**: {alt['when']}")
        elif fw.get("alternatives"):
            fw_lines.append(f"- **Alternatives:** {', '.join(fw['alternatives'])}")

        criteria_lines = criteria_lines + self._criteria_table(plan)
        if crit.get("mistakes"):
            criteria_lines.append(f"\n**Common mistakes:** {crit['mistakes']}")
        analysis_lines = []
        for a in analysis:
            analysis_lines.append(f"- **{a['technique']}**: {a['when']}")
            if depth == "deep" and a.get("how"):
                analysis_lines.append(f"  - *How:* {a['how']}")

        sections = [
            ("", head),
            ("Decision Type", [f"- **Type:** {dt['name']}", f"- **Characteristics:** {dt['characteristics']}"]
             + ([f"- **Watch for:** {dt['warning_signs']}"] if dt.get("warning_signs") else [])),
            ("Recommended Framework", fw_lines),
            (criteria_heading, criteria_lines),
            ("Analysis Techniques", analysis_lines),
            ("Bias Warnings", bias_lines),
            ("Group Facilitation", facil_lines),
            ("Score the Options", self._matrix_hint(plan)),
        ]
        if depth == "deep":
            subject = " vs ".join(plan["options"]) if plan.get("options") else "this decision"
            sections += [
                ("Reversibility", [f"**{rev['label']}.** {rev['advice']}"]),
                ("Pre-Mortem", [
                    f"Imagine it is 12 months later and {subject} turned out badly.",
                    "1. Write down the three most likely reasons it failed.",
                    "2. For each, name the early warning signal you would see first.",
                    "3. Turn the signals into kill criteria: the point at which you stop or reverse."]),
                ("Sensitivity", [
                    "- Which single criterion weight, if changed, flips the winner? (`--matrix ... --scores` reports it)",
                    "- Which score are you least sure of? Re-score it at its plausible worst and best.",
                    "- If the winner flips under a small change, gather information on that criterion first."]),
                ("Information to Gather", [f"- **{i['name']}**: what evidence would justify a 5 ({i['guide']})?"
                                           for i in crit["items"]]),
            ]
        sections += [
            ("Anti-Patterns to Avoid", [plan.get("anti_patterns", "")] if plan.get("anti_patterns") else []),
            ("Decision Checklist", checklist),
        ]
        title = "Deep Decision Analysis" if depth == "deep" else "Decision-Making Plan"
        return f"{title}: {project}", sections

    # ---- Formatters ----
    def format_markdown(self, plan: dict) -> str:
        """The plan as Markdown; what it contains depends on plan['depth']."""
        title, sections = self._sections(plan)
        out = [f"# {title}", ""]
        for heading, lines in sections:
            if not lines:
                continue
            if heading:
                out.append(f"## {heading}")
            out += lines
            out.append("")
        return "\n".join(out)

    def format_ascii_box(self, plan: dict) -> str:
        """The plan in a terminal box (same content as Markdown, without the markup)."""
        width = 90
        title, sections = self._sections(plan)
        out = ["+" + "=" * (width - 1) + "+"]

        def add(text: str = "", indent: str = "  "):
            if not text.strip():
                out.append("|" + " " * width + "|")
                return
            # Columns, not characters: accents (even typed as combining marks) and wide characters
            for line in wrap_display(text, width - 2, indent + " ", indent + "    "):
                out.append("|" + pad_display(line, width) + "|")

        add(title.upper())
        out.append("+" + "=" * (width - 1) + "+")
        for heading, lines in sections:
            if not lines:
                continue
            if heading:
                out.append("+" + "-" * (width - 1) + "+")
                add(heading.upper())
            for line in lines:
                plain = re.sub(r"\*\*|`|(?<![\w*])[*_](?=\S)|(?<=\S)[*_](?![\w*])", "", line).replace("\n", " ")
                add(plain, "    " if heading else "  ")
            add()
        out.append("+" + "=" * (width - 1) + "+")
        return "\n".join(out)

    # ---- Persisted plans ----
    @staticmethod
    def _plan_dir(plan: dict, output_dir: str = None) -> Path:
        base = Path(output_dir) if output_dir else default_output_dir()
        plan_dir = base / workspace.PLANS_DIR / slugify(plan.get("project_name", "decision"))
        plan_dir.mkdir(parents=True, exist_ok=True)
        return plan_dir

    def persist_plan(self, plan: dict, output_dir: str = None, force: bool = False) -> tuple:
        """Save the plan as PLAN.md; returns (path, written). An existing PLAN.md is kept unless force."""
        plan_dir = self._plan_dir(plan, output_dir)
        workspace.prepare_folder(plan_dir, plan.get("request", ""), plan["decision_type"]["name"], ["PLAN.md"],
                                 force)
        content = self.format_markdown(plan)
        content += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        written, _ = save_docs(plan_dir, {"PLAN.md": content}, force)
        return str(plan_dir / "PLAN.md"), bool(written)

    def step_docs(self, plan: dict) -> dict:
        """{file name: content} of the step-by-step workspace."""
        project = plan.get("project_name", "Decision")
        dt, fw, crit = plan["decision_type"], plan["framework"], plan["criteria"]
        rev = plan["reversibility"]
        options = plan.get("options") or []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        request_quote = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in plan.get("request", "").splitlines())
        docs = {}

        rows = "\n".join(f"| {s['number']}. {s['label']} | [{s['file']}](./{s['file']}) | {workspace.UNTICKED} |"
                         for s in workspace.STEPS)
        docs[workspace.OVERVIEW] = f"""# Decision Workspace: {project}

**Request:** {_first_line(plan.get('request', ''), 200)}
**Decision type:** {dt['name']}  |  **Criteria:** {crit['domain']}  |  **Depth:** {plan.get('depth', 'standard')}
**Options:** {' | '.join(options) if options else '_not listed yet_'}
**Created:** {ts}

Work the steps in order. When a step is done, tick it (`search.py --done <step> -p {slugify(project)}`)
or write ☑ in its row; `search.py --status -p {slugify(project)}` shows where you are.

| Step | File | Done? |
|---|---|---|
{rows}

Also here: [BIAS-WARNINGS.md](./BIAS-WARNINGS.md) (biases to check) and
[DECISION-LOG.md](./DECISION-LOG.md) (decisions and revisits).
"""

        docs["01-DECISION-TYPE.md"] = f"""# Step 1: Classify the Decision

## The Request
{request_quote}

## Decision Type: {dt['name']}
**Characteristics:** {dt['characteristics']}
**Recommended Frameworks:** {dt['recommended_frameworks']}
**Analysis Methods:** {dt['analysis_methods']}
**Reversibility:** {rev['label']}. {rev['advice']}

## Warning Signs
{dt.get('warning_signs') or 'N/A'}

## Common Pitfalls
{dt.get('common_pitfalls') or 'N/A'}

## Your Decision Statement
<!-- One sentence: what exactly are you deciding? -->

- **Decision owner:**
- **Decide by:**
- **Out of scope:**
"""

        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(_numbered_steps(fw.get("steps")), 1))
        alts = ", ".join(a for a in fw.get("alternatives", []) if a) or "N/A"
        docs["02-FRAMEWORK.md"] = f"""# Step 2: Apply the Framework

## Recommended: {fw['name']} ({fw['complexity']} complexity)
**Category:** {fw.get('category', '')}
**Description:** {fw.get('description', '')}

### Steps
{steps}

### Strengths
{fw.get('strengths', '')}

### Limitations
{fw.get('limitations', '')}

### Alternative Frameworks
{alts}

## Notes While Applying It
<!-- Where you followed the steps, where you deviated and why -->
"""

        crit_rows = "\n".join(f"| {i['name']} | {i['weight']} | {i['guide']} |" for i in crit["items"])
        note = f"\n> {crit['note']}\n" if crit.get("note") else ""
        docs["03-CRITERIA.md"] = f"""# Step 3: Define Evaluation Criteria

Agree on the criteria and weights BEFORE scoring any option (at most 5; weights sum to 100).
Suggested template: **{crit['domain']}**.
{note}
## Your Criteria
| Criterion | Weight (%) | What a 5 looks like |
|---|---|---|
{crit_rows}

## Common Mistakes
{crit.get('mistakes') or 'N/A'}
"""

        analysis = "\n\n".join(f"## {i}. {a['technique']}\n**When to use:** {a['when']}\n**How:** {a['how']}\n"
                               f"**Output:** {a['output']}" for i, a in enumerate(plan["analysis_techniques"], 1))
        docs["04-ANALYSIS.md"] = f"""# Step 4: Analyze

{analysis or 'Pick one technique: Sensitivity Analysis, Pre-Mortem Analysis or Opportunity Cost Assessment.'}

## Key Assumptions
| Assumption | Evidence so far | How to test it | Result |
|---|---|---|---|
| | | | |
"""

        names = options or ["Option A", "Option B", "Option C"]
        option_rows = "\n".join(f"| {o} | | | | |" for o in names)
        head = " | ".join(names)
        matrix_rows = "\n".join(f"| {i['name']} | {i['weight']} | " + " | ".join(" " for _ in names) + " |"
                                for i in crit["items"])
        spec = ",".join(f"{i['name']}:{i['weight']}" for i in crit["items"])
        docs["05-OPTIONS.md"] = f"""# Step 5: Evaluate the Options

## Options
| Option | Description | Pros | Cons | Score |
|---|---|---|---|---|
{option_rows}

## Weighted Scoring Matrix
Score each option 1-5 per criterion (see 03-CRITERIA.md for what a 5 looks like).
| Criterion | Weight | {head} |
|---|---|{'---|' * len(names)}
{matrix_rows}
| **Weighted total** | 100 | {' | '.join(' ' for _ in names)} |

Totals, winner and the smallest weight change that flips it:
`search.py --matrix "{' vs '.join(names).replace('"', "'")}" -c "{spec}" --scores "<option>:<scores>;..." -f markdown`
"""

        docs["06-DECISION.md"] = f"""# Step 6: Decide

## Decision
<!-- State the decision in one sentence -->


## Rationale
<!-- Why this option over the others? Tie each reason to a criterion -->

## Pre-Mortem
It is 12 months from now and this decision failed. What went wrong?
| Failure story | Early warning signal | Mitigation |
|---|---|---|
| | | |

## Kill Criteria
<!-- Signals that mean stop, reverse or revisit, decided now while you are calm -->
- Revisit if:
- Reverse if:
- Review date:

## Risks and Mitigations
| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| | | | |

## Next Actions
| Action | Owner | Deadline | Status |
|---|---|---|---|
| | | | |

## Confidence
<!-- __% that this works out, and why. Log it: search.py --journal "<decision>" --confidence <n> -->
"""

        bias_doc = "# Bias Warnings\n\nCheck each one before deciding.\n\n"
        for i, b in enumerate(plan["bias_warnings"], 1):
            bias_doc += (f"## {i}. {b['bias']} [{b['severity']}]\n**Impact:** {b['impact']}\n"
                         f"**Detect:** {b['detect']}\n**Remedy:** {b['debiasing']}\n- [ ] Checked\n\n")
        if plan.get("anti_patterns"):
            bias_doc += f"## Anti-Patterns\n{plan['anti_patterns']}\n"
        docs["BIAS-WARNINGS.md"] = bias_doc

        docs["DECISION-LOG.md"] = f"""# Decision Log: {project}

| # | Date | Decision | Rationale | Confidence | Status |
|---|---|---|---|---|---|
| 1 | {ts[:10]} | | | | Open |
"""
        return docs

    def persist_step_by_step(self, plan: dict, output_dir: str = None, force: bool = False) -> tuple:
        """Save one markdown file per step; returns (dir, written, kept).

        Files that already exist hold the user's notes and are kept unless force is set.
        """
        plan_dir = self._plan_dir(plan, output_dir)
        docs = self.step_docs(plan)
        workspace.prepare_folder(plan_dir, plan.get("request", ""), plan["decision_type"]["name"], docs, force)
        written, kept = save_docs(plan_dir, docs, force)
        workspace.record_state(plan_dir, plan, {name: docs[name] for name in written})
        return str(plan_dir), written, kept

    # ---- Decision Journal ----
    def create_journal(self, decision_statement: str, project_name: str = None, output_dir: str = None,
                       options: list = None, framework: str = None, confidence: int = None,
                       review_days: int = journal.DEFAULT_REVIEW_DAYS) -> str:
        """Journal entry for a decision, with its type, framework, options and criteria filled in."""
        self.query = unicodedata.normalize("NFC", str(decision_statement or "")).strip()
        plan = self.generate(project_name)
        return journal.create_journal(
            decision_statement, project_name, output_dir,
            decision_type=plan["decision_type"]["name"], framework=framework or plan["framework"]["name"],
            options=options or plan["options"], criteria=plan["criteria"]["items"],
            confidence=confidence, review_days=review_days)

    @staticmethod
    def review_journals(output_dir: str = None, due: bool = False) -> str:
        return journal.review_journals(output_dir, due)

    @staticmethod
    def update_journal(journal_id: str, outcome: str, output_dir: str = None) -> str:
        return journal.update_journal(journal_id, outcome, output_dir)


# ============ WEIGHTED SCORING MATRIX ============
def parse_criteria(spec: str) -> list:
    """'Cost:3,Speed:2,Risk:1' or 'Cost,Speed' -> [{'name', 'weight'}]; empty items are dropped.

    Raises:
        ValueError: duplicate names, bad or negative weights, or weights on only some criteria.
    """
    items, seen = [], set()
    for part in re.split(r"[,;\n]", str(spec or "")):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(?P<name>.*?)\s*[:=]\s*(?P<w>-?\d+(?:\.\d+)?)\s*%?$", part)
        name, weight = (m.group("name").strip(), float(m.group("w"))) if m else (part, None)
        if not name:
            raise ValueError(f"criterion without a name in {part!r}")
        if weight is not None and weight < 0:
            raise ValueError(f"weight of {name!r} must not be negative")
        key = fold(name).lower()
        if key in seen:
            raise ValueError(f"criterion {name!r} is listed twice")
        seen.add(key)
        items.append({"name": name, "weight": weight})
    if not items:
        raise ValueError("no criteria given; use -c \"Cost:3,Speed:2,Risk:1\"")
    given = [i["weight"] is not None for i in items]
    if any(given) and not all(given):
        raise ValueError("give a weight to every criterion or to none (e.g. \"Cost:3,Speed:2\")")
    if not any(given):
        for i in items:
            i["weight"] = 1.0
    if sum(i["weight"] for i in items) <= 0:
        raise ValueError("at least one weight must be above 0")
    return items


SCORE_MIN, SCORE_MAX = 1, 5


def parse_scores(spec: str, criteria_count: int) -> list:
    """'React:4,3,5;Vue:5,4,3' -> [('React', [4, 3, 5]), ('Vue', [5, 4, 3])].

    Raises:
        ValueError: a score list of the wrong length, a missing name, a non-number or a score outside 1-5.
    """
    result = []
    for part in re.split(r"[;\n]", str(spec or "")):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"scores must look like \"Option:4,3,5\", got {part!r}")
        name, values = part.rsplit(":", 1)
        name = name.strip()
        try:
            numbers = [float(v) for v in re.split(r"[,\s]+", values.strip()) if v]
        except ValueError:
            raise ValueError(f"scores of {name!r} must be numbers, got {values.strip()!r}") from None
        if len(numbers) != criteria_count:
            raise ValueError(f"{name!r} has {len(numbers)} scores but there are {criteria_count} criteria")
        bad = [v for v in numbers if not SCORE_MIN <= v <= SCORE_MAX]
        if bad:
            raise ValueError(f"scores of {name!r} must be from {SCORE_MIN} to {SCORE_MAX} (5 = best), got "
                             + ", ".join(_num(v) for v in bad))
        result.append((name, numbers))
    return result


# A flip within this many points of one criterion's share of the total weight makes a winner fragile
FRAGILE_SHARE = 20


def weighted_total(scores: list, weights: list) -> float:
    total = sum(weights)
    return sum(s * w for s, w in zip(scores, weights)) / total if total else 0.0


def sensitivity(options: list, criteria: list) -> list:
    """For each criterion, the smallest change of its weight alone that lets another option catch the winner.

    options: [{'name', 'scores'}] (all scored); criteria: [{'name', 'weight'}].
    Returns [{'criterion', 'weight', 'new_weight', 'change', 'new_winner'}] sorted by |change|;
    'change' is None when no change of that weight alone flips the winner.
    """
    weights = [c["weight"] for c in criteria]
    totals = [weighted_total(o["scores"], weights) for o in options]
    win = max(range(len(options)), key=lambda i: totals[i])
    a = options[win]["scores"]
    rows = []
    for k, c in enumerate(criteria):
        best = None
        for j, other in enumerate(options):
            if j == win:
                continue
            b = other["scores"]
            lead = sum(w * (x - y) for w, x, y in zip(weights, a, b))  # > 0: winner ahead
            gap = a[k] - b[k]
            if gap == 0:
                continue
            delta = -lead / gap  # weight change at which the two tie
            if (delta > 0 and gap < 0) or (delta < 0 and gap > 0 and weights[k] + delta > 0):
                if best is None or abs(delta) < abs(best[0]):
                    best = (delta, other["name"])
        total = sum(weights)
        rows.append({"criterion": c["name"], "weight": c["weight"],
                     "change": best[0] if best else None,
                     "new_weight": c["weight"] + best[0] if best else None,
                     "new_winner": best[1] if best else None,
                     "share": c["weight"] / total * 100,
                     "new_share": (c["weight"] + best[0]) / (total + best[0]) * 100 if best else None})
    return sorted(rows, key=lambda r: (r["change"] is None, abs(r["change"] or 0)))


def build_matrix(description: str, custom_criteria: str = None, scores: str = None) -> dict:
    """Options x criteria matrix; with scores, weighted totals, the winner and its sensitivity.

    Raises:
        ValueError: bad criteria or scores, or scores for an option that is not in the description.
    """
    options = parse_options(description)
    if custom_criteria is not None and str(custom_criteria).strip():
        criteria = parse_criteria(custom_criteria)
        source = "custom"
        guide = ""
    else:
        found = DecisionAdvisor(description).choose_criteria()
        criteria = [{"name": i["name"], "weight": float(i["weight"]), "guide": i["guide"]}
                    for i in criteria_items(found["row"])]
        source = found["row"].get("Domain", "")
        guide = found["row"].get("Measurement Guidance", "")
    weights = [c["weight"] for c in criteria]
    total_weight = sum(weights)
    for c in criteria:
        c["share"] = round(c["weight"] * 100 / total_weight)

    scored = parse_scores(scores, len(criteria)) if scores else []
    if scored and not options:
        options = [name for name, _ in scored]
    if len(options) < 2 and not scored:
        options = ["Option A", "Option B"]
    by_key = {fold(o).lower(): o for o in options}
    score_map = {}
    for name, values in scored:
        key = fold(name).lower()
        if key not in by_key:
            raise ValueError(f"scores given for {name!r}, which is not one of the options: "
                             + ", ".join(options))
        score_map[by_key[key]] = values

    rows = [{"name": o, "scores": score_map.get(o),
             "total": weighted_total(score_map[o], weights) if o in score_map else None} for o in options]
    result = {"description": description, "criteria_source": source, "criteria": criteria,
              "options": rows, "scoring_guide": guide, "winner": None, "runner_up": None,
              "tie": [], "sensitivity": [], "unscored": [r["name"] for r in rows if r["scores"] is None]}
    ranked = sorted([r for r in rows if r["total"] is not None], key=lambda r: -r["total"])
    if len(ranked) >= 2:
        top = ranked[0]["total"]
        tied = [r["name"] for r in ranked if abs(r["total"] - top) < 1e-9]
        if len(tied) > 1:
            result["tie"] = tied
        else:
            result["winner"], result["runner_up"] = ranked[0]["name"], ranked[1]["name"]
            result["margin"] = ranked[0]["total"] - ranked[1]["total"]
            result["sensitivity"] = sensitivity([r for r in rows if r["scores"] is not None], criteria)
    return result


def _table(header: list, rows: list, markdown: bool) -> list:
    if markdown:
        return (["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
                + ["| " + " | ".join(r) + " |" for r in rows])
    widths = [max(display_width(x) for x in col) for col in zip(header, *rows)]

    def line(cells):
        return " | ".join(pad_display(c, w) for c, w in zip(cells, widths)).rstrip()

    return [line(header), "-+-".join("-" * w for w in widths)] + [line(r) for r in rows]


def format_matrix(m: dict, output_format: str = "ascii") -> str:
    """The matrix as a Markdown or aligned plain-text table, with totals and sensitivity when scored."""
    md = output_format == "markdown"
    bold = (lambda s: f"**{s}**") if md else (lambda s: s)
    criteria, options = m["criteria"], m["options"]
    out = [("## Comparison Matrix" if md else "=== COMPARISON MATRIX ==="), ""]
    if m.get("description"):
        out += [f"{bold('Decision:')} {_first_line(m['description'], 200)}"]
    if m.get("criteria_source") != "custom":
        out += [f"{bold('Criteria:')} {m['criteria_source']} template (adjust with -c \"Name:weight,...\")"]
    out.append("")
    header = ["Option"] + [f"{c['name']} (w {_num(c['weight'])}, {c['share']}%)" for c in criteria] + ["Weighted"]
    rows = []
    for o in options:
        cells = [_num(s) for s in o["scores"]] if o["scores"] else ["?"] * len(criteria)
        total = f"{o['total']:.2f}" if o["total"] is not None else "?"
        name = o["name"]
        if m.get("winner") == name:
            name, total = bold(name), bold(total)
        rows.append([name] + cells + [total])
    out += _table(header, rows, md)
    out.append("")

    if m.get("winner"):
        out.append(f"{bold('Winner:')} {m['winner']} ahead of {m['runner_up']} by {m['margin']:.2f} "
                   "(weighted average of the scores).")
        flips = [s for s in m["sensitivity"] if s["change"] is not None]
        out.append("")
        out.append("### Sensitivity" if md else "Sensitivity:")
        if flips:
            s = flips[0]
            verb = "rises" if s["change"] > 0 else "drops"
            out.append(f"Smallest change that flips the winner: if the weight of {s['criterion']} {verb} from "
                       f"{_num(s['weight'])} to {_num(round(s['new_weight'], 2))} "
                       f"({'+' if s['change'] > 0 else ''}{_num(round(s['change'], 2))}; its share of the total "
                       f"goes from {s['share']:.0f}% to {s['new_share']:.0f}%), "
                       f"{s['new_winner']} ties with {m['winner']}; beyond that it wins.")
            out.append("")
            srows = []
            for row in m["sensitivity"]:
                if row["change"] is None:
                    srows.append([row["criterion"], _num(row["weight"]), "no single change flips it", "-"])
                else:
                    srows.append([row["criterion"], _num(row["weight"]),
                                  f"{_num(round(row['new_weight'], 2))} ({'+' if row['change'] > 0 else ''}"
                                  f"{_num(round(row['change'], 2))})", row["new_winner"]])
            out += _table(["Criterion", "Weight", "Flips at weight", "New winner"], srows, md)
            out.append("")
            shift = abs(s["new_share"] - s["share"])
            if shift <= FRAGILE_SHARE:
                out.append(f"Fragile: a shift of {shift:.0f} points in one criterion's share of the weight flips "
                           f"the result. Firm up the weight and scores of {s['criterion']} before deciding.")
            else:
                out.append(f"Robust: flipping the result takes a shift of {shift:.0f} points in a criterion's "
                           "share of the weight.")
        else:
            out.append(f"No change to a single weight flips the winner: {m['winner']} stays ahead whichever "
                       "one weight you raise or lower. Only the scores themselves can change this result.")
    elif m.get("tie"):
        out.append(f"{bold('Tie:')} {', '.join(m['tie'])} have the same weighted score. Revisit the weights "
                   "or add the criterion that really separates them.")
    else:
        out.append("Scoring: give each option 1-5 per criterion (5 = best), then re-run with")
        example = ";".join(f"{o['name']}:{','.join(['?'] * len(criteria))}" for o in options[:3])
        out.append(f"  --scores \"{example}\"")
        out.append("to get weighted totals, the winner and the smallest weight change that flips it.")
    if m.get("unscored") and (m.get("winner") or m.get("tie")):
        out.append("")
        out.append(f"Not scored (left out of the ranking): {', '.join(m['unscored'])}.")
    if m.get("scoring_guide"):
        out += ["", bold("Scoring guide:")]
        out += [f"- {s}" for s in _sentences(m["scoring_guide"])]
    return "\n".join(out).rstrip() + "\n"


# ============ NEXT-STEP SUGGESTIONS ============
NEXT_STEPS = {
    "quick": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide` | Full standard decision analysis |
| `/decide.deep` | Detailed comparison with alternatives |
| `/solve.quick` | Quick scan of the root problem first |
""",
    "standard": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.deep` | Deeper comparison: pre-mortem, sensitivity, information to gather |
| `/decide.exec` | Executive briefing for leadership |
| Add "save step-by-step" | Workspace with one file per step; continue later with `/decide.resume` |
""",
    "deep": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/decide.exec` | Executive summary for stakeholders |
| `/solve.deep` | Deep analysis of risks for the chosen option |
| Add "save step-by-step" | Workspace with one file per step; continue later with `/decide.resume` |
""",
    "executive": """
---
🎯 **Next Steps:**
| Command | Description |
|---------|-------------|
| `/solve.exec` | Executive problem analysis for related issues |
| Add "save step-by-step" | Full decision workspace; continue later with `/decide.resume` |
| `/decide` | Standard-depth analysis for a different perspective |
""",
}


# ============ PUBLIC API ============
def generate_decision_plan(query: str, project_name: str = None, output_format: str = "ascii",
                           persist: bool = False, output_dir: str = None,
                           depth: str = "standard", step_docs: bool = False,
                           decision_type: str = None, force: bool = False) -> str:
    """Generate a decision plan as text ('ascii', 'markdown') or 'json'.

    persist saves it under decision-plans/<project>/ (PLAN.md, or one file per step
    with step_docs); existing files are kept unless force. Text output ends with
    the Next Steps table, once.
    """
    if not str(query or "").strip():
        raise ValueError("describe the decision (the request is empty)")
    advisor = DecisionAdvisor(query, decision_type=decision_type)
    plan = advisor.generate(project_name, depth=depth)

    saved = {}
    if persist:
        if step_docs:
            plan_dir, files, kept = advisor.persist_step_by_step(plan, output_dir, force)
            saved = {"dir": plan_dir, "written": files, "kept": kept}
        else:
            path, written = advisor.persist_plan(plan, output_dir, force)
            saved = {"path": path, "written": written}

    if output_format == "json":
        if saved:
            plan["saved"] = saved
        return json.dumps(plan, indent=2, ensure_ascii=False)

    result = advisor.format_markdown(plan) if output_format == "markdown" else advisor.format_ascii_box(plan)
    if saved.get("dir"):
        result += f"\n\nStep-by-step plan saved to: {saved['dir']}/"
        result += f"\n  Files created: {len(saved['written'])}"
        for name in saved["written"]:
            result += f"\n    {name}"
        if saved["kept"]:
            result += f"\n  Kept {len(saved['kept'])} existing files with your notes (add --force to replace them):"
            for name in saved["kept"]:
                result += f"\n    {name}"
        result += (f"\n  Progress: search.py --status -p {Path(saved['dir']).name}"
                   f"  |  tick a step: search.py --done <step> -p {Path(saved['dir']).name}")
    elif saved:
        if saved["written"]:
            result += f"\n\nPlan saved to: {saved['path']}"
        else:
            result += f"\n\nKept the existing plan at {saved['path']} (add --force to replace it)."
    return result + next_steps_table(NEXT_STEPS.get(depth, NEXT_STEPS["standard"]), bool(saved.get("dir")))


def next_steps_table(text: str, saved_step_docs: bool) -> str:
    """The Next Steps table, without the "save step-by-step" row once the workspace is saved."""
    if not saved_step_docs:
        return text
    return "".join(line for line in text.splitlines(True) if "save step-by-step" not in line)
