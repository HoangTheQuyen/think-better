<div align="center">

<img src="docs/images/banner.png" alt="Think Better" width="100%">

# Think Better

**Structured thinking skills for your AI coding assistant.**<br>
One CLI installs three skills and their slash commands so your AI decides with real frameworks,
solves problems with a proven method, and changes code with evidence instead of guesses.

[![Release](https://img.shields.io/github/v/release/HoangTheQuyen/think-better?style=flat-square)](https://github.com/HoangTheQuyen/think-better/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/HoangTheQuyen/think-better/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/HoangTheQuyen/think-better/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**3 skills · 323 knowledge records · 20 slash commands · 4 AI tools**

**Works with** Claude Code · GitHub Copilot · Antigravity · OpenCode

[Website](https://thinkbetter.dev/) · [User Guide](USER-GUIDE.md) · [Quick Reference](QUICK-REFERENCE.md) · [Examples](examples/README.md) · [Changelog](CHANGELOG.md) · [Tiếng Việt](#-tiếng-việt)

</div>

## Install

Pick one:

```bash
# Homebrew (macOS / Linux)
brew tap HoangTheQuyen/think-better https://github.com/HoangTheQuyen/think-better && brew install think-better

# Scoop (Windows)
scoop bucket add think-better https://github.com/HoangTheQuyen/think-better; scoop install think-better

# Install script (macOS / Linux) — installs to ~/.local/bin and verifies the SHA-256 checksum
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh

# Install script (Windows PowerShell) — installs to %LOCALAPPDATA%\think-better
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

# Go 1.25+
go install github.com/HoangTheQuyen/think-better/cmd/think-better@latest
```

Then, **inside your project**, install the skills for your AI tool:

| AI tool | Command | Skills | Slash commands |
|---------|---------|--------|----------------|
| Claude Code | `think-better init --ai claude` | `.claude/skills/` | `.claude/commands/` |
| GitHub Copilot | `think-better init --ai copilot` | `.github/prompts/<skill>/` | `.github/prompts/*.prompt.md` (agent mode) |
| Antigravity | `think-better init --ai antigravity` | `.agents/skills/` | `.agents/workflows/` |
| OpenCode | `think-better init --ai opencode` | `.opencode/skills/` | `.opencode/commands/` |

Every target gets all three skills and all 20 slash commands (`/solve*`, `/decide*`, `/code*`).
Add `--global` to install once for every project (Claude Code, OpenCode, Antigravity), or
`--skill code-solving` to install a single skill with its commands. The skills need **Python 3**
(standard library only); run `think-better check` to verify.

<details>
<summary>Pin a version, Nix, source, manual download</summary>

```bash
# Pin a release and pick the directory (no sudo needed)
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh \
  | THINK_BETTER_VERSION=v1.3.0 INSTALL_DIR="$HOME/bin" sh

# Nix
nix run github:HoangTheQuyen/think-better -- init --ai claude

# From source
git clone https://github.com/HoangTheQuyen/think-better && cd think-better && make build
```

Manual download: grab a binary from [Releases](https://github.com/HoangTheQuyen/think-better/releases)
and check it against `checksums.txt`.

</details>

## 30 seconds per skill

Talk to your AI as usual (each skill activates on its own trigger phrases) or type a slash command.

**`/decide`: choose between options**

```
/decide Postgres vs MongoDB vs DynamoDB for our order service

→ Decision type: Multi-Option Selection
→ Framework: Weighted Criteria Matrix (criteria and weights before scoring)
→ Bias warning: Framing Effect; remedy: reframe as gains and as losses
→ Checklist, then next steps: /decide.deep, /decide.exec, /solve
```

**`/solve`: get to the root of a business or product problem**

```
/solve Signups dropped 15% after the pricing change

→ Type: Wicked · Context: Business Performance
→ Process: Define → Profitability tree → Pareto prioritize → Hypothesis-driven analysis
→ Tools: Sensitivity Analysis, Benchmarking; communicate with the Pyramid Principle
→ Bias warnings: Status Quo Bias, Sunk Cost Fallacy
```

**`/code`: change code in 7 gated steps**

```
/code.debug Checkout throws "TypeError: Cannot read properties of undefined (reading 'id')"
            after yesterday's deploy. Repro: add a gift card, then pay.

→ Context from the project: src/checkout/total.js:10  const discount = cart.coupon.id ? ...
→ Known error: likely causes, what to check first, the root-cause fix
→ Steps: Define (a failing test) → Decompose → Prioritize → Plan → Execute → Verify → Communicate
→ Project checks found: npm run test, npm run lint, npm run build
```

Full walk-throughs: [examples/](examples/README.md).

## The three skills

### `/decide` — make a choice · `make-decision` · 63 records

| | |
|---|---|
| **10 decision frameworks** | Weighted Criteria Matrix, Reversibility Filter, Pre-Mortem, Pros-Cons-Fixes, Expected Value, Scenario Planning… |
| **12 cognitive biases** | Overconfidence, Anchoring, Sunk Cost, Status Quo, Confirmation… with remedies |
| **Comparison matrix** | `--matrix "A vs B vs C"` with weighted criteria |
| **Decision journal** | Record the decision, review it later with the real outcome |

### `/solve` — solve a problem · `problem-solving-pro` · 111 records

| | |
|---|---|
| **7-Step Method** | Define → Disaggregate → Prioritize → Workplan → Analyze → Synthesize → Communicate |
| **18 decomposition frameworks** | Issue Tree, Hypothesis Tree, Profitability Tree, Systems Map… |
| **13 mental models** | First Principles, Inversion, Bayesian Updating, Second-Order Thinking… |
| **10 communication patterns** | Pyramid Principle, BLUF, SCR, Action Titles… |

For bugs and other code changes use `/code`.

### `/code` — change code · `code-solving` · 149 records

| | |
|---|---|
| **7 Steps with Gates** | Define → Decompose → Prioritize → Plan → Execute → Verify → Communicate; each step needs evidence (a failing test, a change map, passing checks) before the next |
| **12 task types** | debug, feature, refactor, performance, flaky-test, incident, migration, review, test, explain, security, quick-fix |
| **Reads your project first** | Maps stack-trace frames to your files and lines, finds where named symbols are defined, lists recent commits; reviews get the diff and the risk areas it touches |
| **44 common error messages** | JS/TS, Python, Go, Java, C#, Rust, SQL and infrastructure: likely causes and what to check first |
| **Your own checks** | Finds the project's test/lint/build commands (npm/pnpm/yarn, Make, Go, Cargo, pytest via uv/Poetry, Maven/Gradle, CI steps…) for the Verify step |
| **Resumable** | Save a step-by-step workspace; `/code.resume` continues at the first unmet gate |

## Slash commands

| Skill | Commands |
|-------|----------|
| problem-solving-pro | `/solve.quick` · `/solve` · `/solve.deep` · `/solve.exec` · `/solve.resume` |
| make-decision | `/decide.quick` · `/decide` · `/decide.deep` · `/decide.exec` · `/decide.resume` |
| code-solving | `/code` · `/code.deep` · `/code.debug` · `/code.feature` · `/code.refactor` · `/code.perf` · `/code.review` · `/code.test` · `/code.explain` · `/code.resume` |

Depth: `.quick` is a fast scan, the plain command is the default, `.deep` adds alternatives and pitfalls
for high-stakes work, `.exec` adds a summary for leadership. `/code` auto-detects the task type;
`/code.deep` is the same with more techniques and the full review checklist.

Add *"save step-by-step"* to any request to get a Markdown workspace with one file per step
(`solving-plans/`, `decision-plans/` or `coding-plans/`). Saving again keeps the files you
already filled in.

## How it works

```
You ── "Revenue dropped 20%"  or  /solve.deep …  or  /code.debug …
          │
          ▼
  AI tool (Claude Code · GitHub Copilot · Antigravity · OpenCode)
   ├─ picks the skill: SKILL.md trigger phrases, or the slash command
   └─ runs the skill's script:  python3 <skills dir>/<skill>/scripts/search.py --stdin --plan
          │
          ▼
  Skill engine (local, Python 3 standard library)
   ├─ BM25 search over 323 knowledge records (CSV files shipped with the skill)
   ├─ classify: problem type · decision type · coding task type
   ├─ /code only: read the project (stack-trace frames, symbols, git log, diff, test commands)
   └─ build the plan: framework · steps and gates · bias warnings · checklist
          │
          ▼
  A structured answer + next-step commands (optionally saved as a step-by-step workspace)
```

The CLI only copies Markdown, CSV and Python files into your project (or home directory);
the scripts run locally with no network calls, accounts or API keys.

## CLI

```bash
think-better init        # Install skills and slash commands (--ai, --skill, --global, --force)
think-better list        # Skills and where they are installed (every AI tool, project + global)
think-better check       # Verify prerequisites (Python 3)
think-better uninstall   # Remove a skill and its slash commands (--skill, --global)
think-better version     # Show version
```

`THINK_BETTER_AI=claude` sets the default for `--ai`.

## Documentation

- [User Guide](USER-GUIDE.md): every skill, workflow and script option in detail
- [Quick Reference](QUICK-REFERENCE.md): one-page cheat sheet
- [Examples](examples/README.md): worked decisions, problems and a debugging session
- [Changelog](CHANGELOG.md): what changed in each release
- [Contributing](CONTRIBUTING.md): add a skill, knowledge records, a slash command or an AI tool
  (`make check` runs the same checks as CI)
- [Security](SECURITY.md): report a vulnerability

---

<div align="center">

# 🇻🇳 Tiếng Việt

**Kỹ năng tư duy có cấu trúc cho AI lập trình của bạn.**

</div>

Một CLI cài ba skill và các lệnh slash đi kèm, để AI ra quyết định bằng framework thật, giải quyết
vấn đề theo phương pháp rõ ràng và sửa code bằng bằng chứng thay vì đoán.

**3 skill · 323 bản ghi kiến thức · 20 lệnh slash · 4 công cụ AI** (Claude Code, GitHub Copilot, Antigravity, OpenCode)

### Cài đặt

```bash
# macOS / Linux
brew tap HoangTheQuyen/think-better https://github.com/HoangTheQuyen/think-better && brew install think-better
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh     # hoặc script

# Windows
scoop bucket add think-better https://github.com/HoangTheQuyen/think-better; scoop install think-better
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex           # hoặc script

# Go 1.25+
go install github.com/HoangTheQuyen/think-better/cmd/think-better@latest

# Trong thư mục project: cài skill cho công cụ AI của bạn
think-better init --ai claude        # hoặc: --ai copilot, --ai antigravity, --ai opencode
think-better init --ai claude --global   # một lần cho mọi project (không áp dụng cho Copilot)
```

Cần **Python 3** (chỉ dùng thư viện chuẩn). Kiểm tra bằng `think-better check`.

### 3 skill

**`/decide`** — Ra quyết định · `make-decision` · 63 bản ghi
- 10 framework quyết định · 12 thiên kiến nhận thức kèm cách khắc phục · Bảng so sánh có trọng số · Nhật ký quyết định

**`/solve`** — Giải quyết vấn đề kinh doanh, sản phẩm · `problem-solving-pro` · 111 bản ghi
- 7 bước: Định nghĩa → Phân tách → Ưu tiên → Lập kế hoạch → Phân tích → Tổng hợp → Trình bày
- 18 framework phân tách · 13 mô hình tư duy · 10 mẫu trình bày

**`/code`** — Sửa và viết code có quy trình · `code-solving` · 149 bản ghi
- 7 bước có "cổng kiểm tra": phải có test fail, chạy test thật, đủ bằng chứng mới qua bước
- 12 loại việc: sửa bug, thêm tính năng, refactor, tối ưu, test chập chờn, sự cố production, nâng cấp, review code, viết test, giải thích code, vá lỗ hổng bảo mật, sửa nhỏ
- Đọc project trước: map stack trace ra file:dòng, tìm nơi định nghĩa hàm/class, commit gần đây; review thì lấy diff và chỉ ra vùng rủi ro
- Nhận ra 44 thông báo lỗi hay gặp (JS/TS, Python, Go, Java, C#, Rust, SQL, hạ tầng) và tự tìm lệnh test/lint/build của project
- Lưu workspace từng bước và làm tiếp ở phiên sau với `/code.resume`

### Lệnh slash

| Skill | Lệnh |
|-------|------|
| problem-solving-pro | `/solve.quick` · `/solve` · `/solve.deep` · `/solve.exec` · `/solve.resume` |
| make-decision | `/decide.quick` · `/decide` · `/decide.deep` · `/decide.exec` · `/decide.resume` |
| code-solving | `/code` · `/code.deep` · `/code.debug` · `/code.feature` · `/code.refactor` · `/code.perf` · `/code.review` · `/code.test` · `/code.explain` · `/code.resume` |

`.quick` quét nhanh, lệnh gốc là mặc định, `.deep` phân tích sâu cho việc quan trọng, `.exec` thêm tóm tắt cho lãnh đạo.

```
/decide.deep Nên dùng AWS hay Azure hay GCP?
/solve.quick Lượt đăng ký giảm 15% sau khi đổi giá
/code.debug Đăng nhập bị lỗi 500 sau khi deploy
/code.feature Thêm xuất file CSV cho trang báo cáo
```

Thêm *"save step-by-step"* (lưu từng bước) vào yêu cầu để có workspace Markdown mỗi bước một file.

### Lưu ý

- Knowledge base bằng tiếng Anh: AI tự dịch từ khóa trước khi tìm kiếm.
- Tài liệu chi tiết: [User Guide](USER-GUIDE.md) · [Quick Reference](QUICK-REFERENCE.md) · [Ví dụ](examples/README.md)
- Muốn đóng góp skill/framework mới? Xem [CONTRIBUTING.md](CONTRIBUTING.md) (PR bằng tiếng Việt cũng được).

---

<div align="center">

**MIT License** · Built by [HoangTheQuyen](https://github.com/HoangTheQuyen)

**[⭐ Star](https://github.com/HoangTheQuyen/think-better)** if Think Better helped you think better.

</div>
