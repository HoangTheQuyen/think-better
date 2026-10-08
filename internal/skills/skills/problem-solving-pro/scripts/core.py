#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Solving Pro Core - BM25 search engine for structured problem-solving knowledge base.
Searchable database covering 7-step methodology, decomposition frameworks, analysis tools,
cognitive biases, communication patterns, mental models, and team dynamics.
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path
from math import log
from collections import defaultdict

# ============ CONFIGURATION ============
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
MAX_RESULTS = 3
REASONING_FILE = "reasoning.csv"

CSV_CONFIG = {
    "steps": {
        "file": "steps.csv",
        "search_cols": ["Step", "Phase", "Keywords", "Description", "Key Activities"],
        "output_cols": ["Step", "Phase", "Keywords", "Description", "Key Activities", "Common Pitfalls", "Output Artifacts", "Time Allocation", "Quality Gate", "Tips"]
    },
    "problem-types": {
        "file": "problem-types.csv",
        "search_cols": ["Problem Type", "Keywords", "Characteristics", "Recommended Approach", "Example Domains"],
        "output_cols": ["Problem Type", "Keywords", "Complexity", "Characteristics", "Recommended Approach", "Decomposition Style", "Analysis Methods", "Common Mistakes", "Example Domains", "Time Frame", "Team Size"]
    },
    "decomposition": {
        "file": "decomposition.csv",
        "search_cols": ["Framework", "Type", "Keywords", "Description", "When to Use"],
        "output_cols": ["Framework", "Type", "Keywords", "Description", "When to Use", "Structure Pattern", "Example Application", "MECE Test", "Common Mistakes", "Complexity"]
    },
    "prioritization": {
        "file": "prioritization.csv",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use"],
        "output_cols": ["Technique", "Category", "Keywords", "Description", "When to Use", "How to Apply", "Output Format", "Pitfalls", "Complexity"]
    },
    "analysis": {
        "file": "analysis-tools.csv",
        "search_cols": ["Tool", "Category", "Keywords", "Description", "When to Use"],
        "output_cols": ["Tool", "Category", "Keywords", "Description", "When to Use", "How to Apply", "Data Requirements", "Output Format", "Strengths", "Limitations", "Complexity"]
    },
    "biases": {
        "file": "cognitive-biases.csv",
        "search_cols": ["Bias", "Category", "Keywords", "Description", "Impact on Problem Solving"],
        "output_cols": ["Bias", "Category", "Keywords", "Description", "Impact on Problem Solving", "How to Detect", "Debiasing Strategy", "Example", "Severity"]
    },
    "communication": {
        "file": "communication.csv",
        "search_cols": ["Pattern", "Category", "Keywords", "Description", "When to Use"],
        "output_cols": ["Pattern", "Category", "Keywords", "Description", "When to Use", "Structure", "Example", "Pitfalls", "Audience"]
    },
    "heuristics": {
        "file": "heuristics.csv",
        "search_cols": ["Mental Model", "Category", "Keywords", "Description", "Application to Problem Solving"],
        "output_cols": ["Mental Model", "Category", "Keywords", "Description", "Application to Problem Solving", "When to Use", "Example", "Danger Zone"]
    },
    "team": {
        "file": "team-dynamics.csv",
        "search_cols": ["Pattern", "Category", "Keywords", "Description", "When to Use"],
        "output_cols": ["Pattern", "Category", "Keywords", "Description", "When to Use", "How to Facilitate", "Signs of Dysfunction", "Remedy", "Team Size"]
    }
}


# ============ TEXT PROCESSING ============
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "do", "does",
    "for", "from", "had", "has", "have", "how", "i", "if", "in", "into", "is", "it", "its",
    "me", "my", "of", "on", "or", "our", "should", "so", "that", "the", "their", "them",
    "then", "there", "these", "this", "to", "us", "was", "we", "were", "what", "when",
    "which", "who", "why", "will", "with", "would", "you", "your",
}

_SUFFIXES = ("ations", "ation", "ings", "ing", "ies", "ied", "ed", "es", "ly", "s")


