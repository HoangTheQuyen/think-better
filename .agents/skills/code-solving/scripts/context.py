#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Solving Context - facts from the project itself, gathered before any
code is read: where an error points (stack-trace locations with the source
line), the files and symbols the request names, the commits that last
touched them, the working tree, and for reviews the diff with the review
areas it touches.

Read-only: it reads files and runs `git` with fixed arguments (never a
shell, never anything the request could turn into a command).
"""

import os
import re
import subprocess
from pathlib import Path

MAX_ITEMS = 8
GIT_TIMEOUT = 10
MAX_WALK_FILES = 20000
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv",
             "__pycache__", ".next", ".nuxt", ".tox", ".mypy_cache", ".pytest_cache",
             "site-packages", "coverage", ".gradle", ".idea", ".vscode"}
CODE_EXT = ("py|pyi|js|jsx|ts|tsx|mjs|cjs|vue|svelte|go|rs|java|kt|kts|scala|groovy|rb|php|cs|fs|"
            "swift|m|mm|c|h|cc|cpp|cxx|hpp|ex|exs|erl|dart|lua|sh|bash|sql|proto|graphql|"
            "yml|yaml|json|toml|ini|cfg|html|css|scss|md")

# Stack-trace frames. Each pattern yields file, line and optionally func.
TRACE_PATTERNS = [
    # Python:  File "app/orders.py", line 42, in get_total
    re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>[\w<>.]+))?'),
    # Java / Kotlin / Scala:  at com.shop.OrderService.getTotal(OrderService.java:42)
    re.compile(r"at (?P<func>[\w$.<>]+)\((?P<file>[\w$-]+\.(?:java|kt|kts|scala|groovy)):(?P<line>\d+)\)"),
    # C#:  in /src/Orders/OrderService.cs:line 42
    re.compile(r" in (?P<file>\S+\.cs):line (?P<line>\d+)"),
    # Everything else: path.ext:line[:col] (JS/TS, Go, Rust, Ruby, PHP, C, compiler errors)
    re.compile(r"(?P<file>(?:[A-Za-z]:)?[\w./\\@~+-]*\w\.(?:" + CODE_EXT + r")):(?P<line>\d+)(?::\d+)?\b"),
]
FILE_TOKEN = re.compile(r"(?<![\w/.-])(?P<file>[\w@~+-][\w./@~+-]*\.(?:" + CODE_EXT + r"))(?![\w:])")
IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
# First words of lines that call a function rather than declare it
NOT_DECLARATIONS = {"return", "await", "new", "throw", "yield", "if", "else", "elif", "case", "while",
                    "for", "assert", "print", "echo", "go", "defer", "not", "and", "or", "in", "is"}

# Review areas a diff touches, by changed path or by added lines.
# Names match review-checklist.csv.
AREA_RULES = (
    ("Security",
     r"auth|login|passw|token|session|secret|crypt|permission|acl|oauth|jwt|csrf|cors|sanitiz",
     r"password|secret|api[_-]?key|\beval\(|\bexec\(|innerHTML|dangerouslySetInnerHTML|os\.system|"
     r"shell=True|verify=False|InsecureSkipVerify|\bmd5\b|\bsha1\b|Math\.random"),
    ("Data Safety",
     r"migrat|schema|\.sql$|(^|/)models?/|entities|prisma|alembic",
     r"\bDROP\s|ALTER\s+TABLE|DELETE\s+FROM|TRUNCATE|\bUPDATE\s+\w+\s+SET\b"),
    ("API Compatibility",
     r"(^|/)api/|routes?[/.]|controllers?/|handlers?/|\.proto$|openapi|swagger|graphql|(^|/)public/",
     None),
    ("Concurrency",
     None,
     r"\bgo func|\bsync\.|Mutex|\.Lock\(\)|[Tt]hread|\basync\s|\bawait\s|Promise\.all|asyncio|"
     r"concurrent|[Aa]tomic|\bchan\s"),
    ("Error Handling",
     None,
     r"\bcatch\b|\bexcept\b|\brescue\b|recover\(\)|err != nil|\.unwrap\(\)|\bpanic\(|\bthrow\s|\braise\s"),
    ("Performance",
     r"cache|quer(y|ies)|(^|/)db/|repositor",
     r"\bSELECT\s|\.query\(|findAll|\.all\(\)|\bsleep\(|time\.Sleep|N\+1"),
    ("Observability",
     None,
     r"logger\.|\blog\.(debug|info|warn|error)|logging\.|metrics|tracing|\bspan\b"),
)
TEST_PATH = re.compile(r"(^|/)(tests?|spec|__tests__|testdata)/|_test\.go$|(^|/)test_[^/]+\.py$|"
                       r"_test\.py$|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt|cs)$|_spec\.rb$")
NO_CODE_PATH = re.compile(r"\.(md|rst|txt|adoc|csv|json|lock|svg|png|jpg|gif)$|(^|/)(docs?|LICENSE)", re.I)
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|--|<!--|;)")
SOURCE_PATH = re.compile(r"\.(py|js|jsx|ts|tsx|mjs|go|rs|java|kt|scala|rb|php|cs|swift|c|cc|cpp|ex|dart)$")


# ============ GIT ============
def git(root: Path, *args):
    """stdout of `git -C root <args>`, or None when git is missing or the command fails."""
    try:
        proc = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True,
                              timeout=GIT_TIMEOUT, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def is_git_repo(root: Path) -> bool:
    return git(root, "rev-parse", "--is-inside-work-tree") is not None


def project_files(root: Path, in_git: bool) -> list:
    """Project files relative to root (tracked plus untracked, not ignored), posix paths."""
    if in_git:
        out = git(root, "ls-files", "-co", "--exclude-standard")
        if out is not None:
            return [f for f in out.splitlines() if f and not SKIP_DIRS.intersection(f.split("/")[:-1])]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel = Path(dirpath).relative_to(root).as_posix()
        for name in filenames:
            files.append(name if rel == "." else f"{rel}/{name}")
            if len(files) >= MAX_WALK_FILES:
                return files
    return files


# ============ RESOLVING PATHS ============
# Frames from installed libraries and runtimes, never the project's own code
LIBRARY_MARKERS = ("site-packages/", "dist-packages/", "node_modules/", "/lib/python2", "/lib/python3", "/usr/lib/",
                   "/usr/local/lib/", "go/pkg/mod/", "/go/src/runtime/", ".cargo/registry/", "/rustc/",
                   "node:internal", "<frozen", "<anonymous>", "/jdk/", "java.base/")


def _normalize(path: str) -> str:
    path = path.replace("\\", "/")
    for prefix in ("file://", "webpack:///", "webpack://"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    path = re.sub(r"^[A-Za-z]:", "", path)
    return path


def index_files(files: list) -> dict:
    """{base name: [paths]} so a path tail is matched without scanning every file."""
    index = {}
    for f in files:
        index.setdefault(f.rsplit("/", 1)[-1], []).append(f)
    return index


def resolve(path: str, files, root: Path, hint: str = "") -> str:
    """The project file a path from an error or request refers to, or "".

    `files` is a list of project paths or its index_files() index. Absolute
    paths from another machine (CI, a container) still resolve when their
    tail matches a project file. `hint` (e.g. a Java package) breaks ties.
    """
    index = files if isinstance(files, dict) else index_files(files)
    path = _normalize(path)
    if any(marker in path for marker in LIBRARY_MARKERS):
        return ""
    try:
        absolute = Path(path)
        if absolute.is_absolute() and root.resolve() in absolute.resolve().parents:
            rel = absolute.resolve().relative_to(root.resolve()).as_posix()
            if rel in index.get(rel.rsplit("/", 1)[-1], ()):
                return rel
    except (OSError, ValueError):
        pass
    parts = [p for p in path.split("/") if p not in ("", ".", "..", "~")]
    candidates = index.get(parts[-1], []) if parts else []
    for start in range(len(parts)):
        tail = "/".join(parts[start:])
        matches = [f for f in candidates if f == tail or f.endswith("/" + tail)]
        if len(matches) == 1:
            return matches[0]
        if matches:
            hinted = [m for m in matches if hint and hint in m]
            return (hinted or sorted(matches, key=len))[0]
    return ""


def _source_line(root: Path, rel: str, line: int) -> str:
    try:
        with open(root / rel, encoding="utf-8", errors="replace") as f:
            for number, text in enumerate(f, 1):
                if number == line:
                    text = text.strip()
                    return text if len(text) <= 120 else text[:117] + "..."
    except OSError:
        pass
    return ""


# ============ WHAT THE REQUEST POINTS AT ============
def trace_locations(text: str, files: list, root: Path) -> list:
    """Project locations in stack traces and compiler errors, in the order they appear.

    Frames in libraries (node_modules, site-packages, the standard library)
    do not resolve to project files and are dropped.
    """
    found, seen = [], set()
    spans = []
    index = index_files(files)
    for pattern in TRACE_PATTERNS:
        for m in pattern.finditer(text):
            if any(s <= m.start() < e for s, e in spans):
                continue
            spans.append((m.start(), m.end()))
            func = (m.groupdict().get("func") or "").strip()
            hint = "/".join(func.split(".")[:-2]) if m.re is TRACE_PATTERNS[1] else ""
            rel = resolve(m.group("file"), index, root, hint)
            line = int(m.group("line"))
            if not rel or (rel, line) in seen:
                continue
            seen.add((rel, line))
            found.append({"file": rel, "line": line, "func": func, "pos": m.start(),
                          "code": _source_line(root, rel, line)})
    found.sort(key=lambda loc: loc["pos"])
    for loc in found:
        del loc["pos"]
    return found[:MAX_ITEMS]


def named_files(text: str, files: list, root: Path, exclude=()) -> list:
    """Project files the request names (UserList.tsx, src/api/orders.py)."""
    found = []
    index = index_files(files)
    for m in FILE_TOKEN.finditer(text):
        rel = resolve(m.group("file"), index, root)
        if rel and rel not in found and rel not in exclude:
            found.append(rel)
    return found[:MAX_ITEMS]


def candidate_symbols(text: str) -> list:
    """Identifiers worth looking up: camelCase, PascalCase, snake_case, dotted parts.

    Plain lowercase words are skipped (too common), as are error class names,
    which belong to the language rather than the project.
    """
    names = []
    for word in IDENTIFIER.findall(text):
        if len(word) < 4 or word in names:
            continue
        mixed = re.search(r"[a-z][A-Z]", word) or re.search(r"[A-Z][a-z]+[A-Z]", word)
        snake = "_" in word.strip("_") and word.lower() == word
        if not (mixed or snake):
            continue
        if re.search(r"(Error|Exception|Warning|Panic)$", word):
            continue
        names.append(word)
    return names[:6]


def find_symbols(names: list, root: Path) -> list:
    """Where each symbol is defined and how many files refer to it (git grep)."""
    found = []
    for name in names:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            continue
        definition = (r"(def|class|func|function|fn|interface|type|struct|enum|trait|const|let|var|val|"
                      r"module|record)[[:space:]]+(\([^)]*\)[[:space:]]*)?" + name)
        out = git(root, "grep", "-n", "-I", "-w", "-E", "-e", definition, "--", ".") or ""
        defs = []
        for line in out.splitlines():
            path, _, rest = line.partition(":")
            number, _, _ = rest.partition(":")
            if path and number.isdigit() and not SKIP_DIRS.intersection(path.split("/")[:-1]):
                defs.append(f"{path}:{number}")
        if not defs:
            # Typed declarations without a keyword: `int getTotal() {`, `public Order find(...)`
            # POSIX bracket expression: a literal ] must come first, and \ does not escape
            typed = r"^[[:space:]]*([][[:alnum:]_<>,.?*&:]+[[:space:]]+)+" + name + r"[[:space:]]*\("
            out = git(root, "grep", "-n", "-I", "-E", "-e", typed, "--", ".") or ""
            for line in out.splitlines():
                path, _, rest = line.partition(":")
                number, _, code = rest.partition(":")
                code = code.strip()
                if (path and number.isdigit() and not code.endswith(";")
                        and code.split()[0] not in NOT_DECLARATIONS
                        and not SKIP_DIRS.intersection(path.split("/")[:-1])):
                    defs.append(f"{path}:{number}")
        refs = git(root, "grep", "-l", "-I", "-w", "-F", "-e", name, "--", ".") or ""
        ref_files = [f for f in refs.splitlines() if f and not SKIP_DIRS.intersection(f.split("/")[:-1])]
        if defs or ref_files:
            found.append({"name": name, "defined": defs[:3], "files": len(ref_files)})
    return found


# ============ GIT STATE ============
def recent_commits(root: Path, paths: list) -> list:
    """The last commits that touched `paths` (or the repo when none), newest first."""
    fmt = "%h\t%ad\t%an\t%s"
    args = ["log", "-n", "5", f"--format={fmt}", "--date=short"]
    if paths:
        args += ["--"] + paths[:MAX_ITEMS]
    out = git(root, *args) or ""
    commits = []
    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) == 4:
            commits.append({"sha": parts[0], "date": parts[1], "author": parts[2], "subject": parts[3][:80]})
    return commits


def working_tree(root: Path) -> dict:
    branch = (git(root, "rev-parse", "--abbrev-ref", "HEAD") or "").strip()
    status = git(root, "status", "--porcelain=v1") or ""
    changes = [line[3:] if len(line) > 3 else line for line in status.splitlines()]
    return {"branch": branch, "changes": changes[:10], "change_count": len(changes)}


# ============ DIFF FOR REVIEW ============
def _default_base(root: Path) -> str:
    head = (git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD") or "").strip()
    candidates = ([head] if head else []) + ["origin/main", "origin/master", "main", "master"]
    current = (git(root, "rev-parse", "HEAD") or "").strip()
    for ref in candidates:
        sha = (git(root, "rev-parse", "--verify", "--quiet", ref + "^{commit}") or "").strip()
        if sha and sha != current:
            return ref
    return ""


# Untracked output of the skills and the AI tools themselves: not part of the change under review
OWN_OUTPUT = ("coding-plans/", "solving-plans/", "decision-plans/", ".decisions/", ".claude/",
              ".github/prompts/", ".agents/", ".opencode/", ".agent/", ".cursor/", ".windsurf/")


def _uncommitted(root: Path) -> list:
    """`git status` entries that belong to the user's change (tool output left out)."""
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all") or ""
    entries = []
    for line in status.splitlines():
        path = line[3:].strip('"')
        if line.startswith("??") and path.startswith(OWN_OUTPUT):
            continue
        entries.append(line)
    return entries


