#!/usr/bin/env python3
"""Keep the docs honest.

Checks that the numbers in README.md, USER-GUIDE.md, QUICK-REFERENCE.md and
the website (docs/index.html) match the repository, and that relative links in
the Markdown docs resolve:

- knowledge records: rows of .agents/skills/*/data/*.csv, per skill and in total
- a few named counts (decision frameworks, criteria templates, error messages,
  task types, ...)
- slash commands: files in .agents/workflows/; README and the guides list every
  one, and every /solve, /decide or /code command the docs mention exists
- AI tools: the targets in internal/targets/target.go, and the install paths in
  the README and USER-GUIDE tables match each target's paths there
- CLI commands: README and USER-GUIDE mention every think-better subcommand
  (cmd/think-better/main.go)
- bias names in the docs' bias tables exist in a skill's biases CSV
- the sample outputs in the docs match a real run (scripts/test_doc_samples.py)
- the version in Formula/think-better.rb has a CHANGELOG.md section
- relative links and #anchors in the Markdown docs point at existing files
  and headings inside the repository

Run: python3 scripts/test_docs.py   (standard library only, Python 3.9+)
When it fails after you add records or commands, update the numbers it names.
"""

import csv
import re
import sys
from pathlib import Path

import test_doc_samples  # noqa: E402 - same directory as this script

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".agents" / "skills"
WORKFLOWS_DIR = ROOT / ".agents" / "workflows"
TARGETS_GO = ROOT / "internal" / "targets" / "target.go"
MAIN_GO = ROOT / "cmd" / "think-better" / "main.go"
USER_GUIDE = ROOT / "USER-GUIDE.md"
README = ROOT / "README.md"
# Guides checked like the README, except that they need not repeat every count.
GUIDES = [ROOT / "USER-GUIDE.md", ROOT / "QUICK-REFERENCE.md"]
WEBSITE = ROOT / "docs" / "index.html"
CHANGELOG = ROOT / "CHANGELOG.md"
FORMULA = ROOT / "Formula" / "think-better.rb"

# How the docs name each AI target (internal/targets/target.go Name -> docs).
TARGET_DISPLAY = {
    "claude": "Claude Code",
    "copilot": "GitHub Copilot",
    "antigravity": "Antigravity",
    "opencode": "OpenCode",
}

# "<number> <phrase>" in README.md must equal the rows of this CSV.
# (regex for the phrase, skill, CSV file in that skill's data/)
NAMED_COUNTS = [
    (r"decision frameworks|framework quyết định", "make-decision", "decision-frameworks.csv"),
    (r"cognitive biases|thiên kiến nhận thức", "make-decision", "cognitive-biases.csv"),
    (r"decomposition frameworks|framework phân tách", "problem-solving-pro", "decomposition.csv"),
    (r"mental models|mô hình tư duy", "problem-solving-pro", "heuristics.csv"),
    (r"communication patterns|mẫu trình bày", "problem-solving-pro", "communication.csv"),
    (r"task types|loại việc", "code-solving", "task-types.csv"),
    (r"(?:common )?error messages|thông báo lỗi(?: hay gặp)?", "code-solving", "errors.csv"),
    (r"decision types|loại quyết định", "make-decision", "decision-types.csv"),
    (r"criteria templates|mẫu tiêu chí", "make-decision", "criteria-templates.csv"),
    (r"analysis techniques", "make-decision", "analysis-techniques.csv"),
    (r"facilitation techniques", "make-decision", "facilitation.csv"),
]

# Biases the docs may name in a bias table: the first column of a table whose
# header starts with "Bias", or the cells of a column headed "Biases".
BIAS_CSVS = [
    ("make-decision", "cognitive-biases.csv"),
    ("problem-solving-pro", "cognitive-biases.csv"),
    ("code-solving", "biases.csv"),
]
BIAS_DOCS = ["README.md", "USER-GUIDE.md", "QUICK-REFERENCE.md"]
BIAS_GLOBS = ["examples/*.md"]

# Markdown files whose relative links must resolve.
LINKED_DOCS = [
    "README.md", "USER-GUIDE.md", "QUICK-REFERENCE.md", "CONTRIBUTING.md",
    "SECURITY.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md",
]
LINKED_GLOBS = ["docs/**/*.md", "examples/*.md"]

# Files whose /solve, /decide and /code mentions must be real commands.
COMMAND_DOCS = ["README.md", "USER-GUIDE.md", "QUICK-REFERENCE.md", "docs/index.html"]
COMMAND_GLOBS = ["examples/*.md"]

errors = []


def fail(msg):
    errors.append(msg)


def rel(path):
    return path.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- repo facts

