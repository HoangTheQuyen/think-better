# Use Case 04: Engineering Resource Allocation

**Decision:** Allocate 10 engineers across 5 competing high-priority projects

**Type:** Resource Allocation  
**Skill Used:** make-decision  
**Duration:** 2 weeks (planning + stakeholder alignment)  
**Outcome:** ✅ Iterative allocation with re-evaluation after 3 weeks

---

## 📋 Context

**Situation:**  
- Q2 planning with 10 available engineering resources
- 5 projects competing for resources, all marked "P0" by stakeholders
- Must deliver revenue-impacting features while reducing tech debt

**Projects:**
1. **Mobile App Redesign** — UX overhaul, exec commitment to customers (6 engineers requested)
2. **API Rate Limiting** — Production incidents, SLA at risk (4 engineers requested)
3. **Data Pipeline Migration** — Legacy system EOL in 4 months (5 engineers requested)
4. **ML Recommendation Engine** — Revenue opportunity, needs PoC (3 engineers requested)
5. **Security Audit Remediation** — Compliance requirement (4 engineers requested)

**Total Requested:** 22 engineers  
**Available:** 10 engineers  
**Shortfall:** 12 engineers (55% gap)

**Constraints:**
- Can't hire fast enough (3-month lead time)
- Projects can't be delayed into Q3 (business commitments)
- Engineers have varying skills (not fungible)

**Stakes:** Very High — business commitments, production stability, compliance risk

---

## 🔬 Process

### Step 1: Generate decision plan

```bash
python scripts/search.py "allocate 10 engineers across 5 competing projects with constraints" \
  --plan -p "Q2 Resource Allocation"
```

**Output:**
```
Decision Type: Resource Allocation (Strategic, Time-Pressured)
Recommended Framework: Iterative Allocation
```

**Key Recommendations:**
- ⚠️ **Avoid "peanut butter" allocation** — Spreading evenly guarantees all projects fail
- ✅ **Use hypothesis-driven approach** — Allocate → measure → re-allocate
- ⚠️ **Watch for Planning Fallacy** — Projects take longer than estimated

### Step 2: Get resource allocation framework

```bash
python scripts/search.py "resource allocation iterative" --domain frameworks -n 2
```

**Framework: Iterative Allocation**
1. Allocate subset of resources (50-70%)
2. Run for 2-4 weeks, measure actual velocity/blockers
3. Re-allocate based on evidence
4. Repeat until resources fully assigned

**Why:** Reduces planning risk, allows learning before full commitment

### Step 3: Identify opportunity costs

```bash
python scripts/search.py "opportunity cost" --domain analysis
```

**Question for each project:** "What do we lose if we DON'T do this in Q2?"

| Project | Opportunity Cost if Deferred |
|---------|------------------------------|
| Mobile Redesign | Exec credibility loss, customer churn ($500K/quarter) |
| API Rate Limiting | **Production outages continue, SLA breach penalties ($50K/incident)** |
| Data Pipeline | **Hard deadline (4mo), vendor EOL, migration more complex if delayed** |
| ML Recommendation | Revenue upside delayed ($200K/quarter), competitive disadvantage |
| Security Remediation | **Compliance fail ($1M penalty), customer trust impact** |

### Step 4: Prioritization session (group facilitation)

Used **Dot Voting** technique:

```bash
python scripts/search.py "dot voting priority" --domain facilitation
```

**Process:**
1. Each stakeholder gets 10 dots
2. Allocate dots across projects (more dots = higher priority)
3. Discussion after vote to surface reasoning

**Results:**
- API Rate Limiting: 24 dots (production risk)
- Security Remediation: 22 dots (compliance)
- Data Pipeline: 20 dots (hard deadline)
- Mobile Redesign: 18 dots (exec commitment)
- ML Recommendation: 6 dots (exploration, can wait)

### Step 5: Iterative allocation plan

**Round 1 (Weeks 1-3): Allocate 7 engineers**

| Project | Engineers | Rationale |
|---------|-----------|------------|
| **API Rate Limiting** | 3 | Immediate production risk, clear scope |
| **Security Remediation** | 2 | Compliance deadline, can parallelize |
| **Data Pipeline** | 2 | Start discovery, assess true complexity |
| Mobile Redesign | 0 | Defer until dependencies clear |
| ML Recommendation | 0 | Defer, explore in H2 |

**Hold back 3 engineers** for re-allocation after Week 3 assessment.

**Metrics to measure:**
- API Rate Limiting: Incidents reduced? Scope creep?
- Security: Audit items closed? Blockers discovered?
- Data Pipeline: Migration complexity? Unknown unknowns?

---

## ✅ Decision

**Round 1 Allocation (Weeks 1-3):**
- **API Rate Limiting:** 3 engineers (stop production bleeding)
- **Security Remediation:** 2 engineers (compliance requirement)
- **Data Pipeline:** 2 engineers (assess migration complexity)
- **Reserve:** 3 engineers (allocate in Week 4 based on learnings)