def stem(word: str) -> str:
    """Light suffix stemmer so inflected forms meet.

    'hire', 'hiring', 'hired' -> 'hir'; 'uncertain', 'uncertainty' -> 'uncertain';
    'decline', 'declining', 'declined' -> 'declin'; 'secure', 'security' -> 'secur'.
    """
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            if suffix in ("ies", "ied"):
                word += "y"
            break
    # Nouns in -ity / -ty meet their adjective (security/secure, uncertainty/uncertain)
    if word.endswith("ity") and len(word) >= 6:
        word = word[:-3]
    elif word.endswith("ty") and len(word) >= 6:
        word = word[:-2]
    # Drop a trailing e whether or not a suffix came off: hire/hiring, agree/agreed
    while len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    # dropp -> drop, plann -> plan (l and s stay: scal(l), clas(s))
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiouls":
        word = word[:-1]
    return word


def tokenize(text) -> list:
    """Lowercase, strip punctuation, drop stopwords, stem.

    Two-letter tokens are kept on purpose: CI, UI, DB, QA, PR, AI, ML matter.
    """
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    return [stem(w) for w in text.split() if len(w) > 1 and w not in STOPWORDS]


# ============ BM25 IMPLEMENTATION ============
class BM25:
    """BM25 ranking algorithm for text search."""

    def __init__(self, k1: float=1.5, b: float=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0

    def tokenize(self, text):
        return tokenize(text)

    def fit(self, documents) -> None:
        """Build BM25 index from documents."""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.N

        for doc in self.corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        """Score all documents against query."""
        query_tokens = self.tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_lengths[idx]
            term_freqs = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token in self.idf:
                    tf = term_freqs[token]
                    idf = self.idf[token]
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                    score += idf * numerator / denominator

            scores.append((idx, score))

        return sorted(scores, key=lambda x: x[1], reverse=True)


class TermBM25(BM25):
    """BM25 over ready-made term lists (see phrase_terms), so phrases can be matched."""

    def tokenize(self, text):
        return list(text) if isinstance(text, (list, tuple)) else phrase_terms(text)


# ============ MULTILINGUAL MATCHING ============
def fold_accents(text) -> str:
    """Drop diacritics so Vietnamese typed without accents still matches: 'giảm' -> 'giam'."""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def phrase_terms(text) -> list:
    """Tokens plus their adjacent pairs ('mua lại' -> mua, lại, mua_lại).

    Vietnamese words are several syllables and the tokenizer splits on spaces, so
    single syllables are ambiguous ('lại' = again, 'mua lại' = acquire); the pairs
    let a whole phrase outweigh a stray syllable. English phrases gain the same way.
    """
    tokens = tokenize(text)
    return tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]


