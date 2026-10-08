# Use Case 03: Senior Engineer Hiring

**Decision:** Choose between three senior software engineer finalists

**Type:** Multi-Option Selection (Hiring)  
**Skill Used:** make-decision  
**Duration:** 3 weeks (interviews + decision)  
**Outcome:** ✅ Candidate B selected

---

## 📋 Context

**Situation:**  
- Tech company hiring senior backend engineer for payments team
- Three finalists after screening 45 applicants
- Critical role: handles $50M/year transaction volume

**Candidates:**
- **Candidate A:** 8 years exp, ex-Google, strong algorithms, wants $180K
- **Candidate B:** 6 years exp, startup background, payments domain expert, wants $160K
- **Candidate C:** 10 years exp, ex-Amazon, leadership experience, wants $200K

**Constraints:**
- Budget: $160-190K salary range
- Start date: Within 2 months
- Team gap: Need payments domain knowledge + Golang expertise

**Stakes:** High - wrong hire costs 12-18 months + $150K+ in total cost

---

## 🔬 Process

### Step 1: Generate decision plan

Commands run from the project root. `$DECIDE` is the skill's script, for a Claude Code install
`DECIDE=.claude/skills/make-decision/scripts/search.py` (other tools: see the
[User Guide](../USER-GUIDE.md#running-the-scripts-yourself)). In a chat, `/decide <question>`
runs the same plan for you.

```bash
python3 $DECIDE "hiring senior software engineer from 3 finalists with payments domain" \
  --plan -p "Backend Engineer Hire Q1"
```

**Output (shortened):**
```
Decision type: Multi-Option Selection
Recommended framework: Weighted Criteria Matrix
Evaluation criteria (Hiring Decision): Skills match, Growth potential, Values and team add,
  Team complement, Compensation fit
```

**Bias warnings** (from the plan, with how they applied here):
- ⚠️ **Anchoring Effect** [High]: the first candidate, first impression or first salary sets the bar
- ⚠️ **Confirmation Bias** [High]: the first impression drives what we notice in the interview
- ⚠️ **Availability Heuristic** [Medium]: one vivid interview story outweighs the rest of the evidence

### Step 2: Get hiring criteria template

```bash
python3 $DECIDE "hiring" --domain criteria
```

**Criteria (customized from the template, five at most):**
- Technical skills (Golang, distributed systems)
- Domain expertise (payments, fraud, compliance)
- Values and team add (startup pace, ownership; references checked here)
- Team complement (fills skill gaps)
- Compensation fit (within budget and equity expectations)

### Step 3: Define criteria BEFORE seeing resumes

**Critical:** To avoid anchoring bias, we defined weights before round 1 interviews:

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| Technical skills | 20 | Must be strong, but all three are qualified |
| Domain expertise | 30 | **Highest**: payments knowledge is rare |
| Values and team add | 20 | Important for retention |
| Team complement | 20 | We have algorithms experts, need domain depth |
| Compensation fit | 10 | All close to the range |

### Step 4: Structured interview process

Each candidate got identical treatment:
1. **Technical Screen** (same coding problems)
2. **System Design** (same prompt: "design payment processing system")
3. **Domain Deep-Dive** (same questions: "how do you handle idempotency?")
4. **Culture Interview** (same behavioral questions)
5. **Anonymous Scoring** (before team discussion)

### Step 5: Comparison matrix

```bash
python3 $DECIDE --matrix "Candidate A vs Candidate B vs Candidate C" \
  -c "Technical skills:20,Domain expertise:30,Values and team add:20,Team complement:20,Compensation fit:10" \
  --scores "Candidate A:5,2,3,2,3;Candidate B:4,5,5,5,5;Candidate C:5,3,4,3,1"
```

**Scoring:**

| Criterion | Weight | Candidate A | Candidate B | Candidate C |
|-----------|--------|-------------|-------------|-------------|
| **Technical skills** | 20 | 5 (excellent) | 4 (strong) | 5 (excellent) |
| **Domain expertise** | 30 | 2 (weak) | **5** (expert) | 3 (basic) |
| **Values and team add** | 20 | 3 (corporate) | **5** (startup fit) | 4 (good) |
| **Team complement** | 20 | 2 (overlap) | **5** (fills gap) | 3 (some overlap) |
| **Compensation fit** | 10 | 3 ($180K) | **5** ($160K) | 1 ($200K) |
| **Weighted (script)** | 100 | **2.90** | **4.80** ⭐ | **3.40** |

The script names Candidate B the winner; only Technical skills at two thirds of the total weight
would make Candidate C tie with it.

### Step 6: Group facilitation - Anonymous Input

Used **Nominal Group Technique:**
1. Each interviewer scored independently (no discussion)
2. Revealed scores anonymously
3. Discussed only the **gaps** (where scores differed by 2+)
4. Re-voted after discussion

**Pre-discussion:** Candidate A (3 votes), Candidate B (2 votes), Candidate C (3 votes)  
**Post-discussion:** Candidate B (7 votes), Candidate A (1 vote)

**What changed:**
- **Team realized Candidate A = "mini-me"**: the same Google background as 3 team members, who looked for evidence that confirmed their first impression (Confirmation Bias)
- **The brand set the bar**: "Ex-FAANG" impressed people first (Anchoring Effect), but actual domain knowledge was weak
- **Team complement became obvious** — We already have 4 Googlers; need payment expertise

---

## ✅ Decision

**Choice:** Candidate B

**Rationale:**
1. **Domain expertise is the multiplier** — Can teach Golang, can't easily teach payments
2. **Fills the team gap** — Algorithms/infrastructure covered, payments knowledge rare
3. **Culture fit + ownership** — Startup background = comfortable with ambiguity
4. **Budget alignment** — $160K at bottom of range, room for retention raises
5. **Immediate impact** — Can contribute productively week 1 due to domain knowledge

**Risk Mitigation:**
- Pair with Candidate A's technical bar (offer rejected, but validated our process)
- 3-month checkpoint to assess integration
- Assign payments architecture ownership explicitly

---

## 🎓 Lessons Learned

### Key Insight
**Biases are strongest in hiring.** We documented multiple bias interventions:

| Bias | How It Manifested | Remedy Applied |
|------|-------------------|----------------|
| **Anchoring Effect** | "Ex-Google" impressed everyone; the first salary mentioned ($200K) made others seem cheap | Blind resume review first, company names revealed later; all comp expectations collected up front |
| **Confirmation Bias** | Googlers favored Candidate A; first impressions stuck | Structured rubric per interviewer; anonymous voting before group discussion |
| **Availability Heuristic** | One great whiteboard session dominated the debrief | Scores per criterion, written before the debrief |

### Pattern Recognition
This is **Build vs. Buy talent:**
- **Candidate A = "Buy"** — Premium brand (FAANG), expensive, needs domain training
- **Candidate B = "Build partnership"** — Domain expert, culture fit, ready to contribute
- **Candidate C = "Overqualified buy"** — Above budget, may leave quickly

### Critical Process Elements

**What worked:**
1. ✅ **Define criteria before seeing resumes** — Prevented post-hoc rationalization
2. ✅ **Structured interviews** — Same questions, comparable data
3. ✅ **Anonymous scoring first** — Surface minority views before group pressure
4. ✅ **Explicit bias check** — Called out when someone said "I just like them"

**What didn't work:**
1. ❌ Initial weights too balanced (20/20/20...) — Didn't reflect team's actual needs
2. ❌ First round of cultural fit questions too generic — Refined in round 2

### Sensitivity Analysis

**Question:** What if compensation weight was higher (25 instead of 10)? Re-running the matrix:

| Candidate | Original | High Comp Weight | Change |
|-----------|----------|------------------|--------|
| A | 2.90 | 2.91 | ➖ |
| B | 4.80 | **4.83** | ⬆️ (still wins) |
| C | 3.40 | 3.09 | ⬇️ (big drop) |

**Insight:** Decision is robust. The script's sensitivity check agrees: only Technical skills at
about two thirds of the total weight would bring Candidate C level with B.

### Retrospective Decision Documentation

Created journal entry with explicit biases addressed:

```bash
python3 $DECIDE --journal "Senior backend engineer hire: Candidate B (payments expert)" \
  -p "Q1 Hiring"
```

**3-Month Update:**
```bash
python3 $DECIDE --journal --update "senior-backend-hire" \
  --outcome "Candidate B exceeded expectations. Led payment idempotency redesign, mentored 2 juniors, prevented $200K fraud loss in month 2. Promotion to Staff Engineer recommended."
```

### Applicability
Use this framework for:
- ✅ Any high-stakes hiring decision
- ✅ Promotion decisions (internal candidates)
- ✅ Vendor selection (similar bias risks)
- ✅ Partnership evaluations

---

**Decision Date:** February 10, 2026  
**Review Date:** May 10, 2026 (3 months)  
**Decision Maker:** Engineering Manager + 3 Senior Engineers + VP Engineering  
**Stakeholders:** Payments team (8 engineers)

**Retrospective (May 2026):**
- ✅ **Exceeded expectations** — Led critical payment idempotency redesign
- ✅ **Team impact** — Mentored 2 junior engineers, improved code review quality
- ✅ **Business impact** — Identified fraud pattern that saved $200K
- 🎯 **Promotion recommended** — Staff Engineer promotion at 9-month mark
- 📖 **Process validated** — Structured approach significantly reduced hire time (3 weeks vs. 6-week average)
