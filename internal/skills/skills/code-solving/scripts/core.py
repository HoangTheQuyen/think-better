#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving Core - BM25 search over a coding knowledge base, task-type
classification, and detection of a project's own test/lint/build commands.

Domains: steps, task-types, debugging, changes, testing, principles,
         biases, review, artifacts, errors
"""

import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from math import log
from functools import lru_cache
from pathlib import Path

# ============ CONFIGURATION ============
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
MAX_RESULTS = 3
# Folder name when a project name has nothing usable in it
SLUG_FALLBACK = "plan"

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
    "errors": {
        "file": "errors.csv", "name_col": "Error",
        "search_cols": ["Error", "Language", "Keywords", "Meaning", "Likely Causes"],
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


# ============ BM25 ============
class BM25:
    """BM25 ranking over short documents."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.corpus, self.doc_lengths, self.idf, self.tfs = [], [], {}, []
        self.avgdl = 0

    def fit(self, documents) -> None:
        self.corpus = [tokenize(doc) for doc in documents]
        if not self.corpus:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / len(self.corpus) or 1
        freqs = defaultdict(int)
        self.tfs = []
        for doc in self.corpus:
            tf = defaultdict(int)
            for word in doc:
                tf[word] += 1
            self.tfs.append(tf)
            for word in tf:
                freqs[word] += 1
        n = len(self.corpus)
        self.idf = {w: log((n - f + 0.5) / (f + 0.5) + 1) for w, f in freqs.items()}

    def score(self, query: str) -> list:
        # Each query term counts once: repeating a word must not outweigh the rest
        tokens = [t for t in dict.fromkeys(tokenize(query)) if t in self.idf]
        scores = []
        for idx, tf in enumerate(self.tfs):
            score = 0.0
            norm = 1 - self.b + self.b * self.doc_lengths[idx] / self.avgdl
            for token in tokens:
                if tf.get(token):
                    score += self.idf[token] * tf[token] * (self.k1 + 1) / (tf[token] + self.k1 * norm)
            scores.append((idx, score))
        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============ DATA ACCESS ============
@lru_cache(maxsize=None)
def _read_rows(path: Path) -> tuple:
    with open(path, "r", encoding="utf-8") as f:
        return tuple(csv.DictReader(f))


def load_csv(domain: str) -> list:
    """All rows of a domain's CSV as dicts (copies: callers may change them)."""
    return [dict(row) for row in _read_rows(DATA_DIR / CSV_CONFIG[domain]["file"])]


