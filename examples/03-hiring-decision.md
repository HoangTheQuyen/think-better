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

```bash
python scripts/search.py "hiring senior software engineer from 3 finalists with payments domain" \
  --plan -p "Backend Engineer Hire Q1"
```

**Output:**
```
Decision Type: Multi-Option Selection (Hiring Decision)
Recommended Framework: Weighted Criteria Matrix
```

**Bias Warnings (CRITICAL for hiring):**
- ⚠️ **Affinity Bias** [High] — We favor candidates similar to us
- ⚠️ **Halo Effect** [High] — One strong trait (e.g., "ex-FAANG") colors everything
- ⚠️ **Confirmation Bias** [High] — First impression drives what we notice in interview

### Step 2: Get hiring criteria template

```bash
python scripts/search.py "hiring" --domain criteria
```

**Criteria (customized):**
- Technical skills (Golang, distributed systems, payments)
- Domain expertise (payments, fraud, compliance)
- Culture fit (startup pace, ownership mentality)
- Growth potential (can grow to staff/principal)
- Team complement (fills skill gaps)
- References (credible, enthusiastic)
- Compensation alignment (within budget + equity expectations)

### Step 3: Define criteria BEFORE seeing resumes

**Critical:** To avoid anchoring bias, we defined weights before round 1 interviews:

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| Technical Skills | 20 | Must be strong, but all three are qualified |
| Domain Expertise | 25 | **Highest** — payments knowledge is rare |
| Culture Fit | 15 | Important for retention |
| Growth Potential | 10 | Nice but not critical (senior, not staff) |
| Team Complement | 20 | We have algorithms experts, need domain depth |
| References | 5 | Hygiene factor |
| Compensation | 5 | All within range |

### Step 4: Structured interview process

Each candidate got identical treatment:
1. **Technical Screen** (same coding problems)
2. **System Design** (same prompt: "design payment processing system")
3. **Domain Deep-Dive** (same questions: "how do you handle idempotency?")
4. **Culture Interview** (same behavioral questions)
5. **Anonymous Scoring** (before team discussion)

### Step 5: Comparison matrix

```bash
python scripts/search.py --matrix "Candidate A vs Candidate B vs Candidate C" \
  -c "technical,domain,culture,growth,complement,references,compensation"
```

**Scoring:**

| Criterion | Weight | Candidate A | Candidate B | Candidate C |
|-----------|--------|-------------|-------------|-------------|
| **Technical Skills** | 20 | 5 (excellent) | 4 (strong) | 5 (excellent) |
| **Domain Expertise** | 25 | 2 (weak) | **5** (expert) | 3 (basic) |
| **Culture Fit** | 15 | 3 (corporate) | **5** (startup fit) | 4 (good) |
| **Growth Potential** | 10 | 5 (high) | 4 (solid) | 5 (high) |
| **Team Complement** | 20 | 2 (overlap) | **5** (fills gap) | 3 (some overlap) |
| **References** | 5 | 4 | 5 | 5 |
| **Compensation** | 5 | 3 ($180K) | **5** ($160K) | 1 ($200K) |
| **TOTAL** | 100 | **3.3** | **4.7** ⭐ | **3.8** |

### Step 6: Group facilitation - Anonymous Input

Used **Nominal Group Technique:**
1. Each interviewer scored independently (no discussion)
2. Revealed scores anonymously
3. Discussed only the **gaps** (where scores differed by 2+)
4. Re-voted after discussion

**Pre-discussion:** Candidate A (3 votes), Candidate B (2 votes), Candidate C (3 votes)  
**Post-discussion:** Candidate B (7 votes), Candidate A (1 vote)

**What changed:**
- **Team realized Candidate A = "mini-me"** — Same Google background as 3 team members (affinity bias)
- **Halo effect exposed** — "Ex-FAANG" impressed people, but actual domain knowledge was weak
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

| Bias Detected | How It Manifested | Remedy Applied |
|---------------|-------------------|----------------|
| **Halo Effect** | "Ex-Google" impressed everyone | Blind resume review first, company names revealed later |
| **Affinity Bias** | Googlers favored Candidate A | Anonymous voting before group discussion |
| **Confirmation Bias** | First impressions stuck | Each interviewer used structured rubric |
| **Anchoring** | First salary mentioned ($200K) made others seem cheap | Got all comp expectations up front, evaluated separately |

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

**Question:** What if compensation weight was higher (15 instead of 5)?

| Candidate | Original | High Comp Weight | Change |
|-----------|----------|------------------|--------|
| A | 3.3 | 3.1 | ⬇️ |
| B | 4.7 | **4.6** | ⬇️ (still wins) |
| C | 3.8 | 3.2 | ⬇️⬇️ (big drop) |

**Insight:** Decision is robust. Candidate B wins across reasonable weight variations.

### Retrospective Decision Documentation

Created journal entry with explicit biases addressed:

```bash
python scripts/search.py --journal "Senior backend engineer hire: Candidate B (payments expert)" \
  -p "Q1 Hiring"
```

**3-Month Update:**
```bash
python scripts/search.py --journal --update "senior-backend-hire" \
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
