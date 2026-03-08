# Decision-Making Use Cases & Lessons Learned

Real-world examples demonstrating how to use the `make-decision` CLI tool and bundled skills for structured decision-making and problem-solving.

## 📚 Available Use Cases

| # | Use Case | Skill | Decision Type | Key Learning |
|---|----------|-------|---------------|--------------|
| [01](01-product-strategy.md) | **CLI Product Strategy** | make-decision | Binary Choice | Keep it minimal - fixable cons beat permanent ones |
| [02](02-cloud-migration.md) | **Cloud Provider Selection** | make-decision | Multi-Option | Use weighted criteria + sensitivity analysis |
| [03](03-hiring-decision.md) | **Senior Engineer Hiring** | make-decision | Multi-Option | Define criteria before seeing candidates to avoid bias |
| [04](04-budget-allocation.md) | **Resource Allocation** | make-decision | Resource Allocation | Iterative allocation reduces planning risk |
| [05](05-debugging-race-condition.md) | **API Race Condition** | problem-solving-pro | Debugging | Structured hypothesis testing finds root cause faster |
| [06](06-template.md) | **[Template for new use case]** | - | - | - |
| [07](07-template.md) | **[Template for new use case]** | - | - | - |
| [08](08-template.md) | **[Template for new use case]** | - | - | - |
| [09](09-template.md) | **[Template for new use case]** | - | - | - |
| [10](10-template.md) | **[Template for new use case]** | - | - | - |

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

### Problem Solving (debugging, root cause analysis)
- Use: **Hypothesis-Driven Investigation**
- Examples: [05 - Race Condition](05-debugging-race-condition.md)
- Key: Rank hypotheses by likelihood, test highest-probability first

## 🧠 Common Cognitive Biases to Watch

| Bias | What It Is | Remedy |
|------|-----------|---------|
| **Confirmation Bias** | You notice evidence supporting your first impression | Actively seek disconfirming evidence |
| **Anchoring** | First number you see influences all estimates | Generate independent estimates before comparing |
| **Sunk Cost Fallacy** | Past investment makes you continue failing projects | Evaluate as if starting fresh today |
| **Status Quo Bias** | You prefer current state even when change is better | Reframe as opportunity cost |
| **Overconfidence** | You're too certain about uncertain outcomes | Use pre-mortem, track calibration over time |

## 🔄 Suggested Workflow

```bash
# 1. Install the skill
make-decision init --ai copilot --skill make-decision

# 2. Generate decision plan (always start here)
cd .github/prompts/make-decision
python scripts/search.py "your decision question" --plan -p "Project Name"

# 3. Deep-dive into specific domains as needed
python scripts/search.py "relevant keywords" --domain frameworks

# 4. Create comparison matrix for options
python scripts/search.py --matrix "Option A vs Option B vs Option C" -c "criterion1,criterion2"

# 5. Document the decision
python scripts/search.py --journal "Decision title" -p "Project Name"

# 6. Update with actual outcome later
python scripts/search.py --journal --update "decision-slug" --outcome "What actually happened"
```

## 🤝 Contributing Your Own Use Case

Have a great example? Follow the template in [06-template.md](06-template.md) and submit a PR!

**What makes a good use case:**
- ✅ Real scenario (anonymized if needed)
- ✅ Shows actual commands and outputs
- ✅ Highlights key learning or insight
- ✅ Identifies biases that were mitigated
- ✅ Documents the outcome/retrospective

---

**Back to:** [Main README](../README.md)
