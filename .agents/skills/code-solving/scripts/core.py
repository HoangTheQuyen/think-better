#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving Core - BM25 search over a coding knowledge base, task-type
classification, and detection of a project's own test/lint/build commands.

Domains: steps, task-types, debugging, changes, testing, principles,
         biases, review, artifacts
"""

import csv
import json
import re
from collections import defaultdict
from math import log
from pathlib import Path

# ============ CONFIGURATION ============
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
MAX_RESULTS = 3

CSV_CONFIG = {
    "steps": {
        "file": "steps.csv", "name_col": "Name",
        "search_cols": ["Name", "Goal", "Key Activities", "Quality Gate"],
    },
    "task-types": {
        "file": "task-types.csv", "name_col": "Type",
        "search_cols": ["Type", "Name", "Keywords", "Description"],
    },
    "debugging": {
        "file": "debugging.csv", "name_col": "Technique",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use"],
    },
    "changes": {
        "file": "changes.csv", "name_col": "Technique",
        "search_cols": ["Technique", "Category", "Keywords", "Description", "When to Use"],
    },
    "testing": {
        "file": "testing.csv", "name_col": "Strategy",
        "search_cols": ["Strategy", "Keywords", "Description", "When to Use"],
    },
    "principles": {
        "file": "principles.csv", "name_col": "Principle",
        "search_cols": ["Principle", "Keywords", "Description", "Apply When"],
    },
    "biases": {
        "file": "biases.csv", "name_col": "Bias",
        "search_cols": ["Bias", "Keywords", "Description", "How It Shows Up"],
    },
    "review": {
        "file": "review-checklist.csv", "name_col": "Area",
        "search_cols": ["Area", "Keywords", "What to Check", "Red Flags"],
    },
    "artifacts": {
        "file": "artifacts.csv", "name_col": "Artifact",
        "search_cols": ["Artifact", "Keywords", "When to Use"],
    },
}


# ============ TEXT PROCESSING ============
# Kept identical to the other skills' core.py (checked by scripts/test_skill_engines.py).
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "do", "does",
    "for", "from", "had", "has", "have", "how", "i", "if", "in", "into", "is", "it", "its",
    "me", "my", "of", "on", "or", "our", "should", "so", "that", "the", "their", "them",
    "then", "there", "these", "this", "to", "us", "was", "we", "were", "what", "when",
    "which", "who", "why", "will", "with", "would", "you", "your",
}


_SUFFIXES = ("ations", "ation", "ings", "ing", "ies", "ied", "ed", "es", "ly", "s")



def stem(word: str) -> str:
    """Light suffix stemmer so 'declining', 'declined' and 'decline' match."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            if suffix in ("ies", "ied"):
                word += "y"
            break
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    # dropp -> drop, scal(l) stays readable enough for matching
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiouls":
        word = word[:-1]
    return word


def tokenize(text) -> list:
    """Lowercase, strip punctuation, drop stopwords, stem.

    Two-letter tokens are kept on purpose: CI, UI, DB, QA, PR, AI, ML matter.
    """
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    return [stem(w) for w in text.split() if len(w) > 1 and w not in STOPWORDS]



