# Use Case 08: [Technical Architecture Template]

**Decision:** [Choose between competing technologies, architectures, or technical approaches]

**Type:** Multi-Option Selection (Technical)  
**Skill Used:** make-decision  
**Duration:** [Typically 1-3 weeks including POCs]  
**Outcome:** [Technology chosen + migration plan]

---

## 📋 Context

**Situation:**  
[Technical decisions often involve:
- Competing technologies or frameworks
- Need for proof-of-concept
- Team skill gaps
- Long-term maintenance considerations]

**Technical Requirements:**
- [Performance: throughput, latency targets]
- [Scale: data volume, request volume]
- [Integration: existing systems]
- [Compliance: security, audit requirements]

**Options:**
1. **[Technology A]** — [Pros/cons summary]
2. **[Technology B]** — [Pros/cons summary]
3. **[Technology C]** — [Pros/cons summary]

**Constraints:**
- [Budget for licenses, infrastructure]
- [Team skills and learning curve]
- [Migration timeline]
- [Vendor lock-in concerns]

**Stakes:** High — [Multi-year commitment]

---

## 🔬 Process

### Step 1: Get technology evaluation criteria

```bash
python scripts/search.py "technology" --domain criteria
```

**Criteria Template (customized):**
- Performance (benchmark results)
- Developer experience (learning curve, tooling)
- Community/ecosystem (libraries, support)
- Operational complexity (deployment, monitoring)
- Total cost of ownership (licenses + infrastructure + people)
- Migration path (how hard to adopt)

### Step 2: Run proof-of-concepts

[For technical decisions, POCs are essential]

**POC Scope:**
- [ ] Implement core use case with each technology
- [ ] Benchmark performance
- [ ] Assess developer ergonomics
- [ ] Estimate migration effort

| Technology | POC Result | Performance | Dev Experience | Migration Effort |
|------------|------------|-------------|----------------|------------------|
| [Tech A] | [Pass/Fail] | [Metric] | [Rating 1-5] | [Estimate] |
| [Tech B] | [Pass/Fail] | [Metric] | [Rating 1-5] | [Estimate] |
| [Tech C] | [Pass/Fail] | [Metric] | [Rating 1-5] | [Estimate] |

### Step 3: Generate comparison matrix

```bash
python scripts/search.py --matrix "[Tech A] vs [Tech B] vs [Tech C]" \
  -c "performance,dev_experience,ecosystem,ops_complexity,tco,migration"
```

### Step 4: Check for biases

```bash
python scripts/search.py "resume status quo" --domain biases
```

**Common biases in tech decisions:**
- **Resume-Driven Development** — Choosing trendy tech for career growth
- **Status Quo Bias** — Sticking with current stack even when better options exist
- **Not Invented Here** — Building instead of buying because "we can do it better"

---

## 📊 Technical Comparison

| Criterion | Weight | [Tech A] | [Tech B] | [Tech C] |
|-----------|--------|----------|----------|----------|
| **Performance** | 25 | [Score + metric] | [Score + metric] | [Score + metric] |
| **Dev Experience** | 20 | [Score] | [Score] | [Score] |
| **Ecosystem** | 15 | [Score] | [Score] | [Score] |
| **Ops Complexity** | 15 | [Score] | [Score] | [Score] |
| **TCO (3-year)** | 15 | [Score + $] | [Score + $] | [Score + $] |
| **Migration** | 10 | [Score + timeline] | [Score + timeline] | [Score + timeline] |
| **TOTAL** | 100 | **[X.X]** | **[X.X]** | **[X.X]** |

---

## ✅ Decision

**Choice:** [Selected technology]

**Rationale:**
1. [Technical fit: meets requirements]
2. [Team readiness: skills or trainable]
3. [Ecosystem maturity: production-ready]
4. [Total cost: acceptable TCO]

**Migration Plan:**
- **Week 1-2:** [Training, environment setup]
- **Week 3-4:** [Pilot with non-critical service]
- **Month 2-3:** [Migrate core services]
- **Month 4:** [Full cutover + legacy deprecation]

**Risk Mitigation:**
- [Fallback plan if POC doesn't scale]
- [Vendor diversification strategy]
- [Knowledge transfer and documentation]

---

## 🎓 Lessons Learned

### Key Insight
[What made this technology the right choice]

### Technical Debt Consideration
[Every technology choice creates future debt. Document the trade-offs.]

**What we gain:**
- [Benefit 1]
- [Benefit 2]

**What we accept:**
- [Trade-off 1: e.g., vendor lock-in]
- [Trade-off 2: e.g., not polyglot-friendly]

### Bias Mitigation

| Bias | How We Caught It | Remedy |
|------|------------------|--------|
| [e.g., Hype] | [Team wanted trendy tech] | [Required POC with business metrics] |

### Applicability
Use this framework for:
- ✅ Database selection
- ✅ Programming language choice for new service
- ✅ Observability stack (logging, metrics, tracing)
- ✅ Authentication/authorization system

---

**Decision Date:** [Date]  
**Review Date:** [6-12 months]  
**Decision Maker:** [Tech Lead + Architect]  
**Stakeholders:** [Engineering team]

**Retrospective ([Date]):**
- [Performance in production]
- [Team satisfaction]
- [Unexpected challenges]
- [Would you choose the same technology today?]
