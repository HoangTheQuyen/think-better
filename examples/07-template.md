# Use Case 07: [Strategic Decision Template]

**Decision:** [Long-term strategic choice, e.g., market expansion, product direction, organizational structure]

**Type:** Strategic  
**Skill Used:** make-decision  
**Duration:** [Typically weeks to months for strategic decisions]  
**Outcome:** [Decision + early indicators]

---

## 📋 Context

**Situation:**  
[Strategic decisions often involve:
- Long-term impact (3-5 years)
- High uncertainty
- Multiple stakeholders
- Difficult to reverse]

**Options Under Consideration:**
1. **[Option 1]** — [Brief description]
2. **[Option 2]** — [Brief description]
3. **[Option 3]** — [Brief description]

**Constraints:**
- [Strategic constraints: market timing, competitive pressure, board expectations]
- [Resource constraints]
- [Organizational readiness]

**Stakes:** Very High — [Why this is a pivotal decision]

---

## 🔬 Process

### Step 1: Generate decision plan for strategic choice

```bash
python scripts/search.py "[your strategic decision]" --plan -p "[Project Name]" -f markdown
```

**Recommended Framework:** [Likely Scenario Planning or Hypothesis-Driven]

### Step 2: Scenario analysis

[Strategic decisions benefit from exploring multiple future scenarios]

```bash
python scripts/search.py "scenario planning uncertainty" --domain frameworks
```

**Scenarios to Model:**
- **Best Case:** [What happens if everything goes right]
- **Base Case:** [Most likely outcome]
- **Worst Case:** [What if key assumptions are wrong]

### Step 3: Stakeholder analysis

[Who has influence? Who will be impacted?]

| Stakeholder | Influence | Support | Key Concern |
|-------------|-----------|---------|-------------|
| [e.g., CEO] | High | Neutral | [What they care about] |
| [e.g., Board] | High | Supportive | [What they care about] |
| [e.g., Team] | Low | Resistant | [What they care about] |

### Step 4: [Continue your process...]

---

## 📊 Decision Matrix

| Criterion | Weight | Option 1 | Option 2 | Option 3 |
|-----------|--------|----------|----------|----------|
| [Criterion 1] | [%] | [Score] | [Score] | [Score] |
| [Criterion 2] | [%] | [Score] | [Score] | [Score] |
| **TOTAL** | 100 | **[X.X]** | **[X.X]** | **[X.X]** |

---

## ✅ Decision

**Choice:** [Selected option]

**Rationale:**
1. [Strategic fit]
2. [Risk/reward balance]
3. [Organizational readiness]
4. [Market timing]

**Implementation Phases:**
- **Phase 1 (Months 1-3):** [Initial steps]
- **Phase 2 (Months 4-6):** [Scaling]
- **Phase 3 (Months 7-12):** [Full rollout]

**Decision Reversibility:** [One-way door vs. two-way door]

---

## 🎓 Lessons Learned

### Key Insight
[Strategic decisions require different frameworks than tactical ones]

### Bias Watch
**For Strategic Decisions, especially watch:**
- **Overconfidence** — Long-term predictions are highly uncertain
- **Planning Fallacy** — Strategic initiatives take 2-3x longer than estimated
- **Groupthink** — Senior teams often converge too quickly

### Documentation

```bash
python scripts/search.py --journal "[Decision title]" -p "[Project Name]"
```

**Annual Review:** Update journal entry with actual outcomes

---

**Decision Date:** [Date]  
**Review Date:** [1 year out]  
**Decision Maker:** [C-level or Board]  
**Stakeholders:** [Entire organization]

**12-Month Retrospective:**
- [Outcome vs. expectation]
- [What was learned]
- [What would you do differently]
