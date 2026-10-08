# Quick Reference Card

## Installation & Setup

```bash
# Install binary
curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh
# Or Windows: irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

# Install skills and slash commands
think-better init --ai claude       # or: copilot, antigravity, opencode
think-better init --ai claude --global   # once for all projects (not Copilot)

# List installed skills
think-better list

# Verify setup
think-better check
```

---

## Decision Workflows (One-Pagers)

### Binary Choice (2 Options)
```bash
python scripts/search.py "your decision" --plan -p "Project"
python scripts/search.py --matrix "Option A vs Option B" -c "criterion1,criterion2"
python scripts/search.py "relevant keyword" --domain biases
python scripts/search.py --journal "Decision title" -p "Project"
```
**Framework:** Pros-Cons-Fixes Analysis  
**Key Q:** Which cons are fixable vs permanent?

---

### Multi-Option Selection (3+ Options)
```bash
# 1. Get decision plan
python scripts/search.py "choosing between A, B, C for [purpose]" --plan -p "Project"

# 2. Get criteria template
python scripts/search.py "[topic]" --domain criteria

# 3. Get analysis techniques
python scripts/search.py "comparison scoring sensitivity" --domain analysis

# 4. Create matrix, then score it: weighted totals, winner, and the weight change that flips it
python scripts/search.py --matrix "A vs B vs C" -c "c1:3,c2:2,c3:1"
python scripts/search.py --matrix "A vs B vs C" -c "c1:3,c2:2,c3:1" --scores "A:4,3,5;B:5,4,3;C:3,3,4"

# 5. Check biases
python scripts/search.py "anchoring status quo first impression" --domain biases

# 6. Group facilitation (if team)
python scripts/search.py "anonymous voting structured" --domain facilitation

# 7. Document (confidence and a review date), and list the decisions due for review later
python scripts/search.py --journal "Chose [WINNER] because..." -p "Project" --confidence 70 --review-in 30d
python scripts/search.py --journal --review --due
```
**Framework:** Weighted Criteria Matrix + Sensitivity Analysis  
**Key:** Define criteria BEFORE evaluating options

---

### Resource Allocation
```bash
python scripts/search.py "allocate resources across priorities" --plan -p "Project"
python scripts/search.py "iterative allocation" --domain frameworks
python scripts/search.py "opportunity cost" --domain analysis

# Remember: Allocate 50-70% in Round 1, measure velocity, reallocate
```
**Framework:** Iterative Allocation  
**Key:** Don't allocate 100% upfront; learn before committing

---

### Coding (bugs, features, refactors, performance, reviews, tests, explanations)
```bash
/code.debug [error message, repro steps, what changed]
/code.feature [what users can do when it is done]
/code.refactor [module and the change it should make easier]
/code.perf [metric, current value, target]
/code.review [PR or files]
/code.test [module or behavior to protect]
/code.explain [what you want to understand]
/code.resume [which saved workspace, or nothing for the latest]
/code [anything else: flaky tests, incidents, migrations, security fixes, small changes]

# Every step needs evidence before the next:
# 1 Define: failing test or repro    2 Decompose: change map
# 3-4 Plan: tasks with tests          5 Execute: small green steps
# 6 Verify: Step 1 check + project checks pass
# 7 Communicate: PR description / postmortem
```
**Key:** No fix without a test that failed first; no "done" without the checks' output

---

### Problem-Solving (business, product, process)
```bash
# In your AI assistant with problem-solving-pro skill:
/solve [Describe problem, environment, what you've tried]

# With depth control:
/solve.quick Signups dropped after the pricing change
/solve.deep Revenue declining despite growth
/solve.exec Board-level crisis analysis

# The skill guides you through:
# 1. Problem decomposition (break into layers)
# 2. Hypothesis ranking (by likelihood)
# 3. Evidence collection (specific tests)
# 4. Root cause (5 Whys)
# 5. Solution options (quick vs proper vs architectural)
# 6. Prevention (monitoring, alerts)
```
**Key:** Test hypotheses by likelihood × ease of testing

---

## Domain-Specific Searches

```bash
# Get decision-making frameworks (10 available)
python scripts/search.py "keywords" --domain frameworks

# Get decision type classifications (8 types)
python scripts/search.py "keywords" --domain types

# Get cognitive biases (12 with remedies)
python scripts/search.py "keywords" --domain biases

# Get analysis techniques (10 methods)
python scripts/search.py "keywords" --domain analysis

# Get evaluation criteria (8 templates)
python scripts/search.py "keywords" --domain criteria

# Get group facilitation techniques (8 methods)
python scripts/search.py "keywords" --domain facilitation
```

