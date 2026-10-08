# Quick Reference Card

## Installation & Setup

```bash
# Install the binary
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh
# Or Windows: irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

# Install skills and slash commands (in your project root)
think-better init --ai claude            # Claude Code
think-better init --ai copilot           # GitHub Copilot (agent mode: .github/skills/ + .github/prompts/)
think-better init --ai antigravity       # Antigravity
think-better init --ai opencode          # OpenCode
think-better init --ai claude --global   # once for all projects (Copilot: skills only, no slash commands)

think-better list                # what is installed where
think-better check               # Python 3 + each install: installed / outdated / modified / incomplete
think-better update --dry-run    # after upgrading the binary: what would change
think-better update              # apply; your edited files are kept, new version saved as <file>.new
think-better diff                # your edited files against their .new versions
think-better init --ai claude --exclude-command code.perf   # leave out a slash command (remembered)
think-better uninstall --skill make-decision   # finds the AI tool; keeps files you modified
think-better uninstall --all --yes             # every skill, no confirmation
```

Flags: `--ai`, `--skill`, `--global`, `--dry-run`; `--force` (init/update: replace your edits,
saving them as `.bak`; uninstall: also delete files you modified); `-y`/`--yes` (uninstall: no
confirmation, keeps your edits); `--exclude-command`/`--include-command` (init/update);
`--context N` (diff). `THINK_BETTER_AI=claude` sets the default `--ai`. After `diff`: take the new
version with `mv <file>.new <file>`, keep yours with `rm <file>.new`. Commands other than `init`
work from any folder inside the project.

---

## Slash Commands

| Skill | Commands |
|-------|----------|
| make-decision | `/decide.quick` · `/decide` · `/decide.deep` · `/decide.exec` · `/decide.resume` |
| problem-solving-pro | `/solve.quick` · `/solve` · `/solve.deep` · `/solve.exec` · `/solve.resume` |
| code-solving | `/code` · `/code.deep` · `/code.debug` · `/code.feature` · `/code.refactor` · `/code.perf` · `/code.review` · `/code.test` · `/code.explain` · `/code.resume` |

Add "save step-by-step" (or "lưu", "lưu lại", "lưu từng bước") to save a workspace; continue it with the
`.resume` command (no text: the latest workspace). `/code.review` with no text reviews your current changes.
You can also just describe the problem: every supported tool loads the skills by their
description (GitHub Copilot in agent mode).

---

## Running the Scripts Yourself

From the project root. Paths for Claude Code (others: `.opencode/skills/`, `.agents/skills/`,
`.github/skills/` for Copilot):

```bash
DECIDE=.claude/skills/make-decision/scripts/search.py
SOLVE=.claude/skills/problem-solving-pro/scripts/search.py
CODE=.claude/skills/code-solving/scripts/search.py
```

All three take `-p`/`--project-name`/`--project` and `-n`/`--max-results`/`--results`. Bad input
(an empty request, scores outside 1-5) exits 2; a missing saved workspace exits 1. Reusing a
workspace name for another request needs `--force` or another `-p`.

---

## Decision Workflows (One-Pagers)

### Binary Choice (2 Options)
```bash
python3 $DECIDE "your decision" --plan -p "Project"
python3 $DECIDE --matrix "Option A vs Option B" -c "criterion1:3,criterion2:2,criterion3:1"
python3 $DECIDE "status quo confirmation" --domain biases
python3 $DECIDE --journal "Decision title" -p "Project"
```
**Framework:** Pros-Cons-Fixes Analysis
**Key Q:** Which cons are fixable vs permanent?

---

