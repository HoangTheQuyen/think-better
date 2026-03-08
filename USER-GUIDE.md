# User Guide: How to Use Think Better

A step-by-step guide to installing and using the bundled skills for structured thinking, decision-making, and problem-solving with your AI assistant.

---

## 🚀 Quick Start (5 minutes)

### 1. Download and Install

```bash
# Download binary for your platform from releases
# Or build from source:
git clone https://github.com/htrbao/think-better.git
cd think-better
go build -o bin/think-better ./cmd/make-decision
```

### 2. Install a Skill

```bash
# For Claude (VS Code)
make-decision init --ai claude --skill make-decision

# For GitHub Copilot
make-decision init --ai copilot --skill problem-solving-pro

# Install all skills
make-decision init --ai claude --force
```

### 3. Open Your AI Assistant

- **Claude:** Open Cursor or VS Code with Continue extension
- **Copilot:** Open VS Code and switch to Copilot Chat

### 4. Start Using

In your AI chat, type:
```
@workspace /make-decision Should we migrate to microservices?
```

---

## 📚 Bundled Skills

### Skill 1: make-decision

**What it does:** Guides you through structured decision-making with frameworks, bias detection, and facilitation techniques.

**Best for:**
- Strategic choices (keep it minimal vs scale up)
- Multi-option selection (choose between 3+ vendors/technologies)
- Resource allocation (budget distribution)
- Team decisions (need group consensus)

**How it works:**
```bash
# Inside the skill directory:
cd .github/prompts/make-decision

# Step 1: Generate decision plan (always start here!)
python scripts/search.py "your decision question here" --plan -p "Project Name"

# Step 2: Deep-dive into specific domains
python scripts/search.py "relevant keywords" --domain frameworks  # 10 frameworks
python scripts/search.py "relevant keywords" --domain biases     # 12 cognitive biases
python scripts/search.py "relevant keywords" --domain criteria   # Evaluation templates
python scripts/search.py "relevant keywords" --domain analysis   # 10 analysis techniques
python scripts/search.py "relevant keywords" --domain facilitation # Group decision tips

# Step 3: Create comparison matrix for options
python scripts/search.py --matrix "Option A vs Option B vs Option C" \
  -c "criterion1,criterion2,criterion3"

# Step 4: Document the decision
python scripts/search.py --journal "Decision title" -p "Project Name"

# Step 5: Update with actual outcome (later)
python scripts/search.py --journal --update "decision-slug" \
  --outcome "What actually happened and what you learned"
```

### Skill 2: problem-solving-pro

**What it does:** Guides you through structured problem-solving with hypothesis testing, root cause analysis, and systematic investigation.

**Best for:**
- Production incidents (bugs, performance issues)
- Debugging intermittent failures
- Root cause analysis
- Technical investigations
- Data quality issues

**How it works:**

In your AI assistant:
```
@workspace /solve [Describe your problem in detail]

Example:
@workspace /solve My API sometimes returns stale data after updates. 
Happens intermittently (~2% of requests), no clear pattern by time or user.
Stack: Node.js + Express, PostgreSQL with read replica, Redis cache.
```

The skill will guide you through:
1. **Problem Decomposition** — Break system into layers
2. **Hypothesis Generation** — Rank potential causes by likelihood
3. **Evidence Collection** — Specific tests to validate each hypothesis
4. **Root Cause Identification** — 5 Whys analysis
5. **Solution Design** — Compare quick fix vs proper fix vs architectural fix
6. **Prevention** — Monitoring to catch this in future

---

## 🎯 Decision-Making Workflows

### Scenario A: Binary Choice (2 Options)

**Example:** "Keep frontend simple or add more features?"

**Workflow:**

```bash
# Step 1: Get decision plan
python scripts/search.py "binary choice: keep simple vs add features" --plan -p "Product Roadmap"

# Output should recommend: Pros-Cons-Fixes Analysis

# Step 2: Search for relevant frameworks
python scripts/search.py "binary simplicity complexity" --domain frameworks

# Step 3: Create comparison matrix
python scripts/search.py --matrix "Keep simple vs Add features" \
  -c "development_time,maintainability,user_value,technical_debt,learning_curve"

# Step 4: Check for biases specific to this decision
python scripts/search.py "feature creep perfectionism" --domain biases

# Step 5: Document with decision journal
python scripts/search.py --journal "Frontend complexity: simple vs feature-rich" \
  -p "Product Roadmap"
```

**Key Question to Ask:**
> "Which cons are fixable vs permanent?"

