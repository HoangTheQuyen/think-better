<div align="center">

<img src="docs/images/banner.png" alt="Think Better" width="100%">

# Think Better

**Your AI writes code fast but makes terrible decisions.**<br>
Think Better injects structured decision frameworks directly into your AI prompts.

[![Go 1.25](https://img.shields.io/badge/Go-1.25-00ADD8?style=flat-square&logo=go&logoColor=white)](https://golang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![2 AI Skills](https://img.shields.io/badge/AI_Skills-2-blueviolet?style=flat-square)](.)
[![10+ Frameworks](https://img.shields.io/badge/Frameworks-10+-orange?style=flat-square)](.)  
[![15 Decomposition](https://img.shields.io/badge/Decomposition-15-teal?style=flat-square)](.)
[![12 Biases](https://img.shields.io/badge/Biases-12-red?style=flat-square)](.)
[![4 Depth Levels](https://img.shields.io/badge/Depth-4_Levels-ff69b4?style=flat-square)](.)

[Website](https://thinkbetter.dev/) · [Documentation](USER-GUIDE.md) · [Quick Reference](QUICK-REFERENCE.md) · [Contributing](CONTRIBUTING.md)

**Works with** Claude Code · GitHub Copilot · Antigravity · OpenCode

</div>

<br>

## The Problem

You ask your AI *"Should we migrate to microservices?"* and get a generic pros/cons list. No framework. No bias detection. No structured analysis. Just vibes.

**Think Better fixes this.** It gives your AI access to 10 decision frameworks, 15 decomposition methods, 12 cognitive bias detectors, and 160 knowledge records — turning surface-level responses into structured, rigorous analysis.

<br>

## Quick Start

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

# Homebrew (macOS / Linux)
brew install HoangTheQuyen/tap/think-better

# Scoop (Windows)
scoop bucket add think-better https://github.com/HoangTheQuyen/scoop-bucket
scoop install think-better
```

The installers download the right binary for your OS/CPU and verify its SHA-256 checksum.
Pin a version or change the location with environment variables, e.g.
`curl -fsSL .../install.sh | THINK_BETTER_VERSION=v1.0.3 INSTALL_DIR=/usr/local/bin sh`.

Then, **inside your project**, install the skills for your AI:

```bash
think-better init --ai claude        # Claude Code   → .claude/skills + /solve, /decide commands
think-better init --ai copilot       # GitHub Copilot → .github/prompts
think-better init --ai antigravity   # Antigravity   → .agents/skills + workflows
think-better init --ai opencode      # OpenCode      → .opencode/skills
```

<details>
<summary>Other install methods</summary>

```bash
# Go 1.25+
go install github.com/HoangTheQuyen/think-better/cmd/think-better@latest

# Nix
nix run github:HoangTheQuyen/think-better -- init --ai claude

# From source
git clone https://github.com/HoangTheQuyen/think-better && cd think-better && make build
```

Manual download: grab a binary from [Releases](https://github.com/HoangTheQuyen/think-better/releases) and check it against `checksums.txt`.

</details>

<br>

## How It Works

Just talk to your AI naturally. Think Better auto-activates when it detects a decision or problem:

```
You: "Should we migrate from React to Next.js for our main app?"

AI:  → Detects: Binary Choice
     → Framework: Reversibility Filter
     → Warns: Overconfidence Bias, Status Quo Bias, Sunk Cost
     → Generates: Weighted comparison matrix + action plan
```

```
You: "Revenue dropped 20% despite market growth"

AI:  → Detects: Opportunity Gap
     → Decomposition: Profitability Tree (MECE)
     → Analysis: Root Cause (5 Whys) + Fermi Estimation
     → Warns: Anchoring Bias, Confirmation Bias
```

<br>

## Two Skills

### `/decide` — For Choices

> *"choose", "compare", "should I", "pros and cons", "nên chọn cái nào", "phân vân"*

| | |
|---|---|
| **10 Frameworks** | Reversibility Filter, Weighted Matrix, Hypothesis-Driven, Pre-Mortem, Pros-Cons-Fixes... |
| **12 Bias Warnings** | Overconfidence, Anchoring, Sunk Cost, Status Quo, Confirmation... |
| **Comparison Matrix** | `--matrix "A vs B vs C"` with weighted scoring |
| **Decision Journal** | Track → Review → Improve calibration |

### `/solve` — For Problems

> *"solve", "debug", "root cause", "I'm stuck", "tại sao bị vậy", "không biết làm sao"*

| | |
|---|---|
| **7-Step Method** | Define → Decompose → Prioritize → Analyze → Synthesize → Communicate |
| **15 Decomposition Frameworks** | Issue Tree, MECE, Hypothesis Tree, Profitability Tree, Systems Map... |
| **12 Mental Models** | First Principles, Inversion, Bayesian Updating, Pareto... |
| **10 Communication Patterns** | Pyramid Principle, BLUF, SCR, Action Titles... |

<br>

## Depth Levels

Control analysis depth with slash commands:

| Command | Depth | Records | Best For |
|---------|-------|---------|----------|
| `/solve.quick` · `/decide.quick` | Quick | 0.5× | Fast scan, simple problems |
| `/solve` · `/decide` | Standard | 1.0× | Default for most situations |
| `/solve.deep` · `/decide.deep` | Deep | 1.7× | Complex, high-stakes decisions |
| `/solve.exec` · `/decide.exec` | Executive | 2.5× | Board reports, stakeholder briefings |

**Examples:**
```
/solve.quick API latency spiked after deploy
/decide.deep AWS vs Azure vs GCP for cloud migration
/solve.exec Revenue declined 20% quarter over quarter
```

<br>

## Architecture

```
YOU ─── "Revenue dropped 20%" ──────────────────────────────────┐
                                                                │
  ┌─────────────────────────────────────────────────────────────▼──┐
  │  AI ASSISTANT (Claude / Copilot / Antigravity)                 │
  │                                                                │
  │  ┌─ Auto-detect ──────────┐    ┌─ Slash Command ────────────┐ │
  │  │ SKILL.md triggers      │ OR │ /solve.deep → deep mode    │ │
  │  │ "solve" → problem-pro  │    │ /decide.quick → quick mode │ │
  │  └────────────┬───────────┘    └────────────┬───────────────┘ │
  │               └───────────┬────────────────┘                  │
  │                           ▼                                    │
  │  ┌────────────────────────────────────────────────────────┐   │
  │  │  🐍 BM25 Search Engine                                 │   │
  │  │  160 records × depth multiplier (0.5× → 2.5×)         │   │
  │  └────────────────────────┬───────────────────────────────┘   │
  │                           ▼                                    │
  │  ┌────────────────────────────────────────────────────────┐   │
  │  │  📋 Advisor Engine                                      │   │
  │  │  Classify → Framework → Bias Detection → Plan          │   │
  │  └────────────────────────┬───────────────────────────────┘   │
  │                           ▼                                    │
  │  📄 Structured Output + Next-step suggestions                 │
  └───────────────────────────────────────────────────────────────┘
```

<br>

## Step-by-Step Workspace

Add *"save step-by-step"* to any prompt to generate a full markdown workspace:

```
solving-plans/project/               decision-plans/project/
├── 00-OVERVIEW.md                   ├── 00-OVERVIEW.md
├── 01-PROBLEM-DEFINITION.md         ├── 01-DECISION-TYPE.md
├── 02-DECOMPOSITION.md              ├── 02-FRAMEWORK.md
├── 03-PRIORITIZATION.md             ├── 03-CRITERIA.md
├── 04-ANALYSIS-PLAN.md              ├── 04-ANALYSIS.md
├── 05-FINDINGS.md                   ├── 05-OPTIONS.md
├── 06-SYNTHESIS.md                  ├── 06-DECISION.md
├── 07-RECOMMENDATION.md             ├── BIAS-WARNINGS.md
├── BIAS-WARNINGS.md                 └── DECISION-LOG.md
└── DECISION-LOG.md
```

<br>

## CLI Commands

```bash
think-better init             # Install skills for your AI (--ai, --skill, --force)
think-better list             # Show installed skills
think-better check            # Verify prerequisites (Python 3)
think-better uninstall        # Remove skills
think-better version          # Show version
```

<br>

## Project Structure

```
think-better/
├── .agents/                     # ✏️  Source of truth — edit skills & workflows here
│   ├── skills/
│   │   ├── make-decision/       # Decision skill (SKILL.md, scripts, CSVs)
│   │   └── problem-solving-pro/ # Problem-solving skill
│   └── workflows/               # Slash commands (/solve, /decide, ...)
├── cmd/think-better/            # CLI entry point (Go)
├── internal/
│   ├── skills/                  # Auto-discovered registry + generated embed mirror
│   ├── targets/                 # AI platform definitions
│   ├── installer/               # Install/uninstall logic
│   └── cli/                     # Command handlers
├── scripts/                     # Dev tooling (skill smoke tests)
└── specs/                       # Specifications
```

New skills are picked up automatically from `.agents/skills/<name>/SKILL.md` — see
[Adding a new skill](CONTRIBUTING.md#adding-a-new-skill).

<br>

## Requirements

| Method | Requirements |
|--------|-------------|
| Binary download / Homebrew / Scoop | None — just run |
| `go install` | Go 1.25+ |
| Nix | Nix with flakes |
| Build from source | Go 1.25+ |
| Running skills | Python 3 |

<br>

## Contributing

Contributions of new skills, frameworks, biases and AI targets are very welcome.

```bash
make embed-prep   # mirror .agents/ into the embedded copy
make check        # the same checks CI runs (Go tests + Python smoke tests)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

<br>

---

<div align="center">

# 🇻🇳 Tiếng Việt

**Ngừng Đoán Mò. Bắt Đầu Tư Duy Có Cấu Trúc.**

AI viết code nhanh nhưng ra quyết định tệ.<br>
Think Better tiêm framework tư duy vào prompt — biến AI thành Staff Engineer.

</div>

### Cài Đặt

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh
brew install HoangTheQuyen/tap/think-better      # hoặc Homebrew

# Windows
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
scoop bucket add think-better https://github.com/HoangTheQuyen/scoop-bucket; scoop install think-better   # hoặc Scoop

# Cài skill
think-better init --ai claude
```

### Cách Dùng

Nói chuyện với AI bình thường — Think Better tự kích hoạt:

| Bạn Nói | AI Làm |
|---------|--------|
| *"Nên chọn công ty lớn hay startup?"* | `make-decision` → Weighted Matrix, cảnh báo Status Quo Bias |
| *"So sánh React vs Vue vs Angular"* | Bảng so sánh với tiêu chí có trọng số |
| *"Tại sao doanh thu giảm?"* | `problem-solving-pro` → Issue Tree, Root Cause Analysis |
| *"Bị kẹt, không biết làm sao"* | 7 bước: Định nghĩa → Phân tách → Ưu tiên → Phân tích |

### 2 Skill

**`/decide`** — Chọn lựa
- 10 framework · 12 bias · So sánh đa tiêu chí · Nhật ký quyết định

**`/solve`** — Giải quyết vấn đề
- 7 bước McKinsey · 15 framework phân tách · 12 mô hình tư duy

### Slash Commands

| Lệnh | Khi Nào |
|------|---------|
| `/solve.quick` · `/decide.quick` | Scan nhanh |
| `/solve` · `/decide` | Phân tích chuẩn |
| `/solve.deep` · `/decide.deep` | Phức tạp, high-stakes |
| `/solve.exec` · `/decide.exec` | Báo cáo cho leadership |

```
/solve.quick API chậm sau deploy
/decide.deep Nên dùng AWS hay Azure hay GCP?
```

### Lưu Ý

- Knowledge base tiếng Anh — AI tự dịch keyword trước khi search
- Cần **Python 3** cho script phân tích
- Hỗ trợ **Claude Code, Copilot, Antigravity, OpenCode**
- Muốn đóng góp skill/framework mới? Xem [CONTRIBUTING.md](CONTRIBUTING.md)

---

<div align="center">

**MIT License** · Built by [HoangTheQuyen](https://github.com/HoangTheQuyen)

**[⭐ Star](https://github.com/HoangTheQuyen/think-better)** if Think Better helped you think better.

</div>