def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.reader(fh) if any(cell.strip() for cell in r)]
    return max(len(rows) - 1, 0)


def skill_records():
    """{skill: {csv name: rows}} for every skill with a SKILL.md."""
    out = {}
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skill = skill_md.parent
        out[skill.name] = {p.name: csv_rows(p) for p in sorted((skill / "data").glob("*.csv"))}
    return out


def workflows():
    return sorted(p.stem for p in WORKFLOWS_DIR.glob("*.md"))


def targets():
    return re.findall(r'^\s*Name:\s*"([a-z0-9-]+)"', TARGETS_GO.read_text(encoding="utf-8"), re.M)


def target_paths():
    """{name: {"install": ..., "workflow": ..., "global": ...}} from target.go
    (each entry's fields up to the next Name:)."""
    text = TARGETS_GO.read_text(encoding="utf-8")
    out = {}
    blocks = re.split(r'^\s*Name:\s*"', text, flags=re.M)[1:]
    for block in blocks:
        name = block.split('"', 1)[0]
        fields = dict(re.findall(r'^\s*(\w+):\s*"([^"]*)"', block, re.M))
        out[name] = {
            "install": fields.get("InstallPattern", ""),
            "workflow": fields.get("WorkflowPattern", ""),
            "global": fields.get("GlobalInstallPattern", ""),
        }
    return out


def cli_commands():
    """Subcommand names from the command map in cmd/think-better/main.go."""
    return re.findall(r'^\s*"([a-z-]+)":\s*cli\.Run', MAIN_GO.read_text(encoding="utf-8"), re.M)


# ---------------------------------------------------------------- helpers

def strip_code_blocks(text):
    """Markdown without fenced code blocks."""
    return re.sub(r"^([ \t]*)(```|~~~).*?^\1\2[^\n]*$", "", text, flags=re.M | re.S)


