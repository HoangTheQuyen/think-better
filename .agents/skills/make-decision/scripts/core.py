#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make-Decision Core - BM25 search engine for decision-making knowledge base.

Provides full-text search across 6 decision-making domains:
  frameworks, types, biases, analysis, criteria, facilitation

Usage:
    from core import search, search_domain, auto_detect_domains, CSV_CONFIG
    results = search("hypothesis driven uncertainty")
    results = search_domain("sunk cost", "biases", max_results=3)
"""

import csv
import math
import re
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

# ============ PATHS ============
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
MAX_RESULTS = 3
# Folder name when a project name has nothing usable in it
SLUG_FALLBACK = "decision"

# ============ CSV CONFIGURATION ============
CSV_CONFIG = {
    "frameworks": {
        "file": "decision-frameworks.csv",
        "search_cols": ["Framework", "Category", "Keywords", "Description", "When to Use", "Best For"],
        "output_cols": ["Framework", "Category", "Description", "When to Use", "Steps", "Strengths", "Limitations", "Best For", "Complexity"],
    },
    "types": {
        "file": "decision-types.csv",
        "search_cols": ["Decision Type", "Strong Signals", "Keywords", "Characteristics", "Warning Signs", "Example Scenarios"],
        "output_cols": ["Decision Type", "Characteristics", "Recommended Frameworks", "Analysis Methods", "Key Biases", "Facilitation", "Common Pitfalls", "Warning Signs", "Example Scenarios"],
    },
    "biases": {
        "file": "cognitive-biases.csv",
        "search_cols": ["Bias", "Category", "Keywords", "Description", "Impact on Decisions"],
        "output_cols": ["Bias", "Category", "Description", "Impact on Decisions", "How to Detect", "Debiasing Strategy", "Example", "Severity"],
    },
    "analysis": {
        "file": "analysis-techniques.csv",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use"],
        "output_cols": ["Technique", "Category", "Description", "When to Use", "Inputs Required", "How to Apply", "Output Format", "Strengths", "Limitations", "Complexity"],
    },
    "criteria": {
        "file": "criteria-templates.csv",
        "search_cols": ["Domain", "Strong Signals", "Keywords", "Description", "Criteria"],
        "output_cols": ["Domain", "Description", "Criteria", "Default Weights", "Measurement Guidance", "Common Mistakes", "Key Biases"],
    },
    "facilitation": {
        "file": "facilitation.csv",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use", "Counters Bias"],
        "output_cols": ["Technique", "Category", "Description", "When to Use", "Group Size", "Time Required", "Steps", "Counters Bias", "Output"],
    },
}


# ============ SHARED TEXT HELPERS ============
# Identical in the three skills' core.py: scripts/test_skill_engines.py compares
# their source. Each skill is installed on its own, so each keeps a copy.
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
    """Lowercase, strip punctuation, drop stopwords, stem (for BM25 search).

    Two-letter tokens are kept on purpose: CI, UI, DB, QA, PR, AI, ML matter.
    """
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    return [stem(w) for w in text.split() if len(w) > 1 and w not in STOPWORDS]


def fold(text) -> str:
    """Accent-insensitive form: 'Nên chọn' -> 'Nen chon', 'đ' -> 'd'.

    NFC and NFD input give the same result, so text typed on any OS (or
    without diacritics) matches the knowledge base.
    """
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", text.replace("đ", "d").replace("Đ", "D"))


def has_accents(text) -> bool:
    """True when text carries diacritics (e.g. Vietnamese typed with its accents)."""
    text = unicodedata.normalize("NFC", str(text))
    return fold(text) != text


def match_tokens(text, folded: bool = True) -> list:
    """Lowercased, stemmed words (accents folded unless folded=False) for phrase matching.

    Unlike tokenize(), stopwords and one-letter words are kept, so keyword
    phrases match only whole: 'how many' never matches 'too many', 'y tế'
    (health) never matches 'kinh tế' (economy).
    """
    text = fold(text) if folded else unicodedata.normalize("NFC", str(text))
    words = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return [stem(w) for w in words]


@lru_cache(maxsize=64)
def query_grams(query: str, longest: int = 6) -> tuple:
    """(frozenset of the query's word n-grams, folded) for phrase matching.

    Text typed with accents is matched exactly, so 'chi nhánh' (branch) never
    meets 'nhanh' (fast); text typed without accents is matched against the
    keywords with their accents folded away. Cached: classifiers call it once
    per CSV row.
    """
    folded = not has_accents(query)
    tokens = match_tokens(query, folded)
    grams = set()
    for n in range(1, longest + 1):
        grams.update(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
    return frozenset(grams), folded


@lru_cache(maxsize=4096)
def phrase_tokens(phrase: str, folded: bool = True) -> tuple:
    """The match_tokens() of one keyword phrase, cached (keyword lists are matched over and over)."""
    return tuple(match_tokens(phrase, folded))


def display_width(text) -> int:
    """Columns text takes in a terminal: combining marks take none, wide (CJK, emoji) characters two."""
    width = 0
    for ch in unicodedata.normalize("NFC", str(text)):
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad_display(text, width: int) -> str:
    """text (NFC) padded with spaces to `width` terminal columns."""
    text = unicodedata.normalize("NFC", str(text))
    return text + " " * max(0, width - display_width(text))


def wrap_display(text, width: int, indent: str = "", subsequent: str = None) -> list:
    """Lines of at most `width` terminal columns, wrapped at spaces; over-long words are split."""
    subsequent = indent if subsequent is None else subsequent
    lines, current = [], ""
    for word in unicodedata.normalize("NFC", str(text)).split():
        if current and display_width(current) + 1 + display_width(word) <= width:
            current += " " + word
            continue
        if current:
            lines.append(current)
        prefix = subsequent if lines else indent
        current = prefix + word
        while display_width(current) > width and len(current) > len(prefix) + 1:
            cut = len(prefix) + 1
            while cut < len(current) and display_width(current[:cut + 1]) <= width:
                cut += 1
            lines.append(current[:cut])
            prefix = subsequent
            current = prefix + current[cut:]
    if current:
        lines.append(current)
    return lines


def slugify(text: str, max_len: int = 50) -> str:
    """Filesystem-safe slug: no separators, no '..', never empty.

    Vietnamese (and other accented Latin) text becomes plain ASCII, so a name
    typed with or without accents, in NFC or NFD, gives the same folder.
    """
    slug = re.sub(r"[^\w\s-]", " ", fold(text).lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")[:max_len].strip("-")
    return slug or SLUG_FALLBACK


def default_output_dir() -> Path:
    """Where plans (and journals) go when --output-dir is not given.

    Normally the current directory (the user's project). If the script is run
    from inside the installed skill folder (e.g. after `cd .../scripts`),
    use the project root instead so files never land inside the skill,
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
    """The text piped on stdin (--stdin), decoded as UTF-8.

    Slash commands pass the user's text this way (a quoted heredoc) so that
    quotes, backticks and $ in pasted error messages never reach a shell.
    """
    stream = stream or sys.stdin
    data = stream.buffer.read() if hasattr(stream, "buffer") else stream.read()
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    return data.lstrip("\ufeff").strip()


def matched_phrases(grams: frozenset, folded: bool, phrases) -> list:
    """The phrases (strings) whose words appear next to each other in the query grams."""
    return [p for p in phrases if phrase_tokens(p, folded) and phrase_tokens(p, folded) in grams]


# ============ BM25 ENGINE ============
class BM25:
    """Okapi BM25 ranking function for CSV-based document search."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len = []
        self.avg_dl = 0
        self.doc_freqs = []
        self.idf = {}
        self.corpus_size = 0

    @staticmethod
    def tokenize(text: str) -> list:
        return tokenize(fold(text))

    def fit(self, corpus: list) -> None:
        """Build IDF index from a list of document strings."""
        self.corpus_size = len(corpus)
        if self.corpus_size == 0:
            return

        df = Counter()
        self.doc_freqs = []
        self.doc_len = []

        for doc in corpus:
            tokens = self.tokenize(doc)
            self.doc_len.append(len(tokens))
            tf = Counter(tokens)
            self.doc_freqs.append(tf)
            for term in tf:
                df[term] += 1

        self.avg_dl = sum(self.doc_len) / self.corpus_size if self.corpus_size else 1

        # IDF with smoothing
        for term, freq in df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query: str) -> list:
        """Score all documents against a query. Returns list of (index, score)."""
        # Each query term counts once: repeating a word must not outweigh the rest
        query_tokens = [t for t in dict.fromkeys(self.tokenize(query)) if t in self.idf]
        scores = []

        for idx in range(self.corpus_size):
            doc_score = 0.0
            dl = self.doc_len[idx]
            tf_doc = self.doc_freqs[idx]

            for token in query_tokens:
                tf = tf_doc.get(token, 0)
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                doc_score += idf * (numerator / denominator)

            scores.append((idx, doc_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


# ============ DATA LOADING ============
@lru_cache(maxsize=None)
def _read_rows(filepath: Path) -> tuple:
    with open(filepath, "r", encoding="utf-8") as f:
        return tuple(row for row in csv.DictReader(f) if any(v.strip() for v in row.values()))


def load_csv(domain: str) -> list:
    """Load CSV data for a domain. Returns list of row dicts (copies: callers may change them)."""
    config = CSV_CONFIG.get(domain)
    if not config:
        return []

    filepath = DATA_DIR / config["file"]
    if not filepath.exists():
        return []
    return [dict(row) for row in _read_rows(filepath)]


# ============ KEYWORD SIGNALS ============
STRONG_WEIGHT = 3


@lru_cache(maxsize=1024)
def _phrases(cell: str, folded: bool = True) -> tuple:
    """Comma-separated keyword phrases of a CSV cell as (token tuple, phrase), duplicates removed."""
    seen, phrases = set(), []
    for phrase in str(cell or "").split(","):
        tokens = phrase_tokens(phrase, folded)
        if tokens and tokens not in seen:
            seen.add(tokens)
            phrases.append((tokens, phrase.strip()))
    return tuple(phrases)


def signal_matches(query: str, row: dict) -> tuple:
    """(score, matched phrases) of a row's 'Strong Signals' (3 each) and 'Keywords' (1 each).

    A phrase matches when its words appear next to each other in the query;
    a phrase counts once even when it is listed in both columns.
    """
    grams, folded = query_grams(query)
    score, matched, counted = 0, [], set()
    for col, weight in (("Strong Signals", STRONG_WEIGHT), ("Keywords", 1)):
        for tokens, phrase in _phrases(row.get(col, ""), folded):
            if tokens in grams and tokens not in counted:
                counted.add(tokens)
                score += weight
                matched.append(phrase)
    return score, matched


def rank_by_signals(query: str, domain: str) -> list:
    """Rows of a domain as (score, row, matched), best first; ties keep CSV order."""
    ranked = []
    for index, row in enumerate(load_csv(domain)):
        score, matched = signal_matches(query, row)
        ranked.append((score, -index, row, matched))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [(score, row, matched) for score, _, row, matched in ranked]


def find_row(domain: str, name: str) -> dict:
    """The row of a domain whose first column equals name (case-insensitive), or {}."""
    wanted = re.sub(r"\(.*?\)", "", str(name)).strip().lower()
    for row in load_csv(domain):
        have = re.sub(r"\(.*?\)", "", next(iter(row.values()), "")).strip().lower()
        if have and (have == wanted or (len(wanted) >= 4 and have.startswith(wanted))):
            return row
    return {}


def search_domain(query: str, domain: str, max_results: int = MAX_RESULTS) -> dict:
    """Search a single domain using BM25. Returns result dict."""
    config = CSV_CONFIG.get(domain)
    if not config:
        return {"error": f"Unknown domain: {domain}", "domain": domain, "query": query}

    rows = load_csv(domain)
    if not rows:
        return {
            "domain": domain,
            "query": query,
            "file": config["file"],
            "count": 0,
            "results": [],
        }

    # Build search corpus from search_cols
    corpus = []
    for row in rows:
        text_parts = [row.get(col, "") for col in config["search_cols"]]
        corpus.append(" ".join(text_parts))

    # BM25 search
    bm25 = BM25()
    bm25.fit(corpus)
    scored = bm25.score(query)

    # Filter results with positive scores
    results = []
    for idx, sc in scored[:max_results]:
        if sc > 0:
            row = rows[idx]
            result = {col: row.get(col, "") for col in config["output_cols"] if col in row}
            results.append(result)

    return {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "count": len(results),
        "results": results,
    }


# ============ DOMAIN DETECTION ============
DOMAIN_KEYWORDS = {
    "frameworks": [
        "framework", "methodology", "phương pháp", "khung", "approach", "method", "tree", "matrix",
        "hypothesis", "mece", "decomposition", "evaluation", "pros cons",
        "pre-mortem", "scenario planning", "weighted criteria", "reversibility",
        "iterative", "expected value", "sensitivity",
    ],
    "types": [
        "type", "classification", "category", "binary", "multi-option",
        "resource allocation", "strategic", "operational", "tactical",
        "uncertainty", "group decision", "stakeholder", "time-pressured",
    ],
    "biases": [
        "bias", "cognitive", "fallacy", "thiên kiến", "ngụy biện", "heuristic", "debiasing",
        "confirmation", "anchoring", "sunk cost", "status quo",
        "overconfidence", "framing", "groupthink", "loss aversion",
        "recency", "survivorship", "planning fallacy", "availability",
    ],
    "analysis": [
        "analysis", "technique", "phân tích", "quantitative", "qualitative",
        "sensitivity", "break-even", "decision tree", "scenario",
        "scoring", "opportunity cost", "risk-reward", "bayesian",
        "pre-mortem", "reference class", "forecasting",
    ],
    "criteria": [
        "criteria", "template", "weight", "tiêu chí", "trọng số", "scoring", "evaluation",
        "technology selection", "hiring", "vendor", "investment",
        "market entry", "product feature", "organizational change",
        "location", "facility",
    ],
    "facilitation": [
        "facilitation", "group", "team", "workshop", "voting", "nhóm", "bỏ phiếu",
        "debate", "red team", "devil's advocate", "nominal group",
        "anonymous", "alignment", "workplan", "structured",
    ],
}


def auto_detect_domains(query: str, top_n: int = 3) -> list:
    """Detect most relevant domains for a query using keyword scoring.

    Keywords match whole words only ('team' is not in 'steam'); multi-word
    keywords score higher.
    """
    grams, folded = query_grams(query)
    scores = {domain: sum(len(kw.split()) for kw in matched_phrases(grams, folded, keywords))
              for domain, keywords in DOMAIN_KEYWORDS.items()}

    # Sort by score descending, take top_n with positive scores
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    detected = [d for d, s in ranked if s > 0][:top_n]

    # If nothing detected, return all domains
    if not detected:
        return list(CSV_CONFIG.keys())

    return detected


def search(query: str, domain: str = None, max_results: int = MAX_RESULTS) -> dict:
    """Main search entry point. Auto-detects domain if not specified."""
    if domain:
        return search_domain(query, domain, max_results)

    # Auto-detect and search across domains
    return search_all(query, max_results)


def search_all(query: str, max_results: int = MAX_RESULTS) -> dict:
    """Search across auto-detected domains, aggregate results."""
    domains = auto_detect_domains(query)

    all_results = []
    domain_counts = {}

    for d in domains:
        result = search_domain(query, d, max_results)
        if result.get("results"):
            domain_counts[d] = result["count"]
            for r in result["results"]:
                r["_domain"] = d
                all_results.append(r)

    return {
        "domain": "auto",
        "detected_domains": domains,
        "query": query,
        "count": len(all_results),
        "domain_counts": domain_counts,
        "results": all_results,
    }


# ============ MAIN (TEST) ============
if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "hypothesis driven decision"
    print(f"Query: {query}\n")

    # Test auto-detect
    detected = auto_detect_domains(query)
    print(f"Detected domains: {detected}\n")

    # Test search
    for domain in CSV_CONFIG:
        result = search_domain(query, domain, 2)
        print(f"--- {domain} ({result['count']} results) ---")
        for r in result["results"]:
            first_key = list(r.keys())[0]
            print(f"  {r[first_key]}")
        print()