def find_named(domain: str, names) -> list:
    """Rows of `domain` whose name matches one of `names` (str with ';' or list), in that order."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(";")]
    col = CSV_CONFIG[domain]["name_col"]
    by_name = {row[col].lower(): row for row in load_csv(domain)}
    return [by_name[n.lower()] for n in names if n and n.lower() in by_name]


@lru_cache(maxsize=None)
def _error_patterns() -> tuple:
    return tuple((re.compile(row["Pattern"], re.I), row) for row in _read_rows(DATA_DIR / "errors.csv"))


def match_errors(text: str, limit: int = 3) -> list:
    """Known errors whose message pattern appears in text, in the order they appear."""
    hits = []
    for pattern, row in _error_patterns():
        m = pattern.search(text)
        if m:
            hits.append((m.start(), dict(row)))
    hits.sort(key=lambda hit: hit[0])
    return [row for _, row in hits[:limit]]


def split_identifiers(text: str) -> str:
    """'NullPointerException in getUserId' -> 'Null Pointer Exception in get User Id'.

    Error names and identifiers carry the signal in code questions.
    """
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text).replace("_", " ")


def _ranked(query: str, domain: str) -> tuple:
    """(rows, [(row index, score)] best first) of a BM25 search in one domain."""
    rows = load_csv(domain)
    cols = CSV_CONFIG[domain]["search_cols"]
    bm25 = BM25()
    bm25.fit([" ".join(str(row.get(c, "")) for c in cols) for row in rows])
    return rows, bm25.score(split_identifiers(query))


def search(query: str, domain: str = None, max_results: int = MAX_RESULTS) -> dict:
    """BM25 search within one domain.

    Without a domain, the one the query's hint words point at; when no hint
    matches (or that domain has nothing), the domain with the best match.
    """
    picked = domain or detect_domain(query, default="")
    rows, ranked = _ranked(query, picked) if picked else ([], [])
    if not domain and (not ranked or ranked[0][1] <= 0):
        best = None
        for name in CSV_CONFIG:
            found = _ranked(query, name)
            if found[1] and found[1][0][1] > 0 and (best is None or found[1][0][1] > best[2][0][1]):
                best = (name,) + found
        if best:
            picked, rows, ranked = best
        picked = picked or "steps"
    results = [rows[i] for i, score in ranked[:max_results] if score > 0]
    return {"domain": picked, "query": query, "file": CSV_CONFIG[picked]["file"],
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
    "errors": ["exception", "panic", "traceback", "error message"],
}


def detect_domain(query: str, default: str = "steps") -> str:
    """Pick the domain whose hint words appear most in the query (else `default`).

    Hints match whole words ('log' is not in 'catalog'); a query that quotes a
    known error message goes to the errors domain.
    """
    grams, folded = query_grams(query)
    scores = {d: len(matched_phrases(grams, folded, kws)) for d, kws in DOMAIN_HINTS.items()}
    best = max(scores, key=scores.get)
    if match_errors(query, 1):
        return "errors"
    return best if scores[best] > 0 else default


# ============ CLASSIFICATION ============
# On equal scores the more specific task type wins
TYPE_PRIORITY = ["security", "incident", "flaky-test", "migration", "performance", "test", "review",
                 "explain", "quick-fix", "refactor", "debug", "feature"]
# A keyword phrase of several words says more than a single word
PHRASE_WEIGHT = 1.5
# A stack trace or a known error message makes it a debugging task unless something else is clearer
TRACE_WEIGHT = 2
STACK_TRACE = re.compile(
    r"Traceback \(most recent call last\)|^\s*File \"[^\"]+\", line \d+|^\s+at \S.*[(\s][^\s()]+:\d+|"
    r"^\s+at .+ in .+:line \d+|^goroutine \d+ \[|^\s*panic: |Exception in thread|^\s*Caused by: ", re.M)
# A measured duration ("4 seconds", "300ms") points at performance
DURATION = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:ms|s|secs?|seconds?|minutes?|mins?|giây|phút)\b", re.I)
DURATION_WEIGHT = 1
# Common Vietnamese words typed without accents. Two of them make the text Vietnamese, and then
# one-syllable keywords match without their accents too ('loi' = lỗi); otherwise 'sap' (sập)
# or 'cham' (chậm) could be English words or names.
VIETNAMESE_WORDS = {
    "khong", "duoc", "nhung", "cua", "bi", "voi", "nay", "khi", "minh", "giup", "lam", "nao", "roi",
    "cung", "dang", "vao", "sua", "cac", "nhieu", "trang", "nguoi", "dung", "chay", "loi", "cham",
    "nut", "trong", "sau", "truoc", "thi", "la", "cho", "ham", "tu", "sang", "len", "moi", "toi",
    "doi", "them", "xoa", "tao", "viet", "mat", "khau", "gui", "nhap", "xuat", "hien",
}


def task_type_names() -> list:
    """Task type ids, for --type choices."""
    return [row["Type"] for row in _read_rows(DATA_DIR / CSV_CONFIG["task-types"]["file"])]


@lru_cache(maxsize=64)
def _keyword_phrases(cell: str, folded: bool) -> tuple:
    """(tokens, phrase, weight, one Vietnamese syllable?) for each comma-separated keyword."""
    out, seen = [], set()
    for phrase in str(cell).split(","):
        tokens = phrase_tokens(phrase, folded)
        if tokens and tokens not in seen:
            seen.add(tokens)
            lone_accented = len(tokens) == 1 and has_accents(phrase)
            out.append((tokens, phrase.strip(), PHRASE_WEIGHT if len(tokens) > 1 else 1, lone_accented))
    return tuple(out)


def task_scores(query: str) -> dict:
    """{task type: (score, [matched keywords])} from whole keyword phrases in the request.

    Each keyword counts once however often it appears. Text typed with accents
    is matched against the accented keywords; text without accents against
    the keywords with their accents folded.
    """
    text = split_identifiers(query)
    grams, folded = query_grams(text)
    vietnamese = folded and len(VIETNAMESE_WORDS.intersection(fold(text).lower().split())) >= 2
    traced = bool(STACK_TRACE.search(query) or match_errors(query, 1))
    timed = bool(DURATION.search(query))
    scores = {}
    for row in _read_rows(DATA_DIR / CSV_CONFIG["task-types"]["file"]):
        score, matched = 0.0, []
        for tokens, phrase, weight, lone_accented in _keyword_phrases(row["Keywords"], folded):
            if tokens in grams and not (folded and lone_accented and not vietnamese):
                score += weight
                matched.append(phrase)
        if row["Type"] == "debug" and traced:
            score += TRACE_WEIGHT
            matched.append("stack trace / error message")
        if row["Type"] == "performance" and timed:
            score += DURATION_WEIGHT
            matched.append("a measured duration")
        scores[row["Type"]] = (score, matched)
    return scores


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
    scores = task_scores(query)
    order = {name: i for i, name in enumerate(TYPE_PRIORITY)}
    best = max(rows, key=lambda r: (scores[r["Type"]][0], -order.get(r["Type"], 99)))
    if scores[best["Type"]][0] > 0:
        return best, "auto"
    return next(r for r in rows if r["Type"] == "feature"), "default"


# ============ PROJECT COMMANDS ============
def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# Words that mark a CI step as a check worth running locally, by purpose (first match wins)
CI_PURPOSES = (
    ("format", ("fmt", "format", "prettier")),
    ("typecheck", ("tsc", "mypy", "typecheck", "type-check", "pyright")),
    ("lint", ("lint", "vet", "clippy", "eslint", "ruff", "golangci", "shellcheck", "flake8")),
    ("test", ("test", "pytest", "tox", "rspec", "spec", "jest", "vitest")),
    ("build", ("build", "compile")),
)
# CI steps that prepare or ship rather than check: by program, or by its subcommand
CI_SKIP_PROGRAMS = {"echo", "cd", "export", "mkdir", "cp", "mv", "rm", "curl", "wget", "sudo",
                    "apt", "apt-get", "brew", "choco", "pip", "pip3", "set", "git"}
CI_SKIP_SUBCOMMANDS = {"install", "ci", "download", "add", "login", "push", "publish", "upload",
                       "deploy", "release", "cache", "sync", "restore"}


def _ci_commands(root: Path) -> list:
    """(purpose, command, source) for check-like `run:` steps in GitHub Actions workflows."""
    found = []
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return found
    for path in sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))):
        lines = _read(path).splitlines()
        commands = []
        for i, line in enumerate(lines):
            m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", line)
            if not m:
                continue
            value = m.group(2).strip()
            if value and value[0] not in "|>":
                commands.append(value.strip("'\""))
                continue
            # Block scalar: the following lines indented deeper than `run:`
            indent = len(m.group(1))
            for nxt in lines[i + 1:]:
                if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                if nxt.strip() and not nxt.strip().startswith("#"):
                    commands.append(nxt.strip())
        for command in commands:
            low = command.lower()
            tokens = low.split()
            if (not tokens or "${{" in low or len(command) > 100 or tokens[0] in CI_SKIP_PROGRAMS
                    or (len(tokens) > 1 and tokens[1] in CI_SKIP_SUBCOMMANDS)):
                continue
            # Flags such as --out-format say nothing about the step's purpose
            text = " ".join(w for w in tokens if not w.startswith("-"))
            words = set(re.findall(r"[a-z]+", text)) | set(re.findall(r"[a-z][a-z-]*", text))
            for purpose, markers in CI_PURPOSES:
                if any(marker in words for marker in markers):
                    found.append((purpose, command, f".github/workflows/{path.name}"))
                    break
    return found


def _python_runner(root: Path, config: str) -> str:
    """Prefix that runs tools inside the project's environment ('uv run ', 'poetry run ', ...)."""
    if (root / "uv.lock").exists() or "[tool.uv" in config:
        return "uv run "
    if (root / "poetry.lock").exists() or "[tool.poetry" in config:
        return "poetry run "
    if (root / "pdm.lock").exists() or "[tool.pdm" in config:
        return "pdm run "
    if (root / "Pipfile").exists():
        return "pipenv run "
    return ""