def strip_code(text):
    """Markdown without fenced code blocks and inline code (for link checks)."""
    text = re.sub(r"^([ \t]*)(```|~~~).*?^\1\2[^\n]*$", "", text, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def numbers(pattern, text):
    return [int(m) for m in re.findall(pattern, text, flags=re.I)]


def expect_all(label, where, found, want, required=True):
    if required and not found:
        fail(f"{where}: no mention of {label} (expected {want})")
    for n in found:
        if n != want:
            fail(f"{where}: says {n} {label}, the repository has {want}")


# ---------------------------------------------------------------- count checks

def check_counts(path, text, records, commands, target_names, full, required=True):
    """full: also slash commands, AI tools, skills, named counts and steps.
    required: the main counts must be mentioned at all (README, website)."""
    where = rel(path)
    total = sum(sum(c.values()) for c in records.values())

    expect_all("knowledge records", where,
               numbers(r"(\d+)\s+(?:knowledge records|bản ghi kiến thức)", text), total, required)

    # Any other "<n> records" must be the total or one skill's count.
    allowed = {total} | {sum(c.values()) for c in records.values()}
    for n in numbers(r"(\d+)\s+(?:[a-z-]+\s+)?(?:records|bản ghi)\b", text):
        if n not in allowed:
            fail(f"{where}: says {n} records, the repository has {total} "
                 f"(per skill: {sorted(allowed - {total})})")

    for skill, counts in records.items():
        found = numbers(
            rf"{re.escape(skill)}(?:`|</code>)?[\s`·:—–\-]*(\d+)\s+(?:records|bản ghi)", text)
        expect_all(f"records for {skill}", where, found, sum(counts.values()), required)

    for name, display in ((t, TARGET_DISPLAY.get(t)) for t in target_names):
        if display is None:
            fail(f"scripts/test_docs.py: add a display name for target {name!r} to TARGET_DISPLAY")
            continue
        if display not in text:
            fail(f"{where}: does not mention {display}")
        if f"--ai {name}" not in text:
            fail(f"{where}: does not show `think-better init --ai {name}`")

    if re.search(r"install\.sh\s*\|\s*bash", text):
        fail(f"{where}: install.sh is a POSIX sh script, pipe it to `sh`, not `bash`")

    if not full:
        return

    expect_all("slash commands", where,
               numbers(r"(\d+)\s+(?:slash commands|lệnh slash)", text), len(commands), required)
    expect_all("AI tools", where,
               numbers(r"(\d+)\s+(?:AI tools|công cụ AI)", text), len(target_names), required)
    expect_all("skills", where, numbers(r"\b(\d+)\s+skills?\b", text), len(records), required)

    for phrase, skill, csv_name in NAMED_COUNTS:
        want = records.get(skill, {}).get(csv_name)
        if want is None:
            fail(f"scripts/test_docs.py: {skill}/data/{csv_name} not found")
            continue
        expect_all(phrase.split("|")[0], where,
                   numbers(rf"(\d+)\s+(?:{phrase})\b", text), want, required=False)

    steps = {records[s].get("steps.csv") for s in records if "steps.csv" in records[s]}
    for n in numbers(r"\b(\d+)[- ](?:steps?|bước)\b", text):
        if n not in steps:
            fail(f"{where}: says {n} steps, the skills have {sorted(steps)}")
    # Table rows like "| **7-Step Method** | A → B → ... |" must list that many steps.
    for m in re.finditer(r"^\|\s*\*\*(\d+)[- ]Steps?\b[^|]*\|\s*([^|\n]+)", text, re.M | re.I):
        listed = [s for s in m.group(2).split(";")[0].split("→") if s.strip()]
        if len(listed) != int(m.group(1)):
            fail(f"{where}: '{m.group(0).strip()[:40]}...' lists {len(listed)} steps, not {m.group(1)}")

    for cmd in commands:
        if not re.search(rf"(?<![\w/.]){re.escape('/' + cmd)}(?![\w.-])", text):
            fail(f"{where}: slash command /{cmd} is not mentioned")


# ---------------------------------------------------------------- install paths

def table_row(text, display, must_follow=""):
    """The first Markdown table row whose first cell is display (and whose
    second cell starts with must_follow), or None."""
    m = re.search(rf"^\|\s*{re.escape(display)}\s*\|\s*{re.escape(must_follow)}[^\n]*$", text, re.M)
    return m.group(0) if m else None


def check_install_paths(paths):
    """The README install table and the USER-GUIDE "Where the files go" table
    show each target's current paths."""
    readme = README.read_text(encoding="utf-8")
    guide = USER_GUIDE.read_text(encoding="utf-8")
    for name, p in paths.items():
        display = TARGET_DISPLAY.get(name)
        if display is None or not p["install"]:
            continue
        skills_root = p["install"].replace("{skill}/", "")
        skill_dir = p["install"].replace("{skill}", "<skill>")
        for where, row, want in (
            ("README.md install table", table_row(readme, display, f"`think-better init --ai {name}`"),
             [skills_root, p["workflow"]]),
            ("USER-GUIDE.md 'Where the files go' table", table_row(guide, display, "`."),
             [skill_dir, p["workflow"]] + (["~/" + p["global"].replace("{skill}/", "")] if p["global"] else [])),
        ):
            if row is None:
                fail(f"{where}: no row for {display}")
                continue
            for path in filter(None, want):
                if f"`{path}" not in row:
                    fail(f"{where}: the {display} row does not show `{path}` "
                         "(internal/targets/target.go)")


def check_cli_commands(commands):
    for path in (README, USER_GUIDE):
        text = path.read_text(encoding="utf-8")
        for cmd in commands:
            if not re.search(rf"think-better {re.escape(cmd)}\b", text):
                fail(f"{rel(path)}: does not mention `think-better {cmd}` (cmd/think-better/main.go)")


# ---------------------------------------------------------------- bias names

def known_biases(records_dir=SKILLS_DIR):
    """Bias names from the skills' CSVs, lowercased, with and without the
    trailing Bias / Effect / Fallacy / Heuristic ("Anchoring" = "Anchoring Effect")."""
    names = set()
    for skill, csv_name in BIAS_CSVS:
        path = records_dir / skill / "data" / csv_name
        if not path.exists():
            fail(f"scripts/test_docs.py: {skill}/data/{csv_name} not found")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                name = (row.get("Bias") or "").strip().lower()
                if name:
                    names.add(name)
                    names.add(re.sub(r"\s+(?:bias|effect|fallacy|heuristic)$", "", name))
    return names


def table_biases(text):
    """Bias names in the bias tables of a Markdown doc."""
    found = []
    header = None
    for line in strip_code_blocks(text).splitlines():
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.strip("* ").lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        for i, cell in enumerate(cells[:len(header)]):
            if (i == 0 and header[0] == "bias") or header[i] == "biases":
                found += [n.strip("* ").strip() for n in cell.split(",") if n.strip("* ").strip()]
    return found


def check_bias_names(path, names):
    for bias in table_biases(path.read_text(encoding="utf-8")):
        if bias.lower() not in names:
            fail(f"{rel(path)}: bias '{bias}' is not in any skill's biases CSV "
                 f"({', '.join(f'{s}/data/{c}' for s, c in BIAS_CSVS)})")


# ---------------------------------------------------------------- slash commands

def check_command_mentions(path, commands):
    text = path.read_text(encoding="utf-8")
    pattern = r"(?<![\w/.:\-])/((?:solve|decide|code)(?:\.[a-z]+)?)(?![\w/\-])"
    for name in sorted(set(re.findall(pattern, text))):
        if name not in commands:
            fail(f"{rel(path)}: mentions /{name}, which is not in .agents/workflows/")


# ---------------------------------------------------------------- links

def slug(heading):
    """GitHub's heading anchor: lowercase, drop punctuation, spaces to dashes."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)  # links -> their text
    text = re.sub(r"<[^>]+>", "", text).replace("`", "").strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path, cache={}):  # noqa: B006 - deliberate memo
    if path not in cache:
        found, seen = set(), {}
        for line in strip_code(path.read_text(encoding="utf-8")).splitlines():
            m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
            if not m:
                continue
            base = slug(m.group(1))
            n = seen.get(base, 0)
            seen[base] = n + 1
            found.add(base if n == 0 else f"{base}-{n}")
        cache[path] = found
    return cache[path]


def check_links(path):
    text = strip_code(path.read_text(encoding="utf-8"))
    targets_ = re.findall(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", text)
    targets_ += re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", text, re.M)
    targets_ += re.findall(r"\b(?:src|href)=\"([^\"]+)\"", text)
    for target in targets_:
        if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.I) or target.startswith("//"):
            continue  # http:, https:, mailto:, ...
        file_part, _, fragment = target.partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        try:
            dest.relative_to(ROOT)
        except ValueError:
            fail(f"{rel(path)}: link '{target}' points outside the repository")
            continue
        if not dest.exists():
            fail(f"{rel(path)}: link '{target}' does not resolve ({rel(dest)} is missing)")
            continue
        if fragment and dest.suffix == ".md" and fragment.lower() not in anchors(dest):
            fail(f"{rel(path)}: link '{target}': no heading '#{fragment}' in {rel(dest)}")


def check_site_assets():
    text = WEBSITE.read_text(encoding="utf-8")
    for target in re.findall(r"\b(?:src|href)=\"([^\"#]+)\"", text):
        if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.I) or target.startswith("//"):
            continue
        if not (WEBSITE.parent / target.lstrip("/")).exists():
            fail(f"{rel(WEBSITE)}: '{target}' does not exist in docs/")


# ---------------------------------------------------------------- changelog

def check_changelog():
    if not CHANGELOG.exists():
        fail("CHANGELOG.md is missing")
        return
    text = CHANGELOG.read_text(encoding="utf-8")
    if not re.search(r"^## \[Unreleased\]", text, re.M):
        fail("CHANGELOG.md: no '## [Unreleased]' section")
    if FORMULA.exists():
        m = re.search(r'^\s*version "([^"]+)"', FORMULA.read_text(encoding="utf-8"), re.M)
        if m and not re.search(rf"^## \[{re.escape(m.group(1))}\]", text, re.M):
            fail(f"CHANGELOG.md: no section for the released version {m.group(1)} "
                 "(Formula/think-better.rb); move the Unreleased notes under it")


# ---------------------------------------------------------------- main

def doc_files(names, globs):
    files = [ROOT / n for n in names if (ROOT / n).exists()]
    for pattern in globs:
        files += sorted(ROOT.glob(pattern))
    return files


def main():
    records = skill_records()
    commands = workflows()
    target_names = targets()
    if not records or not commands or not target_names:
        print("could not read skills, workflows or targets; run from a full checkout")
        return 1

    check_counts(README, README.read_text(encoding="utf-8"), records, commands, target_names, True)
    check_counts(WEBSITE, WEBSITE.read_text(encoding="utf-8"), records, commands, target_names, False)
    for guide in GUIDES:
        check_counts(guide, guide.read_text(encoding="utf-8"), records, commands, target_names,
                     True, required=False)
    check_install_paths(target_paths())
    subcommands = cli_commands()
    if not subcommands:
        fail("scripts/test_docs.py: no subcommands found in cmd/think-better/main.go")
    check_cli_commands(subcommands)
    names = known_biases()
    for path in doc_files(BIAS_DOCS, BIAS_GLOBS):
        check_bias_names(path, names)
    test_doc_samples.check(fail)
    check_site_assets()
    for path in doc_files(COMMAND_DOCS, COMMAND_GLOBS):
        check_command_mentions(path, commands)
    for path in doc_files(LINKED_DOCS, LINKED_GLOBS):
        check_links(path)
    check_changelog()

    total = sum(sum(c.values()) for c in records.values())
    per_skill = ", ".join(f"{s} {sum(c.values())}" for s, c in records.items())
    print(f"records: {total} ({per_skill}); slash commands: {len(commands)}; "
          f"AI tools: {len(target_names)} ({', '.join(target_names)})")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("docs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