Fixable cons (can be solved with documentation, features, or process changes) are less important than permanent cons (fundamental trade-offs).

---

### Scenario B: Multi-Option Selection (3+ Options)

**Example:** "Which cloud provider: AWS, Azure, or GCP?"

**Workflow:**

```bash
# Step 1: Get decision plan (critical for multi-option!)
python scripts/search.py "choosing between AWS, Azure, and GCP for enterprise migration" \
  --plan -p "Cloud Strategy"

# Output should recommend: Weighted Criteria Matrix + Sensitivity Analysis

# Step 2: Get evaluation criteria template
python scripts/search.py "technology vendor cloud" --domain criteria

# Step 3: Get analysis technique for multi-option decisions
python scripts/search.py "decision tree scoring comparison" --domain analysis

# Step 4: Create detailed comparison matrix
python scripts/search.py --matrix "AWS vs Azure vs GCP" \
  -c "total_cost,team_expertise,service_coverage,support_quality,compliance,migration_tools"

# Step 5: Run sensitivity analysis
# (Ask yourself: if weight of X criterion changes, does the winner change?)
# (Test different scenarios: what if team expertise was less important?)

# Step 6: Check for anchoring & status quo biases
python scripts/search.py "anchoring status quo first impression" --domain biases

# Step 7: Use group facilitation technique if team decisions
python scripts/search.py "structured debate dot voting anonymous" --domain facilitation

# Step 8: Document the final decision
python scripts/search.py --journal "Cloud migration: chose [WINNER] over alternatives" \
  -p "Cloud Strategy"
```

**Critical Steps:**
1. ✅ **Define criteria BEFORE evaluating options** (prevents anchoring)
2. ✅ **Get independent estimates/scores** (before group discussion)
3. ✅ **Run sensitivity analysis** (identify swing factors)
4. ✅ **Check references** (for vendors/hires)

---

### Scenario C: Resource Allocation

**Example:** "Allocate 10 engineers across 5 projects"

**Workflow:**

```bash
# Step 1: Decision plan for allocation
python scripts/search.py "allocate resources across competing priorities with constraints" \
  --plan -p "Q2 Planning"

# Output should recommend: Iterative Allocation (don't allocate all at once!)

# Step 2: Get resource allocation framework
python scripts/search.py "iterative constraint priority" --domain frameworks

# Step 3: Use opportunity cost analysis
python scripts/search.py "opportunity cost what do we lose" --domain analysis

# Step 4: Identify decision type (production risk vs growth opportunity)
python scripts/search.py "prioritization scoring risk reward" --domain types

# Step 5: If team decision, use facilitation
python scripts/search.py "dot voting priority ranking" --domain facilitation

# Step 6-Plan: Allocate conservative portion (50-70%)
# Allocate Round 1 with 30% of resources held back

# Step 6-Execute: Measure actual velocity and blockers for 2-3 weeks

# Step 7-Reassess: Based on evidence, reallocate remaining resources
# Repeat until all resources allocated
```

**Key Principle:**
> "Iterative allocation beats perfect planning."

You can't predict the future accurately. Better to allocate conservatively, measure real velocity, then adjust.

---

### Scenario D: Hiring/Team Decisions

**Example:** "Choose between 3 senior engineer candidates"

**Workflow:**

```bash
# Step 1: Decision plan for hiring
python scripts/search.py "choosing senior engineer from 3 finalists" --plan -p "Q1 Hiring"

# Output should recommend: Weighted Criteria Matrix

# Step 2: Get hiring-specific criteria
python scripts/search.py "hiring technical fit culture team" --domain criteria

# Step 3: CRITICAL - Identify biases in hiring (most dangerous!)
python scripts/search.py "affinity halo confirmation resume driven" --domain biases -n 5

# Step 4: Get group facilitation technique
python scripts/search.py "anonymous voting structured interview blind review" --domain facilitation

# Step 5: Implement bias mitigation:
#   - Define criteria BEFORE seeing resumes (or profiles)
#   - Blind review first (remove names, companies, universities)
#   - Structured interview questions (same for all candidates)
#   - Anonymous scoring before group discussion
#   - Devil's advocate role for top choice
#   - Reference checks (talk to previous managers)

# Step 6: Create comparison matrix
python scripts/search.py --matrix "Candidate A vs Candidate B vs Candidate C" \
  -c "technical_skills,domain_expertise,culture_fit,growth_potential,team_complement,references"

# Step 7: Document the decision
python scripts/search.py --journal "Senior engineer hire: chose [NAME] based on [CRITERIA]" \
  -p "Q1 Hiring"
```

