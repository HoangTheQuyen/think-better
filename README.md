<div align="center">

# 🧠 Think Better

### **Stop Guessing. Start Deciding.**

The AI-powered brain upgrade that turns vague problems into crystal-clear action plans.
Whether you're choosing between two job offers at 2 AM, debugging a production outage, or planning a million-dollar strategy — **Think Better has a framework for that.**

[![Go](https://img.shields.io/badge/Go-1.25-00ADD8?logo=go&logoColor=white)](https://golang.org)
[![Skills](https://img.shields.io/badge/AI%20Skills-2-blueviolet)](https://github.com/HoangTheQuyen/think-better)
[![Frameworks](https://img.shields.io/badge/Frameworks-10+-orange)](https://github.com/HoangTheQuyen/think-better)
[![Biases](https://img.shields.io/badge/Cognitive%20Biases-12-red)](https://github.com/HoangTheQuyen/think-better)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Works with:** Claude AI · GitHub Copilot · Antigravity

---

*10 decision frameworks · 12 cognitive biases · 10 decomposition methods · 155 knowledge records · 32 trigger phrases (EN/VN)*

</div>

---

## 🤯 What This Actually Does

Ever stared at a problem for hours, going in circles? **Think Better injects structured thinking directly into your AI assistant.** Just describe your problem in plain language — the AI will:

1. 🎯 **Classify** what kind of decision/problem you're facing (from 18 types)
2. 🧩 **Recommend** the exact framework, criteria, and analysis method
3. ⚠️ **Warn** you about the cognitive biases that will sabotage your thinking
4. 📊 **Generate** comparison matrices, logic trees, and action plans
5. 📝 **Document** everything for future reflection

> **"I used to spend 3 hours going back and forth. Now I get a structured plan in 30 seconds."**

---

## 🚀 Quick Start

### Option 1: Download Binary (Recommended)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
```

### Option 2: Go Install

```bash
go install github.com/HoangTheQuyen/think-better/cmd/make-decision@latest
```

### Option 3: Build from Source

```bash
git clone https://github.com/HoangTheQuyen/think-better.git && cd think-better
make build          # Linux/macOS (or: bash build.sh)
.\build.ps1         # Windows
```

### Install Skills

```bash
think-better init --ai claude      # For Claude
think-better init --ai copilot     # For GitHub Copilot
think-better init --ai antigravity # For Antigravity
```

Then just talk to your AI:

```
You: "Should I take the new job offer or stay?"
AI:  [Runs make-decision → Binary Choice framework, warns about Status Quo Bias, 
      generates weighted comparison matrix]

You: "Our API latency spiked 5x after deploy, no code changes"  
AI:  [Runs problem-solving-pro → Issue Tree decomposition, Sensitivity Analysis,
      identifies Sunk Cost Fallacy risk]
```

---

## 🎯 Two Killer Skills

### `/make-decision` — For Choices

| Feature | What It Does |
|---------|-------------|
| 🧭 10 Frameworks | Hypothesis-Driven, Weighted Matrix, Pros-Cons-Fixes, Pre-Mortem... |
| 🧠 12 Bias Warnings | Confirmation, Anchoring, Sunk Cost, Status Quo, Overconfidence... |
| 📊 Comparison Matrix | `--matrix "A vs B vs C"` with weighted scoring |
| 📓 Decision Journal | Track decisions, review outcomes, improve calibration |
| 💾 Persist Plans | Save to `decision-plans/` for team reference |

**Triggers:** *"decide", "choose", "compare", "should I", "pros and cons", "nên chọn cái nào", "phân vân"*

### `/problem-solving-pro` — For Everything Else

| Feature | What It Does |
|---------|-------------|
| 🔬 7-Step Methodology | Define → Decompose → Prioritize → Analyze → Synthesize → Communicate |
| 🌳 10 Decomposition Frameworks | Issue Tree, MECE, Hypothesis Tree, Profitability Tree... |
| 🧠 12 Mental Models | First Principles, Inversion, Bayesian Updating, Leverage Points... |
| 📡 10 Communication Patterns | Pyramid Principle, BLUF, SCR, Action Titles... |
| 👥 10 Team Dynamics | Red Team, Brainstorming, Psychological Safety... |

**Triggers:** *"solve", "analyze", "debug", "root cause", "I'm stuck", "tại sao bị vậy", "không biết làm sao"*

---

## 🛠️ Commands

```bash
think-better init       # Install skills for your AI assistant
think-better list       # Show installed skills and status
think-better check      # Verify prerequisites (Python 3)
think-better uninstall  # Remove skills cleanly
think-better version    # Show version
```

---

## 📦 What's Inside

```
think-better/
├── cmd/make-decision/    # CLI entry point (Go)
├── internal/
│   ├── skills/           # Skill registry + embedded files
│   ├── targets/          # AI platform definitions (Claude, Copilot, Antigravity)  
│   ├── installer/        # Install/uninstall/status logic
│   ├── checker/          # Python prerequisite validation
│   └── cli/              # Subcommand handlers
├── .github/prompts/
│   ├── make-decision/    # Decision skill (PROMPT.md, scripts, CSVs)
│   └── problem-solving-pro/  # Problem-solving skill
├── specs/                # Detailed specifications
└── examples/             # Real-world use cases
```

**Stats:** 13 Go files (995 LOC) · 7 Python scripts (2,463 LOC) · 16 CSVs (155 records) · 4 test files (16 tests)

---

## 📋 Requirements

- **No requirements** for binary download (Option 1)
- **Go 1.25+** only if building from source (Option 3)
- **Python 3** (for skill analysis scripts)

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to fork the repo, create a branch, and submit a Pull Request.

---

## License

MIT License

---

<div align="center">

# 🇻🇳 Hướng Dẫn Tiếng Việt

### **Ngừng Đoán Mò. Bắt Đầu Ra Quyết Định Đúng.**

Công cụ AI giúp biến mọi vấn đề mơ hồ thành kế hoạch hành động rõ ràng.
Dù bạn đang **phân vân giữa 2 lời mời làm việc lúc 2 giờ sáng**, đang **debug production sập**, hay đang **lên chiến lược triệu đô** — **Think Better có framework cho tất cả.**

</div>

---

### ⚡ Cài Đặt Nhanh

**Cách 1: Tải binary (Khuyến nghị)**
```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | bash
```
```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
```

**Cách 2: Go Install**
```bash
go install github.com/HoangTheQuyen/think-better/cmd/make-decision@latest
```

**Cách 3: Build từ source**
```bash
git clone https://github.com/HoangTheQuyen/think-better.git && cd think-better
make build          # Linux/macOS
.\build.ps1         # Windows
```

**Cài skill:**
```bash
think-better init --ai claude      # Cho Claude
think-better init --ai copilot     # Cho GitHub Copilot
think-better init --ai antigravity # Cho Antigravity
```

### 💬 Cách Dùng

Chỉ cần nói chuyện với AI bình thường:

| Bạn Nói | AI Sẽ Làm |
|---------|----------|
| *"Nên chọn công ty lớn hay startup?"* | Chạy `make-decision` → Weighted Matrix, cảnh báo Status Quo Bias |
| *"So sánh React vs Vue vs Angular"* | Tạo bảng so sánh với tiêu chí có trọng số |
| *"Tại sao doanh thu giảm mà thị trường tăng?"* | Chạy `problem-solving-pro` → Issue Tree, Root Cause Analysis |
| *"Bị kẹt, không biết làm sao"* | Phân tích vấn đề theo 7 bước: Định nghĩa → Phân tách → Ưu tiên → Phân tích → Tổng hợp → Truyền đạt |

### 🎯 2 Skill Chính

**`/make-decision`** — Khi cần **chọn lựa**
- 10 framework ra quyết định (Hypothesis-Driven, Weighted Matrix, Pre-Mortem...)
- 12 thiên kiến nhận thức được phát hiện tự động
- So sánh đa tiêu chí với trọng số
- Nhật ký quyết định để cải thiện theo thời gian

**`/problem-solving-pro`** — Khi cần **giải quyết vấn đề**
- 7 bước giải quyết có hệ thống (McKinsey-style)
- 10 framework phân tách (Issue Tree, MECE, Hypothesis Tree...)
- 12 mô hình tư duy (First Principles, Inversion, Bayesian...)
- 10 pattern truyền đạt (Pyramid Principle, BLUF...)

### 📝 Lưu Ý

- Knowledge base chỉ có tiếng Anh → AI sẽ **tự dịch** từ khóa của bạn sang English trước khi search
- Cần **Python 3** để chạy script phân tích
- Hoạt động với **Claude, Copilot, và Antigravity**

### 🤝 Đóng Góp (Contributing)

Dự án này là mã nguồn mở! Nếu bạn có ý tưởng cho một AI Skill mới hoặc muốn sửa lỗi, vui lòng tham khảo chi tiết tại [CONTRIBUTING.md](CONTRIBUTING.md).
Quy trình cơ bản: Fork repo → Tạo branch mới → Cập nhật code → Push → Mở Pull Request (PR).

---

<div align="center">

**Built with ❤️ by [HoangTheQuyen](https://github.com/HoangTheQuyen)**

**[⭐ Star this repo](https://github.com/HoangTheQuyen/think-better)** if Think Better helped you make a better decision!

</div>