# ============ BM25 ============
class BM25:
    """BM25 ranking over short documents."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.corpus, self.doc_lengths, self.idf = [], [], {}
        self.avgdl = 0

    def fit(self, documents) -> None:
        self.corpus = [tokenize(doc) for doc in documents]
        if not self.corpus:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / len(self.corpus) or 1
        freqs = defaultdict(int)
        for doc in self.corpus:
            for word in set(doc):
                freqs[word] += 1
        n = len(self.corpus)
        self.idf = {w: log((n - f + 0.5) / (f + 0.5) + 1) for w, f in freqs.items()}

    def score(self, query: str) -> list:
        tokens = tokenize(query)
        scores = []
        for idx, doc in enumerate(self.corpus):
            tf = defaultdict(int)
            for word in doc:
                tf[word] += 1
            score = 0.0
            for token in tokens:
                if token in self.idf and tf[token]:
                    norm = 1 - self.b + self.b * self.doc_lengths[idx] / self.avgdl
                    score += self.idf[token] * tf[token] * (self.k1 + 1) / (tf[token] + self.k1 * norm)
            scores.append((idx, score))
        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============ DATA ACCESS ============
def load_csv(domain: str) -> list:
    """All rows of a domain's CSV as dicts."""
    with open(DATA_DIR / CSV_CONFIG[domain]["file"], "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_named(domain: str, names) -> list:
    """Rows of `domain` whose name matches one of `names` (str with ';' or list), in that order."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(";")]
    col = CSV_CONFIG[domain]["name_col"]
    by_name = {row[col].lower(): row for row in load_csv(domain)}
    return [by_name[n.lower()] for n in names if n and n.lower() in by_name]


def split_identifiers(text: str) -> str:
    """'NullPointerException in getUserId' -> 'Null Pointer Exception in get User Id'.

    Error names and identifiers carry the signal in code questions.
    """
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text).replace("_", " ")


def search(query: str, domain: str = None, max_results: int = MAX_RESULTS) -> dict:
    """BM25 search within one domain (auto-detected when not given)."""
    domain = domain or detect_domain(query)
    rows = load_csv(domain)
    cols = CSV_CONFIG[domain]["search_cols"]
    bm25 = BM25()
    bm25.fit([" ".join(str(row.get(c, "")) for c in cols) for row in rows])
    ranked = bm25.score(split_identifiers(query))
    results = [rows[i] for i, score in ranked[:max_results] if score > 0]
    return {"domain": domain, "query": query, "file": CSV_CONFIG[domain]["file"],
            "count": len(results), "results": results}


DOMAIN_HINTS = {
    "debugging": ["debug", "bug", "error", "bisect", "repro", "trace", "log", "flaky", "profile", "stack"],
    "changes": ["refactor", "migrate", "migration", "flag", "slice", "spike", "legacy", "strangler", "rewrite"],
    "testing": ["test", "tdd", "coverage", "benchmark", "property", "snapshot", "contract"],
    "principles": ["principle", "kiss", "yagni", "dry", "solid", "design", "coupling", "simple"],
    "biases": ["bias", "fallacy", "assumption", "anchoring", "estimate", "premature"],
    "review": ["review", "security", "checklist", "concurrency", "edge case", "compatibility"],
    "artifacts": ["pr description", "commit message", "adr", "postmortem", "rfc", "design doc", "report"],
    "steps": ["step", "process", "workflow", "gate", "define", "verify"],
}


def detect_domain(query: str) -> str:
    """Pick the domain whose hint words appear most in the query (default: steps)."""
    q = query.lower()
    scores = {d: sum(1 for kw in kws if kw in q) for d, kws in DOMAIN_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "steps"


# ============ CLASSIFICATION ============
def task_type_names() -> list:
    """Task type ids, for --type choices."""
    return [row["Type"] for row in load_csv("task-types")]


def classify_task(query: str, task_type: str = None) -> tuple:
    """Return (row, source). source is 'explicit', 'auto', or 'default' when nothing matched.

    Raises:
        ValueError: if task_type is given but unknown.
    """
    rows = load_csv("task-types")
    if task_type:
        wanted = task_type.strip().lower()
        for row in rows:
            if wanted in (row["Type"], row["Name"].lower()):
                return row, "explicit"
        raise ValueError(f"unknown task type {task_type!r}; choose one of: {', '.join(r['Type'] for r in rows)}")
    found = search(query, "task-types", 1)["results"]
    if found:
        return found[0], "auto"
    return next(r for r in rows if r["Type"] == "feature"), "default"


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



# ============ PROJECT COMMANDS ============
def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_project_commands(root: Path = None) -> list:
    """The project's own build/test/lint commands, as (purpose, command, source) tuples.

    Looks only at well-known files in `root` (default: the project root); never runs anything.
    """
    root = Path(root) if root else default_output_dir()
    found = []

    def add(purpose, command, source):
        if all(c != command for _, c, _ in found):
            found.append((purpose, command, source))

    pkg = root / "package.json"
    if pkg.exists():
        try:
            scripts = json.loads(_read(pkg)).get("scripts", {}) or {}
        except ValueError:
            scripts = {}
        runner = "npm run"
        for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun run"), ("bun.lock", "bun run")):
            if (root / lock).exists():
                runner = name
                break
        for key, purpose in (("test", "test"), ("lint", "lint"), ("typecheck", "typecheck"),
                             ("type-check", "typecheck"), ("check", "check"), ("build", "build")):
            if key in scripts:
                add(purpose, f"{runner} {key}", "package.json")

    makefile = root / "Makefile"
    if makefile.exists():
        targets = re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", _read(makefile), flags=re.M)
        for target in ("check", "test", "lint", "vet", "typecheck", "build"):
            if target in targets:
                add("test" if target == "check" else target, f"make {target}", "Makefile")

    if (root / "go.mod").exists():
        add("test", "go test ./...", "go.mod")
        add("lint", "go vet ./...", "go.mod")
        if any((root / f).exists() for f in (".golangci.yml", ".golangci.yaml", ".golangci.toml")):
            add("lint", "golangci-lint run", ".golangci.yml")
        add("build", "go build ./...", "go.mod")

    if (root / "Cargo.toml").exists():
        add("test", "cargo test", "Cargo.toml")
        add("lint", "cargo clippy -- -D warnings", "Cargo.toml")
        add("format", "cargo fmt --check", "Cargo.toml")

    py_config = " ".join(_read(root / f) for f in ("pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini"))
    if py_config.strip() or (root / "requirements.txt").exists():
        if "pytest" in py_config or (root / "pytest.ini").exists() or (root / "tests").is_dir():
            add("test", "pytest", "pyproject.toml / tests/")
        if "ruff" in py_config:
            add("lint", "ruff check .", "pyproject.toml")
        if "mypy" in py_config:
            add("typecheck", "mypy .", "pyproject.toml")
        if (root / "tox.ini").exists():
            add("test", "tox", "tox.ini")

    if (root / "pom.xml").exists():
        add("test", "mvn test", "pom.xml")
    gradle = next((f for f in ("build.gradle.kts", "build.gradle") if (root / f).exists()), None)
    if gradle:
        add("test", ("./gradlew" if (root / "gradlew").exists() else "gradle") + " test", gradle)

    if (root / "Gemfile").exists():
        add("test", "bundle exec rspec" if (root / "spec").is_dir() else "bundle exec rake test", "Gemfile")

    composer = root / "composer.json"
    if composer.exists() and '"test"' in _read(composer):
        add("test", "composer test", "composer.json")

    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        add("test", "dotnet test", "*.sln / *.csproj")

    if (root / "deno.json").exists() or (root / "deno.jsonc").exists():
        add("test", "deno test", "deno.json")

    return found
