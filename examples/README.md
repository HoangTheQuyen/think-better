# Decision-Making Use Cases & Lessons Learned

Worked examples of the bundled skills: decisions (`/decide`), problems (`/solve`) and code changes (`/code`).

## 📚 Available Use Cases

| # | Use Case | Skill | Decision Type | Key Learning |
|---|----------|-------|---------------|--------------|
| [01](01-product-strategy.md) | **CLI Product Strategy** | make-decision | Binary Choice | Keep it minimal - fixable cons beat permanent ones |
| [02](02-cloud-migration.md) | **Cloud Provider Selection** | make-decision | Multi-Option | Use weighted criteria + sensitivity analysis |
| [03](03-hiring-decision.md) | **Senior Engineer Hiring** | make-decision | Multi-Option | Define criteria before seeing candidates to avoid bias |
| [04](04-budget-allocation.md) | **Resource Allocation** | make-decision | Resource Allocation | Iterative allocation reduces planning risk |
| [05](05-debugging-race-condition.md) | **API Race Condition** | code-solving | Debug | A repro first, then rank and test hypotheses one at a time |
| [06](06-code-debug-typeerror.md) | **TypeError After a Deploy** | code-solving | Debug | A failing test first; known-error causes are hypotheses to rule out |

## 📖 How to Use These Examples

1. **Read the scenario** — Understand the decision context and constraints
2. **Follow the commands** — Copy/paste the exact commands used
3. **Study the output** — See what the skill recommends and why
4. **Extract the lesson** — Apply the pattern to your own decisions

## 🎯 Decision Patterns by Type

### Binary Choices (2 options)
- Use: **Pros-Cons-Fixes Analysis**
- Examples: [01 - Product Strategy](01-product-strategy.md)
- Key: Ask "can this con be fixed?" to reveal hidden flexibility

### Multi-Option Selection (3+ options)
- Use: **Weighted Criteria Matrix**
- Examples: [02 - Cloud Migration](02-cloud-migration.md), [03 - Hiring](03-hiring-decision.md)
- Key: Define criteria *before* evaluating options to avoid anchoring

### Resource Allocation (limited budget/time)
- Use: **Iterative Allocation**
- Examples: [04 - Budget Allocation](04-budget-allocation.md)
- Key: Allocate in rounds, reassess after each round

### Business and Product Problems (root cause analysis)
- Use: **`/solve` and its 7 steps** (Define → Disaggregate → Prioritize → Workplan → Analyze → Synthesize → Communicate)
- Examples: the walk-through in the [User Guide](../USER-GUIDE.md#a-business-problem-signups-dropped)
- Key: Decompose MECE, rank hypotheses by impact, lead with the answer

### Code Changes (bugs, features, refactors, reviews)
- Use: **`/code` and its 7 gated steps**
- Examples: [05 - Race Condition](05-debugging-race-condition.md), [06 - TypeError After a Deploy](06-code-debug-typeerror.md)
- Key: No fix without a test that failed first; no "done" without the checks' output

## 🧠 Common Cognitive Biases to Watch

| Bias | What It Is | Remedy |
|------|-----------|---------|
| **Confirmation Bias** | You notice evidence supporting your first impression | Actively seek disconfirming evidence |
| **Anchoring Effect** | First number you see influences all estimates |Generate independent estimates before comparing |
| **Sunk Cost Fallacy** | Past investment makes you continue failing projects | Evaluate as if starting fresh today |
| **Status Quo Bias** | You prefer current state even when change is better | Reframe as opportunity cost |
| **Overconfidence** | You're too certain about uncertain outcomes | Use pre-mortem, track calibration over time |

## 🔄 Suggested Workflow

In a chat, a slash command does all of this for you (`/decide`, `/solve`, `/code.debug`, ...).
To run the scripts yourself, work from the project root:

```bash
# 1. Install the skill
think-better init --ai claude --skill make-decision
DECIDE=.claude/skills/make-decision/scripts/search.py   # Copilot: .github/prompts/make-decision/...

# 2. Generate decision plan (always start here)
python3 $DECIDE "your decision question" --plan -p "Project Name"

# 3. Deep-dive into specific domains as needed
python3 $DECIDE "relevant keywords" --domain frameworks

# 4. Create comparison matrix for options (at most 5 criteria)
python3 $DECIDE --matrix "Option A vs Option B vs Option C" -c "criterion1:3,criterion2:2"

# 5. Document the decision
python3 $DECIDE --journal "Decision title" -p "Project Name"

# 6. Update with actual outcome later
python3 $DECIDE --journal --update "decision-slug" --outcome "What actually happened"
```

## 🤝 Contributing Your Own Use Case

Have a great example? Copy the shape of an existing one and submit a PR: a short context
(situation, constraints, stakes), the exact commands or slash commands used, what the skill
answered, the outcome, and two or three lessons. Keep it to one or two screens.

**What makes a good use case:**
- ✅ Real scenario (anonymized if needed)
- ✅ Shows actual commands and outputs
- ✅ Highlights key learning or insight
- ✅ Identifies biases that were mitigated
- ✅ Documents the outcome/retrospective

---

**Back to:** [Main README](../README.md)
