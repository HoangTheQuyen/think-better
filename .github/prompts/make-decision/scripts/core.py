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
from collections import Counter
from pathlib import Path

# ============ PATHS ============
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MAX_RESULTS = 3

# ============ CSV CONFIGURATION ============
CSV_CONFIG = {
    "frameworks": {
        "file": "decision-frameworks.csv",
        "search_cols": ["Framework", "Category", "Keywords", "Description", "When to Use", "Best For"],
        "output_cols": ["Framework", "Category", "Description", "When to Use", "Steps", "Strengths", "Limitations", "Best For", "Complexity"],
    },
    "types": {
        "file": "decision-types.csv",
        "search_cols": ["Decision Type", "Keywords", "Characteristics", "Warning Signs", "Example Scenarios"],
        "output_cols": ["Decision Type", "Characteristics", "Recommended Frameworks", "Analysis Methods", "Common Pitfalls", "Warning Signs", "Example Scenarios"],
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
        "search_cols": ["Domain", "Keywords", "Description", "Criteria"],
        "output_cols": ["Domain", "Description", "Criteria", "Default Weights", "Measurement Guidance", "Common Mistakes"],
    },
    "facilitation": {
        "file": "facilitation.csv",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use", "Counters Bias"],
        "output_cols": ["Technique", "Category", "Description", "When to Use", "Group Size", "Time Required", "Steps", "Counters Bias", "Output"],
    },
}


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
        """Tokenize text: lowercase, remove punctuation, filter short words."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]

    def fit(self, corpus: list):
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
        query_tokens = self.tokenize(query)
        scores = []

        for idx in range(self.corpus_size):
            doc_score = 0.0
            dl = self.doc_len[idx]
            tf_doc = self.doc_freqs[idx]

            for token in query_tokens:
                if token not in self.idf:
                    continue
                tf = tf_doc.get(token, 0)
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                doc_score += idf * (numerator / denominator)

            scores.append((idx, doc_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


# ============ DATA LOADING ============
def load_csv(domain: str) -> list:
    """Load CSV data for a domain. Returns list of row dicts."""
    config = CSV_CONFIG.get(domain)
    if not config:
        return []

    filepath = DATA_DIR / config["file"]
    if not filepath.exists():
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if any(v.strip() for v in row.values())]


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
        "framework", "methodology", "approach", "method", "tree", "matrix",
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
        "bias", "cognitive", "fallacy", "heuristic", "debiasing",
        "confirmation", "anchoring", "sunk cost", "status quo",
        "overconfidence", "framing", "groupthink", "loss aversion",
        "recency", "survivorship", "planning fallacy", "availability",
    ],
    "analysis": [
        "analysis", "technique", "quantitative", "qualitative",
        "sensitivity", "break-even", "decision tree", "scenario",
        "scoring", "opportunity cost", "risk-reward", "bayesian",
        "pre-mortem", "reference class", "forecasting",
    ],
    "criteria": [
        "criteria", "template", "weight", "scoring", "evaluation",
        "technology selection", "hiring", "vendor", "investment",
        "market entry", "product feature", "organizational change",
        "location", "facility",
    ],
    "facilitation": [
        "facilitation", "group", "team", "workshop", "voting",
        "debate", "red team", "devil's advocate", "nominal group",
        "anonymous", "alignment", "workplan", "structured",
    ],
}


def auto_detect_domains(query: str, top_n: int = 3) -> list:
    """Detect most relevant domains for a query using keyword scoring."""
    query_lower = query.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in query_lower:
                score += len(kw.split())  # Multi-word keywords score higher
        scores[domain] = score

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
