# Use Case 10: [Problem-Solving Template]

**Problem:** [One-sentence description of the problem]

**Type:** Problem-Solving (Root Cause Analysis)  
**Skill Used:** problem-solving-pro  
**Duration:** [Time from discovery to resolution]  
**Outcome:** [Root cause + solution implemented]

---

## 📋 Context

**Situation:**  
[Problem-solving scenarios often involve:
- Symptoms without obvious cause
- Multiple potential root causes
- Urgency (production issue) or complexity (architectural problem)
- Need for structured investigation]

**Symptoms Observed:**
- [Symptom 1: what users/systems are experiencing]
- [Symptom 2]
- [Symptom 3]

**Impact:**
- [Business impact: revenue, customers, SLA]
- [Technical impact: performance, reliability]
- [Team impact: on-call burden, morale]

**Environment:**
- [Tech stack: languages, frameworks, infrastructure]
- [Scale: requests/sec, data volume, users]
- [Recent changes: deployments, config changes]

**Stakes:** [Low | Medium | High] — [Why this must be solved]

---

## 🔬 Problem-Solving Process

### Step 1: Use problem-solving skill

```bash
make-decision init --ai claude --skill problem-solving-pro
```

In your AI assistant:
```
@workspace /solve [Describe the problem symptoms, context, and what you've tried]
```

### Step 2: Problem Decomposition

[Break the system into layers/components]

```
[Component Layer 1: e.g., Load Balancer]
         ↓
[Component Layer 2: e.g., Application Servers]
         ↓
[Component Layer 3: e.g., Database]
         ↓
[Component Layer 4: e.g., Network/Infrastructure]
```

[Which layer is the problem in?]

### Step 3: Hypothesis Generation

[Rank potential root causes by likelihood]

| # | Hypothesis | Likelihood | How to Test |
|---|------------|------------|-------------|
| 1 | [Most likely cause] | [%] | [Specific test] |
| 2 | [Second most likely] | [%] | [Specific test] |
| 3 | [Third most likely] | [%] | [Specific test] |
| 4 | [Less likely] | [%] | [Specific test] |

**Prioritization:** Test highest likelihood × easiest to test first.

### Step 4: Evidence Collection

**Test Hypothesis 1:**

[What you did to test]
```bash
[Commands run, logs checked, metrics analyzed]
```

**Result:** [Confirmed | Rejected | Inconclusive]

**Test Hypothesis 2:**

[Continue testing until root cause found]

### Step 5: Root Cause Identified

**Root Cause:** [Precise description of the actual cause]

**Why this happened:**
[Use 5 Whys technique]
1. **Why [symptom]?** → [Because...]
2. **Why [that]?** → [Because...]
3. **Why [that]?** → [Because...]
4. **Why [that]?** → [Because...]
5. **Why [that]?** → [ROOT CAUSE]

### Step 6: Solution Design

**Option 1: [Quick fix]**
- **Pros:** [Fast, low risk]
- **Cons:** [Doesn't address root cause, may recur]
- **Timeline:** [Hours]

**Option 2: [Proper fix]**
- **Pros:** [Addresses root cause, prevents recurrence]
- **Cons:** [Takes longer, requires testing]
- **Timeline:** [Days]

**Option 3: [Architectural fix]**
- **Pros:** [Prevents entire class of issues]
- **Cons:** [Significant work, potential new risks]
- **Timeline:** [Weeks]

**Decision:** [Which approach and why]

---

## ✅ Solution Implemented

### Code/Config Changes

```diff
[Show the actual changes made]
+ [Added lines]
- [Removed lines]
```

### Testing

**Test 1: Reproduce original issue**
```bash
[Command to reproduce]
# Before fix: [Problem occurs]
# After fix: [Problem resolved]
```

**Test 2: Load test / Edge cases**
```bash
[Commands run]
# Result: [Outcomes]
```

### Monitoring Added

[What metrics/alerts were added to catch this in the future]

```
[Alert rule or monitoring dashboard]
```

---

## 🎓 Lessons Learned

### Key Insight
[The main learning from this investigation]

### Problem-Solving Pattern

**What worked:**
- ✅ [e.g., Structured hypothesis testing vs. random debugging]
- ✅ [e.g., Reproduced in staging before fixing prod]

**What didn't work:**
- ❌ [e.g., Assumed it was X without testing]
- ❌ [e.g., Made changes without measuring impact]

### Root Cause Classification

[What category does this fall into?]
- [ ] **Code bug** — Logic error in application code
- [ ] **Configuration error** — Wrong setting or missing config
- [ ] **Resource exhaustion** — CPU, memory, disk, network limits
- [ ] **Dependency failure** — External service or library issue
- [ ] **Race condition** — Timing-dependent bug
- [ ] **Data corruption** — Invalid or inconsistent data
- [ ] **Scaling issue** — Worked at low load, fails at high load
- [ ] **Architectural limitation** — Design doesn't support the use case

### Prevention Measures

[How to prevent this from happening again]

| Prevention | Implementation |
|------------|----------------|
| [e.g., Add test coverage] | [Unit test for edge case X] |
| [e.g., Monitoring] | [Alert when metric Y exceeds threshold] |
| [e.g., Code review checklist] | [Check for pattern Z in PRs] |
| [e.g., Documentation] | [Runbook for this scenario] |

### Post-Mortem Documentation

```markdown
## Post-Mortem: [Problem Title] ([Date])

**Impact:** [Who/what was affected and how severely]
**Duration:** [Time from discovery to resolution]
**Root Cause:** [One-sentence summary]

**Timeline:**
- [T+0]: Problem first observed
- [T+X]: Investigation started
- [T+Y]: Root cause identified
- [T+Z]: Fix deployed
- [T+Z+verification]: Confirmed resolved

**Fix:** [What was changed]

**Prevention:**
- [Action item 1]
- [Action item 2]
```

### Applicability
Use this structured approach for:
- ✅ Production incidents
- ✅ Performance regressions
- ✅ Flaky tests
- ✅ Customer-reported bugs
- ✅ Data quality issues

---

**Incident Date:** [Date]  
**Resolution Time:** [Duration]  
**Investigator:** [Who solved it]  
**Validation:** [How you confirmed it's fixed]

**Outcome:**
- ✅ [Immediate result: problem resolved]
- ✅ [Monitoring added to detect early]
- 📖 [Runbook created for future incidents]