### Multi-Option Selection (3+ Options)
```bash
# 1. Get the decision plan
python3 $DECIDE "choosing between A, B, C for [purpose]" --plan -p "Project"

# 2. Get a criteria template
python3 $DECIDE "[topic]" --domain criteria

# 3. Get analysis techniques
python3 $DECIDE "comparison scoring sensitivity" --domain analysis

# 4. Matrix (at most 5 criteria), then score it: weighted totals, winner, the weight change that flips it
python3 $DECIDE --matrix "A vs B vs C" -c "c1:3,c2:2,c3:1"
python3 $DECIDE --matrix "A vs B vs C" -c "c1:3,c2:2,c3:1" --scores "A:4,3,5;B:5,4,3;C:3,3,4"

# 5. Check biases
python3 $DECIDE "anchoring first impression" --domain biases

# 6. Group facilitation (if team)
python3 $DECIDE "anonymous input dot voting" --domain facilitation

# 7. Document (confidence and a review date), and list the decisions due for review later
python3 $DECIDE --journal "Chose [WINNER] because..." -p "Project" --confidence 70 --review-in 30d
python3 $DECIDE --journal --review --due
```
**Framework:** Weighted Criteria Matrix + Sensitivity Analysis
**Key:** Define criteria BEFORE evaluating options; at most 5 criteria

---

### Resource Allocation
```bash
python3 $DECIDE "allocate resources across priorities" --plan -p "Project"
python3 $DECIDE "expected value" --domain frameworks
python3 $DECIDE "opportunity cost" --domain analysis

# Remember: allocate 50-70% in round 1, measure velocity, reallocate the rest
```
**Framework:** Expected Value Calculation
**Key:** Don't allocate 100% upfront; learn before committing

---

### Coding (bugs, features, refactors, performance, reviews, tests, explanations)
```bash
/code.debug [error message and stack trace, repro steps, what changed]
/code.feature [what users can do when it is done]
/code.refactor [module and the change it should make easier]
/code.perf [metric, current value, target]
/code.review [PR or files]
/code.test [module or behavior to protect]
/code.explain [what you want to understand]
/code.deep [high-stakes change: more techniques, full review checklist]
/code.resume [which saved workspace, or nothing for the latest]
/code [anything else: flaky tests, incidents, migrations, security fixes, small changes]

# Every step needs evidence before the next:
# 1 Define: failing test or repro    2 Decompose: change map
# 3-4 Plan: tasks with tests          5 Execute: small green steps
# 6 Verify: Step 1 check + project checks pass
# 7 Communicate: PR description / postmortem

python3 $CODE --detect     # the project's test/lint/build commands
```
**Key:** No fix without a test that failed first; no "done" without the checks' output.
Bugs in code go here, not to `/solve`.

---

### Problem-Solving (business, product, process)
```bash
/solve [Describe the problem, the context, what you've tried]

# With depth control:
/solve.quick Signups dropped after the pricing change
/solve.deep Revenue dropped 20% despite market growth
/solve.exec Revenue dropped 20% despite market growth   (adds an executive summary)

# Continue a saved step-by-step workspace at the first open step:
/solve.resume [which saved workspace, or nothing for the latest]

# Vietnamese works too, with or without accents: /solve.quick doanh thu giảm 20% quý này

# The 7 steps:
# 1 Define  2 Disaggregate (issue/profitability tree)  3 Prioritize (80/20)
# 4 Workplan  5 Analyze (test hypotheses)  6 Synthesize ("so what?")
# 7 Communicate (answer first: Pyramid Principle)
```
**Key:** Rank hypotheses by impact × ease of testing; the answer leads the communication

---

## Domain Searches

| Skill | `--domain` | What's in it |
|-------|-----------|--------------|
| make-decision | `frameworks` | 10 decision frameworks |
| | `types` | 8 decision types |
| | `biases` | 12 cognitive biases with remedies |
| | `analysis` | 10 analysis techniques |
| | `criteria` | 15 criteria templates, 5 criteria each |
| | `facilitation` | 8 facilitation techniques |
| problem-solving-pro | `decomposition` | 18 decomposition frameworks |
| | `heuristics` | 13 mental models |
| | `communication` | 10 communication patterns |
| | `steps`, `problem-types`, `prioritization`, `analysis`, `biases`, `team` | the rest of the method |
| code-solving | `errors` | 44 common error messages |
| | `task-types` | 12 task types |
| | `steps`, `debugging`, `changes`, `testing`, `principles`, `biases`, `review`, `artifacts` | techniques, checklists and pitfalls |