**Rationale:**
1. **Production stability first** — API rate limiting prevents immediate $$$ loss
2. **Compliance risk second** — Security remediation prevents $1M penalty
3. **Gather evidence third** — Data pipeline assess before full commitment
4. **Defer revenue opportunities** — ML can wait, mobile redesign dependent on API stability

**Round 2 Plan (Week 4 re-assessment):**

After 3 weeks, measure:
- **If API rate limiting ahead of schedule** → shift 1 engineer to Data Pipeline
- **If Security finds major issues** → add 1 more engineer
- **If Data Pipeline more complex than estimated** → add 2 engineers, defer Mobile to Q3

---

## 📊 Actual Outcomes (Week 3 Re-Assessment)

### Week 3 Status Report

| Project | Status | Finding |
|---------|--------|----------|
| **API Rate Limiting** | ✅ 70% done | Simpler than expected, 1 eng can finish |
| **Security Remediation** | ⚠️ 50% done | Found 5 additional critical issues |
| **Data Pipeline** | ❌ 20% done | Legacy schema more complex, need 4 engineers |

### Round 2 Allocation (Weeks 4-8):

| Project | Change | New Total | Rationale |
|---------|--------|-----------|------------|
| API Rate Limiting | -2 | **1** | Ahead of schedule, 1 eng to finish |
| Security Remediation | +1 | **3** | Critical issues found |
| Data Pipeline | +2 | **4** | Complexity higher, hard deadline |
| Mobile Redesign | +2 | **2** | API stable now, dependencies clear |

**Result:** All 10 engineers allocated with data-driven adjustment.

---

## 🎓 Lessons Learned

### Key Insight
**Iterative allocation beats perfect planning.** Planning fallacy is real:
- API Rate Limiting: Estimated 4 weeks, actually took 5 weeks but with 1 engineer (not 3)
- Data Pipeline: Estimated "medium complexity", actually "high complexity"
- Security: Estimated 12 issues, found 17 during remediation

**Traditional approach would have:**
- Allocated all 10 engineers in Week 1
- Discovered issues too late to adjust
- Failed to deliver any project fully

**Iterative approach:**
- Allocated 70% in Week 1
- Learned actual complexity by Week 3
- Re-allocated based on evidence
- Delivered API + Security + Data Pipeline successfully

### Pattern Recognition

This is **Capital Allocation** pattern applied to engineering:
- **Venture Capital:** Don't fund all startups to Series A; fund seed → assess → Series A winners
- **Engineering:** Don't allocate all resources upfront; allocate → measure → increase winners

### Bias Mitigation

**Planning Fallacy:**
- ❌ **Wrong:** Trust initial estimates ("4 weeks, 3 engineers")
- ✅ **Right:** Allocate conservatively, measure actual velocity, adjust

**Sunk Cost Fallacy:**
- ❌ **Wrong:** "We already put 2 engineers on Data Pipeline, must continue"
- ✅ **Right:** Week 3 assessment revealed true complexity, adjusted allocation

**Overconfidence:**
- ❌ **Wrong:** "We can do all 5 projects with 10 engineers"
- ✅ **Right:** Deferred 2 projects (ML, Mobile initially), focused on top 3

### Decision Documentation

```bash
python scripts/search.py --journal "Q2 resource allocation: iterative approach across 5 projects" \
  -p "Q2 Planning"
```

**8-Week Retrospective:**
```bash
python scripts/search.py --journal --update "q2-resource-allocation" \
  --outcome "Delivered 4/5 projects (API, Security, Data, Mobile partial). ML deferred to H2. Iterative approach prevented over-commitment and enabled data-driven re-allocation."
```

### Applicability
Use this framework for:
- ✅ Sprint planning with capacity constraints
- ✅ Budget allocation across departments
- ✅ Marketing spend across channels (test → scale winners)
- ✅ Sales territory assignment (data-driven rebalancing)

---

**Decision Date:** March 15, 2026  
**Review Date:** May 15, 2026 (8 weeks)  
**Decision Maker:** VP Engineering + Engineering Managers  
**Stakeholders:** Exec team, Product Managers, 5 project leads

**Retrospective (May 2026):**
- ✅ **API Rate Limiting** — Delivered, incidents reduced 90%
- ✅ **Security Remediation** — Delivered, passed compliance audit
- ✅ **Data Pipeline Migration** — Delivered (1 week late, acceptable)
- ⚠️ **Mobile Redesign** — 60% complete, finishing in Q3 Week 1
- ❌ **ML Recommendation** — Deferred to H2 (correct decision, no regrets)

**Process Impact:**
- Traditional approach would have spread engineers thin across all 5 → likely 0 complete
- Iterative approach: 3 fully delivered, 1 nearly complete, 1 intentionally deferred
- **Team morale high** — Seeing projects complete builds momentum vs. perpetual WIP