def keyword_terms(keywords) -> list:
    """Terms of a comma/semicolon separated keyword list; pairs never cross a separator."""
    terms = []
    for keyword in re.split(r"[,;]", str(keywords)):
        tokens = tokenize(keyword)
        terms += tokens if len(tokens) < 2 else [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    return terms


def rank_by_keywords(rows: list, name_col: str, keyword_col: str, query: str) -> list:
    """[(row index, score)] best first, matching the query against each row's name and keywords.

    The score adds an exact pass and an accent-folded pass, so 'doanh thu giam'
    (typed without accents) still matches the keyword 'doanh thu giảm', while a
    match with the right accents counts double.
    """
    def rank(fold):
        prep = fold_accents if fold else (lambda t: t)
        docs = [phrase_terms(prep(r.get(name_col, ""))) + keyword_terms(prep(r.get(keyword_col, "")))
                for r in rows]
        bm25 = TermBM25(b=0.3)
        bm25.fit(docs)
        return dict(bm25.score(phrase_terms(prep(query))))

    if not rows:
        return []
    exact, folded = rank(False), rank(True)
    ranked = sorted(((i, exact[i] + folded[i]) for i in range(len(rows))), key=lambda x: x[1], reverse=True)
    return [(i, score) for i, score in ranked if score > 0]


# ============ SEARCH FUNCTIONS ============
def _load_csv(filepath):
    """Load CSV and return list of dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _search_csv(filepath, search_cols, output_cols, query, max_results):
    """Core search function using BM25."""
    if not filepath.exists():
        return []

    data = _load_csv(filepath)

    # Build documents from search columns
    documents = [" ".join(str(row.get(col, "")) for col in search_cols) for row in data]

    # BM25 search; Vietnamese typed without accents gets a second, accent-folded pass
    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)
    if not ranked or ranked[0][1] <= 0:
        bm25 = BM25()
        bm25.fit([fold_accents(d) for d in documents])
        ranked = bm25.score(fold_accents(query))

    # Get top results with score > 0
    results = []
    for idx, score in ranked[:max_results]:
        if score > 0:
            row = data[idx]
            results.append({col: row.get(col, "") for col in output_cols if col in row})

    return results


def detect_domain(query):
    """Auto-detect the most relevant domain from query."""
    query_lower = query.lower()

    domain_keywords = {
        "steps": ["step", "process", "methodology", "workflow", "phase", "how to", "approach", "procedure"],
        "problem-types": ["type", "kind", "classification", "category", "wicked", "structured", "diagnostic", "opportunity", "design"],
        "decomposition": ["tree", "mece", "decompose", "disaggregate", "break down", "structure", "logic", "issue tree", "hypothesis", "cleave", "framework"],
        "prioritization": ["prioritize", "priority", "rank", "80/20", "pareto", "focus", "triage", "screen", "impact", "feasibility", "moscow"],
        "analysis": ["analyze", "analysis", "tool", "method", "benchmark", "regression", "scenario", "monte carlo", "experiment", "test", "root cause", "5 whys", "fermi", "estimation", "market size"],
        "biases": ["bias", "cognitive", "fallacy", "thinking error", "debiasing", "confirmation", "anchoring", "overconfidence", "sunk cost", "groupthink"],
        "communication": ["communicate", "present", "presentation", "pyramid", "storytelling", "slide", "memo", "executive", "audience", "persuade", "synthesis", "synthesize"],
        "heuristics": ["mental model", "heuristic", "first principles", "inversion", "occam", "bayesian", "opportunity cost", "second order", "leverage", "margin of safety"],
        "team": ["team", "group", "collaboration", "workshop", "facilitation", "red team", "brainstorm", "psychological safety", "conflict", "diversity"]
    }

    scores = {domain: sum(1 for kw in keywords if kw in query_lower) for domain, keywords in domain_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "steps"


def search(query, domain=None, max_results=MAX_RESULTS):
    """Main search function with auto-domain detection."""
    if domain is None:
        domain = detect_domain(query)

    config = CSV_CONFIG.get(domain, CSV_CONFIG["steps"])
    filepath = DATA_DIR / config["file"]

    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    results = _search_csv(filepath, config["search_cols"], config["output_cols"], query, max_results)

    return {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "count": len(results),
        "results": results
    }


# ============ CLASSIFICATION ============
def load_reasoning() -> list:
    """Load reasoning rules (one per problem category)."""
    filepath = DATA_DIR / REASONING_FILE
    if not filepath.exists():
        return []
    return _load_csv(filepath)


def problem_type_names() -> list:
    """All problem types, for --type choices."""
    return [row["Problem Type"] for row in _load_csv(DATA_DIR / CSV_CONFIG["problem-types"]["file"])]


def category_names() -> list:
    """All reasoning categories, for --category choices."""
    return [row["Problem_Category"] for row in load_reasoning()]


def classify_category(query: str) -> str:
    """Pick the reasoning category (business context) that best matches the query.

    Returns "" when nothing matches, so callers fall back to generic defaults
    (and tell the AI to pass --category).
    """
    rules = load_reasoning()
    ranked = rank_by_keywords(rules, "Problem_Category", "Keywords", query)
    return rules[ranked[0][0]].get("Problem_Category", "") if ranked else ""


def classify_problem_type(query: str) -> dict:
    """The problem-types row whose name and keywords best match the query, or {}.

    Keywords decide first (English and Vietnamese); when none match, the full
    description columns are searched as a weaker signal (source "text").
    """
    rows = _load_csv(DATA_DIR / CSV_CONFIG["problem-types"]["file"])
    ranked = rank_by_keywords(rows, "Problem Type", "Keywords", query)
    if ranked:
        return dict(rows[ranked[0][0]], _source="auto")
    results = search(query, "problem-types", 1).get("results", [])
    if results:
        name = results[0].get("Problem Type")
        row = next((r for r in rows if r["Problem Type"] == name), results[0])
        return dict(row, _source="text")
    return {}


# ============ CROSS-REFERENCES ============
def _norm_name(text) -> str:
    """'Root Cause Analysis (5 Whys)' -> 'root cause analysis'."""
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", str(text))).strip().lower()


NAME_COLUMNS = {
    "decomposition": "Framework", "prioritization": "Technique", "analysis": "Tool",
    "biases": "Bias", "communication": "Pattern", "heuristics": "Mental Model", "team": "Pattern",
}


def find_record(domain: str, name: str) -> dict:
    """The record of `domain` called `name`, or {}.

    Parentheticals are ignored and a reference may be the start of the full
    name ('Expert Interview' -> 'Expert Interview / Delphi Method').
    """
    wanted = _norm_name(name)
    if len(wanted) < 3:
        return {}
    rows = _load_csv(DATA_DIR / CSV_CONFIG[domain]["file"])
    col = NAME_COLUMNS[domain]
    for row in rows:
        if _norm_name(row.get(col, "")) == wanted:
            return row
    for row in rows:
        have = _norm_name(row.get(col, ""))
        if have and (have.startswith(wanted + " ") or wanted.startswith(have + " ")):
            return row
    return {}


def split_names(text, sep: str = None) -> list:
    """'A + B; C' -> ['A', 'B', 'C'] (both separators are used in the data)."""
    parts = re.split(r"\s\+\s|;", str(text)) if sep is None else str(text).split(sep)
    return [p.strip() for p in parts if p.strip()]


def resolve_choice(value: str, choices: list, what: str) -> str:
    """Case-insensitive lookup of value in choices; raises ValueError if unknown."""
    for choice in choices:
        if choice.lower() == value.strip().lower():
            return choice
    raise ValueError(f"unknown {what} {value!r}; choose one of: {', '.join(choices)}")


# ============ OUTPUT PATHS ============
def slugify(text: str, max_len: int = 50) -> str:
    """Filesystem-safe slug: no separators, no '..', never empty."""
    slug = re.sub(r"[^\w\s-]", " ", str(text).lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")[:max_len].strip("-")
    return slug or "plan"


def default_output_dir() -> Path:
    """Where persisted plans go when --output-dir is not given.

    Normally the current directory (the user's project). If the script is run
    from inside the installed skill folder (e.g. after `cd .../scripts`),
    write to the project root instead so plans never land inside the skill,
    where reinstalling or uninstalling would delete them.
    """
    cwd = Path.cwd().resolve()
    if cwd != SKILL_DIR and SKILL_DIR not in cwd.parents:
        return cwd
    for parent in SKILL_DIR.parents:
        if (parent / ".git").exists():
            return parent
    # Skills are installed at <project>/<.target>/<skills|prompts>/<name>/
    parents = SKILL_DIR.parents
    return parents[2] if len(parents) > 2 else SKILL_DIR.parent


def save_docs(directory: Path, docs: dict, force: bool = False) -> tuple:
    """Write {file name: content} into directory; returns (written, kept).

    Existing files are kept unless force is set: they hold the user's notes,
    and re-running a plan must never wipe them.
    """
    written, kept = [], []
    for name, content in docs.items():
        path = Path(directory) / name
        if path.exists() and not force:
            kept.append(name)
            continue
        path.write_text(content, encoding="utf-8")
        written.append(name)
    return written, kept


def read_stdin_query(stream=None) -> str:
    """The task text piped on stdin (--stdin), decoded as UTF-8.

    Slash commands pass the user's text this way (a quoted heredoc) so that
    quotes, backticks and $ in pasted error messages never reach a shell.
    """
    stream = stream or sys.stdin
    data = stream.buffer.read() if hasattr(stream, "buffer") else stream.read()
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    return data.lstrip("\ufeff").strip()