def detect_project_commands(root: Path = None) -> list:
    """The project's own build/test/lint commands, as (purpose, command, source) tuples.

    Looks only at well-known files in `root` (default: the project root) and the
    check steps of its CI workflows; never runs anything. Purpose "one test"
    is the command for running a single test, with <file>/<name> to fill in.
    """
    root = Path(root) if root else default_output_dir()
    found = []

    def norm(command):
        return " ".join(command.replace(" run ", " ").split())

    def add(purpose, command, source):
        if all(norm(c) != norm(command) for _, c, _ in found):
            found.append((purpose, command, source))

    pkg = root / "package.json"
    if pkg.exists():
        try:
            manifest = json.loads(_read(pkg))
        except ValueError:
            manifest = {}
        scripts = manifest.get("scripts", {}) or {}
        runner = "npm run"
        for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun run"), ("bun.lock", "bun run")):
            if (root / lock).exists():
                runner = name
                break
        for key, purpose in (("test", "test"), ("lint", "lint"), ("typecheck", "typecheck"),
                             ("type-check", "typecheck"), ("check", "check"), ("format:check", "format"),
                             ("format", "format"), ("fmt", "format"), ("build", "build")):
            if key in scripts and not (purpose == "format" and any(p == "format" for p, _, _ in found)):
                add(purpose, f"{runner} {key}", "package.json")
        test_script = str(scripts.get("test", ""))
        if re.search(r"\b(jest|vitest)\b", test_script):
            args = "-- <file> -t \"<name>\"" if runner == "npm run" else "<file> -t \"<name>\""
            add("one test", f"{runner} test {args}", "package.json")
        elif re.search(r"\bmocha\b", test_script):
            sep = "-- " if runner == "npm run" else ""
            add("one test", f"{runner} test {sep}--grep \"<name>\"", "package.json")
        workspaces = manifest.get("workspaces") or (root / "pnpm-workspace.yaml").exists()
        if workspaces and "test" not in scripts:
            recursive = {"pnpm": "pnpm -r test", "npm run": "npm test --workspaces --if-present",
                         "yarn": "yarn workspaces foreach -A run test" if (root / ".yarnrc.yml").exists()
                         else "yarn workspaces run test"}.get(runner)
            if recursive:
                add("test", recursive, "workspaces")

    makefile = root / "Makefile"
    if makefile.exists():
        targets = re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", _read(makefile), flags=re.M)
        for target in ("check", "test", "lint", "vet", "typecheck", "build"):
            if target in targets:
                add(target, f"make {target}", "Makefile")

    if (root / "go.mod").exists():
        add("test", "go test ./...", "go.mod")
        add("one test", "go test ./<pkg> -run '^<TestName>$'", "go.mod")
        add("lint", "go vet ./...", "go.mod")
        if any((root / f).exists() for f in (".golangci.yml", ".golangci.yaml", ".golangci.toml")):
            add("lint", "golangci-lint run", ".golangci.yml")
        add("build", "go build ./...", "go.mod")

    if (root / "Cargo.toml").exists():
        add("test", "cargo test", "Cargo.toml")
        add("one test", "cargo test <name>", "Cargo.toml")
        add("lint", "cargo clippy -- -D warnings", "Cargo.toml")
        add("format", "cargo fmt --check", "Cargo.toml")

    py_files = ("pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini")
    py_config = " ".join(_read(root / f) for f in py_files)
    if py_config.strip() or (root / "requirements.txt").exists():
        run = _python_runner(root, py_config)
        source = next((f for f in py_files if (root / f).exists()), "requirements.txt")
        if "pytest" in py_config or (root / "pytest.ini").exists() or (root / "tests").is_dir():
            add("test", f"{run}pytest", source)
            add("one test", f"{run}pytest <file>::<name>", source)
        if "ruff" in py_config:
            add("lint", f"{run}ruff check .", source)
        if "mypy" in py_config:
            add("typecheck", f"{run}mypy .", source)
        if (root / "tox.ini").exists():
            add("test", "tox", "tox.ini")

    if (root / "pom.xml").exists():
        add("test", "mvn test", "pom.xml")
        add("one test", "mvn test -Dtest=<Class>#<method>", "pom.xml")
    gradle = next((f for f in ("build.gradle.kts", "build.gradle") if (root / f).exists()), None)
    if gradle:
        tool = "./gradlew" if (root / "gradlew").exists() else "gradle"
        add("test", f"{tool} test", gradle)
        add("one test", f"{tool} test --tests '<Class>.<method>'", gradle)

    if (root / "Gemfile").exists():
        if (root / "spec").is_dir():
            add("test", "bundle exec rspec", "Gemfile")
            add("one test", "bundle exec rspec <file>:<line>", "Gemfile")
        else:
            add("test", "bundle exec rake test", "Gemfile")

    composer = root / "composer.json"
    if composer.exists() and '"test"' in _read(composer):
        add("test", "composer test", "composer.json")

    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        add("test", "dotnet test", "*.sln / *.csproj")
        add("one test", "dotnet test --filter <name>", "*.sln / *.csproj")

    if (root / "deno.json").exists() or (root / "deno.jsonc").exists():
        add("test", "deno test", "deno.json")

    # What CI actually runs: added last, so local config wins on duplicates
    for purpose, command, source in _ci_commands(root)[:8]:
        add(purpose, command, source)

    return found