---

## Decision Journey

### Before Deciding
- ✅ Define problem precisely
- ✅ List all options/alternatives
- ✅ Define criteria BEFORE evaluating options
- ✅ Identify stakeholders
- ✅ Check relevant biases and apply remedies

### During Decision
- ✅ Get independent scores/estimates first
- ✅ Run sensitivity analysis (multi-option)
- ✅ Use structured group process (if team)
- ✅ Check references (vendors/hires)
- ✅ POCs for technical decisions

### After Decision
- ✅ Create journal entry with rationale
- ✅ Set review date (3-6 months or 12 months)
- ✅ Document implementation plan
- ✅ Identify known risks

### Retrospective
- ✅ Update journal with actual outcomes
- ✅ Extract lessons learned
- ✅ Improve future calibration

---

## High-Risk Biases (Always Watch)

| Bias | Watch For | Counter |
|------|-----------|---------|
| **Confirmation** | Noticing what supports first impression | Seek disconfirming evidence actively |
| **Anchoring** | First number/option influences rest | Independent estimates before comparing |
| **Sunk Cost** | Past investment justifying future | Evaluate as if starting fresh |
| **Overconfidence** | Too certain about uncertain outcomes | Pre-mortem, track calibration |
| **Status Quo** | Preference for current state | Reframe as opportunity cost |

### Domain-Specific
- **Hiring:** Affinity, Halo Effect, Resume-Driven
- **Tech:** Resume-Driven, Not Invented Here, Status Quo
- **Allocation:** Planning Fallacy, Overconfidence

---

## Pro Tips

### Decision-Making
1. **Pros-Cons-Fixes** for binary choices — Ask "is this fixable?"
2. **Sensitivity Analysis** for multi-option — What if weights change?
3. **Define Criteria First** — Prevents anchoring and post-hoc rationalization
4. **Use Anonymous Voting** — Surfaces minority views before group pressure
5. **Reference Checks** — Talk to customers/previous managers, not just sales pitch

### Problem-Solving
1. **Break Into Layers** — Decompose by system architecture
2. **Rank by Likelihood** — Test highest probability hypotheses first
3. **Measure Before Fixing** — Understand the problem before proposing solution
4. **5 Whys** — Work backward from symptom to root cause
5. **Prevention Matters** — Add monitoring to catch this in future

---

## Common Decision Types & Frameworks

| Situation | Framework | Time | Who |
|-----------|-----------|------|-----|
| 2 options | Pros-Cons-Fixes | 1-2 hrs | Individual/Team |
| 3+ options | Weighted Matrix | 2-4 hrs | Individual/Team |
| Uncertain | Scenario Planning | 2-4 hrs | Team |
| Sequential | Decision Tree | 1-2 hrs | Team |
| Resources | Iterative Allocation | 2-4 weeks | Team |
| Debugging | Hypothesis Testing | 1-4 hrs | Individual |
| Team aligned | Nominal Group | 2-3 hrs | Group |

---

## Quick Prompts for AI Assistant

```
## For Decision-Making

/decide Should we [option A] or [option B]?
/decide.deep Choosing between [A], [B], and [C] for [purpose].
/decide.exec Strategic analysis of [major decision] for board discussion
/decide.resume [which saved decision, or nothing for the latest]
/decide Nên chọn [A] hay [B]?   (Vietnamese works too)

## For Coding

/code.debug [Error]. Repro: [steps]. Started after [change].
/code.feature [Feature] so that [user outcome]. Out of scope: [x].
/code.review [PR link or files]
/code.test [Module]: protect [behaviors]. Known bugs: [x].
/code.explain How does [feature] work, from [entry point] to [result]?

## For Problem-Solving

/solve [Describe symptom]. Happens in [environment].
Stack: [tech stack]. I've tried [what you've tried so far].

/solve.deep Why does [system] sometimes [fail condition]?
Recent changes: [recent deployments/config changes]
```

---

## Resources

- **Main Guide:** [USER-GUIDE.md](USER-GUIDE.md) — Full workflows with examples
- **Case Studies:** [examples/](examples/) — Real decisions with outcomes
- **Skill Reference:** `.agents/skills/make-decision/SKILL.md` — Full documentation
- **Templates:** [examples/06-template.md](examples/06-template.md) onwards — Adapt for your use cases

---

**Print this card and keep it at your desk!** 📇