**Bias Watch:** Hiring decisions are prone to affinity bias, halo effect, and confirmation bias. The most important mitigation is **defining criteria before seeing candidates**.

---

## 🔍 Problem-Solving Workflows

### Common Production Issue

**Example:** "API intermittently returns stale data"

**Process:**

```bash
# In your AI assistant with problem-solving-pro skill:

@workspace /solve My API returns stale data ~2% of the time after updates.
No clear pattern by time, user, or endpoint. Stack: Node.js + Express,
PostgreSQL (primary + read replica), Redis cache.
```

**The skill will guide you:**

```
1. DECOMPOSITION
   - CDN cache layer (possibility: serving cached response)
   - Application cache layer (possibility: Redis invalidation bug)
   - Database layer (possibility: reading from stale replica)
   - Network/infrastructure layer (possibility: packet loss)

2. HYPOTHESIS RANKING
   Rank by likelihood:
   - Hypothesis 1 (60%): Redis cache not invalidated on write
   - Hypothesis 2 (25%): Reading from replica with replication lag
   - Hypothesis 3 (10%): CDN caching response
   - Hypothesis 4 (5%): Race condition in app

3. TESTING STRATEGY
   Test Hypothesis 1 first (highest likelihood × easiest to test)
   - Check: Is EXPIRE called after update? Is key really deleted?
   - Look at: Redis logs, application code, TTL values

4. ROOT CAUSE
   Found: Cache-aside pattern + read replica + replication lag
   - PATCH invalidates cache ✓
   - GET has cache miss
   - GET reads from REPLICA (has 2-5s lag still)
   - GET repopulates cache with STALE data
   - Subsequent GETs serve stale for 5 minutes (TTL)

5. SOLUTION OPTIONS
   Option 1 (Quick): Read from PRIMARY on cache miss (30 min)
   Option 2 (Proper): Write-through cache (2 hours)
   Option 3 (Architectural): Consistent cache invalidation (1 day)
   Choice: Implement Option 2 (best risk/reward)

6. PREVENTION
   - Add monitoring for cache hit rate drop
   - Alert on staleness detection
   - Document cache consistency guarantees
```

---

## 💡 Tips for Best Results

### Before You Decide/Debug

1. **📋 Define the problem precisely**
   - Not: "Cloud is too expensive"
   - But: "Need cloud infrastructure for 500K req/sec, 18-month migration window, HIPAA compliance"

2. **👥 Identify all stakeholders early**
   - Who decides? Who's affected? Who has relevant experience?
   - Include them in criteria definition, not just final vote

3. **⚖️ Define criteria BEFORE evaluating options**
   - Prevents anchoring (first option influences scoring of others)
   - Prevents post-hoc rationalization ("This option is good because it has feature X")

4. **🧠 Check your biases explicitly**
   - Run: `python scripts/search.py "relevant keywords" --domain biases`
   - Apply specific remedies for each bias

5. **📊 Use decision journal religiously**
   - Document not just the decision, but the rationale
   - 6-12 months later, update with actual outcomes
   - This improves your decision calibration over time

### During Decision-Making

6. **🔍 Run sensitivity analysis for multi-option decisions**
   - Ask: "If I weight criterion X differently, does the winner change?"
   - Identifies which criteria actually swing the decision

7. **👂 Use structured group processes**
   - Not: "What do people think?" (groupthink, halo effect)
   - But: "Anonymous vote first, discuss gaps, revote"

8. **🧪 Run POCs for technical decisions**
   - Prove assumptions with real data
   - Don't trust estimates

9. **📞 Check references**
   - For vendors: Talk to customers
   - For hires: Call previous managers
   - For technologies: Test in your environment

10. **⏱️ Use iterative allocation for resource decisions**
    - Don't allocate all 100% upfront
    - Allocate 50-70%, measure velocity, adjust

### After Decision

11. **📖 Document the decision**
    ```bash
    python scripts/search.py --journal "Decision title" -p "Project Name"
    ```
    Include:
    - Options considered
    - Criteria and weights
    - Winner and why
    - Implementation plan
    - Known risks

12. **📅 Set a review date**
    - 3-6 months for tactical decisions
    - 12 months for strategic decisions
    - Update journal with actual outcomes

13. **🎓 Extract lessons learned**
    - What worked in the process?
    - What surprised you?
    - What would you do differently?
    - Which criteria proved most important?

---

