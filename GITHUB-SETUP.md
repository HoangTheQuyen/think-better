# GitHub Setup Guide for think-better

## Step-by-Step GitHub Creation

### 1. Create New Repository on GitHub

**URL:** https://github.com/new

**Fill in:**

| Field | Value |
|-------|-------|
| **Repository name** | `think-better` |
| **Description** | AI-powered decision-making framework & problem-solving toolkit. 10+ frameworks, cognitive bias detection, critical thinking skills for Claude AI & GitHub Copilot. Career, business, life decisions. |
| **Visibility** | Public |
| **Initialize with:** | ✅ Add .gitignore (Go) |
| **License** | MIT License |

---

### 2. Repository Settings

**General → About**
- ☑️ Add description: "AI-powered decision-making framework & problem-solving toolkit with cognitive bias detection for Claude AI & GitHub Copilot"
- ☑️ Add website: `https://htrbao.github.io/think-better`

**Manage access → Collaborators** (optional, for future contributors)
- Add fellow maintainers here

---

### 3. Repository Topics (for SEO/Discoverability)

Go to **Settings → General → Repository topics**

Add these topics:
```
decision-making
decision-making-framework
problem-solving
problem-solving-toolkit
critical-thinking
cognitive-bias
ai-assistant
ai-prompts
claude-ai
github-copilot
strategic-planning
career-development
business-strategy
thinking-tools
reasoning-framework
cli-tool
go-cli
cross-platform
open-source
```

---

### 4. Create GitHub Discussions (Optional, for Community)

**Settings → Features → Discussions** → ✅ Enable

Creates:
- Announcements
- General discussion
- Ideas
- Show and tell

---

### 5. Create GitHub Pages (Optional, for Docs Site)

**Settings → GitHub Pages → Source:** `main` branch

Then create `docs/` folder with Markdown files that auto-convert to HTML.

---

## Local Repository Setup

### 1. Clone Your New Repo

```bash
cd D:\
git clone https://github.com/htrbao/think-better.git
cd think-better
```

### 2. Move Files from Old to New

```bash
# Copy all files from decision-maker to think-better
# (You can skip this - just create new repo and push code to it)
```

---

## Repository Structure

```
think-better/
├── README.md                          # Main entry point
├── USER-GUIDE.md                      # Complete workflows
├── QUICK-REFERENCE.md                 # Cheat sheet
├── GITHUB-SETUP.md                    # This file
├── LICENSE                            # MIT
├── .gitignore                         # Go + OS stuff
│
├── cmd/
│   └── think-better/                  # CLI tool
│       └── main.go
│
├── internal/
│   ├── skills/
│   │   ├── registry.go
│   │   ├── embed.go
│   │   └── skills/                    # Embedded skill files
│   │       ├── make-decision/
│   │       └── problem-solving-pro/
│   │
│   ├── installer/
│   ├── targets/
│   ├── checker/
│   └── cli/
│
├── .github/
│   ├── prompts/
│   │   ├── make-decision/
│   │   └── problem-solving-pro/
│   │
│   └── workflows/                     # CI/CD (optional)
│       └── build.yml
│
├── examples/
│   ├── README.md
│   ├── 01-career-transition.md       # NEW: Career advice
│   ├── 02-business-strategy.md       # NEW: Business
│   ├── 03-hiring-decision.md         # Keep: Team
│   ├── 04-resource-allocation.md     # Keep: Resource
│   ├── 05-debugging-race-condition.md # NEW: Problem-solving
│   └── 06-10-template.md
│
├── go.mod                             # Module name
├── Makefile
└── docs/                              # (Optional) GitHub Pages
    └── index.md
```

---

## Files to Update for Brand Consistency

### Core Files (REQUIRED)

| File | What to Change |
|------|----------------|
| `README.md` | Header, taglines, description |
| `USER-GUIDE.md` | Intro, language |
| `QUICK-REFERENCE.md` | Header, context |
| `go.mod` | Module path: `github.com/htrbao/think-better` |
| `cmd/think-better/main.go` | Binary name, version string |
| `.gitignore` | Update paths for `think-better` |

### Documentation Files (OPTIONAL but recommended)

| File | Updates |
|------|---------|
| `examples/README.md` | Add career/business/life examples |
| `examples/01-*.md` | Rename/expand for universal appeal |
| Skip | Skill files in `.github/prompts/` (keep as-is) |
| Skip | Internal Go code (no need to change) |

---

## Module Path Change (Go)

### Current
```
module github.com/htrbao/think-better
```

### Should be
```
module github.com/htrbao/think-better
```

**Update in:**
- `go.mod`
- `go.sum` (auto-generated)
- Code imports (if any)

---

## Build & Release

### Build Command
```bash
make build-all
# Creates: bin/think-better-linux-amd64, etc.
```

### Create GitHub Release

1. Go to **Releases → Create a new release**
2. Tag: `v0.1.0`
3. Title: `Think Better v0.1.0 - Launch`
4. Description:
   ```markdown
   # 🎉 Think Better v0.1.0
   
   The operating system for clear thinking & better decisions.
   
   ## What's Included
   - 2 bundled skills (make-decision, problem-solving-pro)
   - 10+ decision frameworks
   - 12 cognitive bias warnings
   - 5 real-world case studies
   - Comprehensive user guide
   
   ## Download
   Pick your platform below and download the binary. No installation needed!
   
   ## Quick Start
   ```bash
   ./think-better init --ai claude
   ```
   
   Then open Claude in VS Code and type:
   ```
   @workspace /think-better Should I change jobs?
   ```
   ```

5. Upload binaries:
   - `bin/think-better-windows-amd64.exe`
   - `bin/think-better-windows-arm64.exe`
   - `bin/think-better-darwin-amd64`
   - `bin/think-better-darwin-arm64`
   - `bin/think-better-linux-amd64`
   - `bin/think-better-linux-arm64`

---

## Post-Launch Checklist

- [ ] Repo created on GitHub with correct name/description
- [ ] Topics added (13 topics for SEO)
- [ ] License set to MIT
- [ ] README.md updated with new branding
- [ ] All file references updated to `think-better`
- [ ] go.mod updated to new module path
- [ ] Build successful: `go build -o bin/think-better ./cmd/think-better`
- [ ] Release created with v0.1.0 tag
- [ ] Binaries uploaded to release
- [ ] Examples updated with universal appeal
- [ ] USER-GUIDE.md references updated
- [ ] QUICK-REFERENCE.md updated

---

## Marketing Checklist (Optional)

- [ ] Write "Show HN" post
- [ ] Tweet announcement
- [ ] Post to r/OpenSource, r/PromptEngineering
- [ ] Add to Awesome lists on GitHub
- [ ] Post to Product Hunt (optional)
- [ ] Create 1-2 minute demo video

---

## Your GitHub Username

**Replace `htrbao` with your actual GitHub username in:**
- Repository URL: `github.com/htrbao/think-better`
- Module path: `github.com/htrbao/think-better`
- URLs in docs

---

## Questions?

Common setup issues:

**Q: Clone failed?**  
A: Check you have Git installed, GitHub username correct

**Q: Permission denied on binary?**  
A: On Mac/Linux: `chmod +x bin/think-better-*`

**Q: Module import error?**  
A: Run `go mod tidy` to fix imports

---

**Ready? Let's rename everything! 🚀**