def diff_range(root: Path, base: str = "auto") -> tuple:
    """(git diff arguments, label) for the change under review.

    auto: uncommitted changes if there are any, else this branch against the
    default branch (merge base), else the last commit.
    """
    if base and base != "auto":
        if not re.fullmatch(r"[\w./@^~{}-]+", base) or base.startswith("-"):
            raise ValueError(f"invalid --diff base {base!r}")
        return [base + "...HEAD"] if "..." not in base and ".." not in base else [base], base
    if _uncommitted(root):
        return ["HEAD"], "uncommitted changes"
    default = _default_base(root)
    if default:
        return [default + "...HEAD"], f"{default}...HEAD"
    if git(root, "rev-parse", "--verify", "--quiet", "HEAD~1") is not None:
        return ["HEAD~1", "HEAD"], "last commit"
    return [], ""


def review_diff(root: Path, base: str = "auto") -> dict:
    """Changed files with line counts and the review areas the change touches."""
    args, label = diff_range(root, base)
    if not args:
        return {}
    numstat = git(root, "diff", "--numstat", "--no-renames", *args)
    if numstat is None:
        return {"label": label, "error": f"git diff {' '.join(args)} failed (unknown base?)"}
    files = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added = int(parts[0]) if parts[0].isdigit() else 0
            removed = int(parts[1]) if parts[1].isdigit() else 0
            files.append({"file": parts[2], "added": added, "removed": removed})

    patch = (git(root, "diff", "-U0", "--no-renames", *args) or "")[:400000]
    added_by_file, current = {}, None
    for line in patch.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and current:
            added_by_file.setdefault(current, []).append(line[1:])

    if args == ["HEAD"]:
        # New files not yet added to git are part of the uncommitted change too
        untracked = git(root, "ls-files", "--others", "--exclude-standard") or ""
        for rel in [r for r in untracked.splitlines() if not r.startswith(OWN_OUTPUT)][:50]:
            try:
                with open(root / rel, encoding="utf-8") as f:
                    lines = f.read(200000).splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            files.append({"file": rel, "added": len(lines), "removed": 0, "new": True})
            added_by_file[rel] = lines
    if not files:
        return {"label": label, "files": [], "areas": []}

    areas = []
    for area, path_rule, line_rule in AREA_RULES:
        reasons = []
        for f in files:
            # Test files are covered by the Tests area below, and legitimately contain
            # risky-looking strings; so do docs. Comments are not code.
            if TEST_PATH.search(f["file"]):
                continue
            by_path = bool(path_rule and re.search(path_rule, f["file"], re.I))
            hit = None
            if line_rule and not NO_CODE_PATH.search(f["file"]):
                hit = next((m.group(0) for text in added_by_file.get(f["file"], [])
                            if not COMMENT_LINE.match(text)
                            for m in [re.search(line_rule, text)] if m), None)
            if hit:
                reasons.append(f"{f['file']} adds `{hit.strip()}`")
            elif by_path:
                reasons.append(f["file"])
        if reasons:
            areas.append({"area": area, "reasons": reasons[:3], "count": len(reasons)})
    sources = [f["file"] for f in files if SOURCE_PATH.search(f["file"]) and not TEST_PATH.search(f["file"])]
    tests = [f["file"] for f in files if TEST_PATH.search(f["file"])]
    if sources and not tests:
        areas.append({"area": "Tests", "reasons": ["source files changed but no test files did"], "count": 1})
    elif tests:
        noun = "test file" if len(tests) == 1 else "test files"
        areas.append({"area": "Tests", "reasons": [f"{len(tests)} {noun} changed: check they test the change"],
                      "count": len(tests)})
    return {"label": label, "files": files, "areas": areas,
            "added": sum(f["added"] for f in files), "removed": sum(f["removed"] for f in files)}


# ============ PUBLIC ============
def gather(text: str, root: Path, diff: str = None) -> dict:
    """Everything the plan's context section shows. Empty parts are left out."""
    root = Path(root)
    in_git = is_git_repo(root)
    ctx = {"git": in_git}
    looks_like_code = bool(re.search(r"\.\w{1,6}:\d+|line \d+|[a-z][A-Z]|\w_\w|\.\w{1,5}\b", text))
    files = project_files(root, in_git) if looks_like_code else []
    if files:
        ctx["locations"] = trace_locations(text, files, root)
        ctx["files"] = named_files(text, files, root, exclude={loc["file"] for loc in ctx["locations"]})
    if in_git:
        ctx["symbols"] = find_symbols(candidate_symbols(text), root)
        touched = [loc["file"] for loc in ctx.get("locations", [])] + ctx.get("files", [])
        touched += [d.split(":")[0] for s in ctx["symbols"] for d in s["defined"][:1]]
        ctx["touched"] = list(dict.fromkeys(touched))
        ctx["commits"] = recent_commits(root, ctx["touched"])
        ctx["tree"] = working_tree(root)
        if diff:
            ctx["diff"] = review_diff(root, diff)
    return {k: v for k, v in ctx.items() if v or k == "git"}