## 🎓 Decision Frameworks Reference

### When to Use Each Framework

| Decision Type | Best Framework | Example |
|---------------|----------------|---------|
| **2 options** | Pros-Cons-Fixes | Keep simple vs add features |
| **3+ options** | Weighted Matrix | AWS vs Azure vs GCP |
| **Uncertain future** | Scenario Planning | Enter new market or not |
| **Sequential choices** | Decision Tree | Hire now vs wait 6mo? |
| **Resource/budget** | Iterative Allocation | Which projects get engineers |
| **Group alignment** | Nominal Group Technique | Team decision on strategy |
| **Testing hypotheses** | Hypothesis-Driven | Debugging root cause |

---

## ⚠️ Cognitive Biases to Watch

### High-Risk Biases (Always Watch)

| Bias | What It Does | How to Counter |
|------|-------------|-----------------|
| **Confirmation Bias** | You notice what confirms your first impression | Actively seek disconfirming evidence |
| **Anchoring** | First number/option influences everything | Get independent estimates before comparing |
| **Sunk Cost Fallacy** | Past investment makes you continue failing projects | Evaluate as if starting fresh today |
| **Overconfidence** | Too certain about uncertain outcomes | Use pre-mortem: assume it failed, work backward |
| **Status Quo Bias** | Prefer current state even when changing is better | Reframe as opportunity cost of NOT acting |

### Domain-Specific High-Risk Biases

**Hiring:**
- Affinity Bias (favor candidates like us)
- Halo Effect (one strong trait colors everything)
- Resume-Driven Development (choose for trendy skills, not fit)

**Technology:**
- Not Invented Here (build vs buy bias)
- Resume-Driven Decisions (choose trendy tech for resumé value)
- Status Quo Bias (stick with current even if better exists)

**Resource Allocation:**
- Planning Fallacy (projects take 2-3x longer than estimated)
- Overconfidence (too certain about estimates)

---

## 📖 Learning Path

### Week 1: Get Familiar
- [ ] Install both skills
- [ ] Read through examples/ directory (01-05)
- [ ] Try one simple decision using make-decision skill
- [ ] Try one simple debugging problem using problem-solving-pro

### Week 2: Build Habit
- [ ] Make one multi-option decision using full workflow
- [ ] Use group facilitation technique in a team decision
- [ ] Document decision with decision journal
- [ ] Identify and counter one cognitive bias explicitly

### Week 3: Deepen Practice
- [ ] Run sensitivity analysis on a multi-option decision
- [ ] Use decision journal to retrospective a past decision
- [ ] Help colleague/team member through the process
- [ ] Share a decision case study

### Week 4+: Become Expert
- [ ] Use decision frameworks automatically without consulting skill
- [ ] Help team improve decision quality
- [ ] Build decision culture in your organization
- [ ] Create custom use case in examples/ directory

---

## 🆘 Getting Help

### From the Skill Itself

```bash
# Quick start for decision-making
cd .github/prompts/make-decision
python scripts/search.py "help guide" --plan

# Search a specific domain
python scripts/search.py "keyword" --domain frameworks
python scripts/search.py "keyword" --domain biases
python scripts/search.py "keyword" --domain criteria
python scripts/search.py "keyword" --domain analysis
python scripts/search.py "keyword" --domain facilitation

# View available data
python scripts/search.py "list all frameworks" --domain frameworks
python scripts/search.py "list all biases" --domain biases
```

### From the Community

- See [examples/](../examples/) for detailed case studies
- Check templates 06-10 for structure
- Review README.md for full reference

---

## ✅ Checklist: Before You Make a Decision

- [ ] **Problem is precisely defined** (not vague)
- [ ] **Options are explicitly listed** (no hidden alternatives)
- [ ] **Criteria are defined BEFORE evaluating options**
- [ ] **Criteria have weights** (not all equally important)
- [ ] **You've checked relevant biases** (and applied remedies)
- [ ] **Stakeholders identified** (and included appropriately)
- [ ] **If group decision: using structured process** (not groupthink)
- [ ] **If technical: POC completed** (not just estimates)
- [ ] **If vendor: references checked** (not just sales pitch)
- [ ] **Decision will be documented** (journal entry created)
- [ ] **Review date set** (when to retrospective)

---

**Next Steps:**
1. Install the skills: `make-decision init --ai claude`
2. Pick a real decision you're facing this week
3. Work through the workflow above for your decision type
4. Document it with decision journal
5. 6 months later: update with actual outcomes

Happy deciding! 🎯