```bash
python3 $DECIDE "keywords" --domain criteria
python3 $SOLVE "keywords" --domain decomposition
python3 $CODE "keywords" --domain errors
```

---

## Decision Journey

### Before deciding
- ✅ Define the problem precisely
- ✅ List all options (including "do nothing" when real)
- ✅ Define criteria BEFORE evaluating options (at most 5)
- ✅ Identify stakeholders
- ✅ Check relevant biases and apply remedies

### During the decision
- ✅ Get independent scores first
- ✅ Read the sensitivity result (multi-option)
- ✅ Use a structured group process (if team)
- ✅ Check references (vendors/hires)
- ✅ Small experiments for technical decisions

### After the decision
- ✅ Journal entry with rationale, confidence and review date
- ✅ Document the implementation plan and known risks

### Review
- ✅ `--journal --review --due`, then `--update` with the actual outcome
- ✅ Extract lessons learned

---

## High-Risk Biases (Always Watch)

| Bias | Watch for | Counter |
|------|-----------|---------|
| **Confirmation Bias** | Noticing what supports the first impression | Seek disconfirming evidence actively |
| **Anchoring Effect** | First number/option influences the rest | Independent estimates before comparing |
| **Sunk Cost Fallacy** | Past investment justifying more | Evaluate as if starting fresh |
| **Overconfidence** | Too certain about uncertain outcomes | Pre-mortem, track calibration |
| **Status Quo Bias** | Preference for the current state | Reframe as the cost of not acting |

### By area

| Area | Biases |
|------|--------|
| Hiring | Confirmation Bias, Anchoring Effect, Availability Heuristic |
| Tech stack | Availability Heuristic, Confirmation Bias, Survivorship Bias |
| Build vs buy | Sunk Cost Fallacy, Status Quo Bias, Not Invented Here |
| Allocation | Sunk Cost Fallacy, Overconfidence, Loss Aversion, Planning Fallacy |

---

## Pro Tips

### Decision-making
1. **Pros-Cons-Fixes** for binary choices: ask "is this fixable?"
2. **Sensitivity analysis** for multi-option: which weight change flips the winner?
3. **Define criteria first**: prevents anchoring and post-hoc rationalization
4. **Anonymous input first**: surfaces minority views before group pressure
5. **Reference checks**: talk to customers and previous managers, not just the sales pitch

### Problem-solving
1. **Decompose MECE**: branches that don't overlap and cover the whole problem
2. **Rank hypotheses**: test the likely, cheap ones first
3. **Measure before fixing**: understand the problem before proposing a solution
4. **5 Whys**: work back from the symptom to the root cause
5. **Answer first**: lead with the recommendation, then the evidence

---

## Quick Prompts for Your AI Assistant

```
## For decision-making
/decide Should we [option A] or [option B]?
/decide.deep Choosing between [A], [B] and [C] for [purpose].
/decide.exec Strategic analysis of [major decision] for the leadership meeting
/decide.resume [which saved decision, or nothing for the latest]
/decide Nên chọn [A] hay [B]?   (Vietnamese works too)

## For coding
/code.debug [Error and stack trace]. Repro: [steps]. Started after [change].
/code.feature [Feature] so that [user outcome]. Out of scope: [x].
/code.review [PR link or files]
/code.test [Module]: protect [behaviors]. Known bugs: [x].
/code.explain How does [feature] work, from [entry point] to [result]?

## For problem-solving
/solve [Describe the symptom]. Context: [market, product, team].
Data so far: [numbers]. I've tried [what you've tried].

/solve.deep Why did [metric] change after [event]?
```

---

## Resources

- **Main guide:** [USER-GUIDE.md](USER-GUIDE.md): full workflows, [Troubleshooting](USER-GUIDE.md#troubleshooting) and [FAQ](USER-GUIDE.md#faq)
- **Case studies:** [examples/](examples/README.md)
- **Coding example:** [examples/06-code-debug-typeerror.md](examples/06-code-debug-typeerror.md): `/code.debug` from stack trace to PR
- **Skill reference:** the `SKILL.md` in each installed skill folder

---

**Print this card and keep it at your desk!** 📇
