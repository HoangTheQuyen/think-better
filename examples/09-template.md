# Use Case 09: [Vendor/Partner Selection Template]

**Decision:** [Choose between vendors, service providers, or business partners]

**Type:** Multi-Option Selection (Vendor)  
**Skill Used:** make-decision  
**Duration:** [Typically 2-4 weeks including RFP process]  
**Outcome:** [Vendor selected + contract negotiated]

---

## 📋 Context

**Situation:**  
[Vendor decisions involve:
- Long-term contractual commitment
- Service level agreements (SLAs)
- Integration complexity
- Switching costs]

**What We're Buying:**
[e.g., Cloud infrastructure, Payroll system, Legal services, Marketing agency]

**Vendors Under Consideration:**
1. **[Vendor A]** — [Quick summary]
2. **[Vendor B]** — [Quick summary]
3. **[Vendor C]** — [Quick summary]

**Requirements:**
- [Functional requirements]
- [SLA requirements: uptime, response time]
- [Integration requirements]
- [Compliance requirements: SOC2, HIPAA, etc.]

**Constraints:**
- Budget: [Annual spend limit]
- Timeline: [When do we need this live]
- Contract: [Length, exit clauses]

**Stakes:** High — [Multi-year commitment, hard to switch]

---

## 🔬 Process

### Step 1: Get vendor evaluation criteria

```bash
python scripts/search.py "vendor" --domain criteria
```

**Criteria (customized for vendor selection):**
- **Functionality:** Does it meet our requirements?
- **Reliability:** Uptime SLA, incident history
- **Support:** Response time, quality of support
- **Integration:** API quality, ease of integration
- **Pricing:** Transparent, predictable, scalable
- **Vendor Stability:** Financial health, customer retention
- **Security/Compliance:** Certifications, audit readiness

### Step 2: RFP (Request for Proposal) process

[Send identical RFP to all vendors]

**RFP Sections:**
1. **Functional fit:** [Can you do X, Y, Z?]
2. **Technical specs:** [API documentation, integration patterns]
3. **SLA commitments:** [Uptime, support response time]
4. **Pricing:** [Detailed pricing model, volume discounts]
5. **References:** [3 similar customers we can contact]
6. **Security:** [SOC2, penetration test results]

### Step 3: Reference checks

[Talk to existing customers BEFORE scoring]

| Vendor | Reference 1 | Reference 2 | Reference 3 | Key Feedback |
|--------|-------------|-------------|-------------|---------------|
| [Vendor A] | [Company, role] | [Company, role] | [Company, role] | [Summary] |
| [Vendor B] | [Company, role] | [Company, role] | [Company, role] | [Summary] |
| [Vendor C] | [Company, role] | [Company, role] | [Company, role] | [Summary] |

### Step 4: Generate comparison matrix

```bash
python scripts/search.py --matrix "[Vendor A] vs [Vendor B] vs [Vendor C]" \
  -c "functionality,reliability,support,integration,pricing,stability,security"
```

---

## 📊 Vendor Comparison

| Criterion | Weight | [Vendor A] | [Vendor B] | [Vendor C] |
|-----------|--------|------------|------------|------------|
| **Functionality** | 25 | [Score + notes] | [Score + notes] | [Score + notes] |
| **Reliability (SLA)** | 20 | [Score: e.g., 99.9%] | [Score] | [Score] |
| **Support** | 15 | [Score: response time] | [Score] | [Score] |
| **Integration** | 10 | [Score: API quality] | [Score] | [Score] |
| **Pricing** | 15 | [Score + annual cost] | [Score] | [Score] |
| **Vendor Stability** | 10 | [Score] | [Score] | [Score] |
| **Security** | 5 | [Score: certifications] | [Score] | [Score] |
| **TOTAL** | 100 | **[X.X]** | **[X.X]** | **[X.X]** |

---

## ✅ Decision

**Choice:** [Selected vendor]

**Rationale:**
1. [Functional fit: meets all must-haves]
2. [Reliability: SLA acceptable]
3. [References: strong feedback from similar companies]
4. [Pricing: within budget with growth runway]
5. [Exit strategy: contract allows termination with 90 days notice]

**Contract Negotiation Points:**
- [e.g., Negotiate down from $X to $Y based on multi-year commitment]
- [e.g., Add custom SLA clause for mission-critical feature]
- [e.g., Include exit assistance (data export) in contract]

**Implementation Plan:**
- **Month 1:** [Contract signing, kickoff, integration planning]
- **Month 2:** [POC with non-production data]
- **Month 3:** [Pilot with subset of users]
- **Month 4:** [Full rollout + legacy system sunset]

---

## 🎓 Lessons Learned

### Key Insight
**Reference checks are the highest signal.** Sales decks are optimized; real customer experiences reveal truth.

### Red Flags to Watch

| Red Flag | What It Means | How to Mitigate |
|----------|---------------|------------------|
| [e.g., Opaque pricing] | [Hidden costs likely] | [Demand detailed pricing before eval] |
| [e.g., No SOC2] | [Security not mature] | [Require certification timeline] |
| [e.g., No customer references] | [Customer churn high] | [Walk away] |

### Bias Mitigation

**Anchoring Bias:**
- ❌ First quote you see ($100K) makes others seem expensive or cheap
- ✅ Get all quotes before comparing

**Halo Effect:**
- ❌ "They work with [Big Brand]" doesn't mean they're good
- ✅ Judge each vendor on criteria independently

### Contract Tips

**Must-haves in vendor contracts:**
- [ ] Defined SLA with penalties for breach
- [ ] Data ownership clause (you own your data)
- [ ] Exit assistance (they help you migrate away)
- [ ] Security incident notification (within 24 hours)
- [ ] Annual price increase cap (e.g., max 5% per year)

### Applicability
Use this framework for:
- ✅ SaaS vendor selection
- ✅ Consulting firm selection
- ✅ Outsourcing partner evaluation
- ✅ Agency selection (marketing, design, recruiting)

---

**Decision Date:** [Date]  
**Review Date:** [6-12 months]  
**Decision Maker:** [Department head + Procurement]  
**Stakeholders:** [End users + Finance + Legal]

**Retrospective ([Date]):**
- [Service quality vs. promises]
- [Pricing accuracy (any hidden costs?)]
- [Support responsiveness]
- [Would you renew the contract?]
