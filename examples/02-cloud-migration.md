# Use Case 02: Cloud Provider Selection

**Decision:** Choose between AWS, Azure, and GCP for enterprise cloud migration

**Type:** Multi-Option Selection (Strategic)  
**Skill Used:** make-decision  
**Duration:** ~2 hours (with stakeholder input)  
**Outcome:** ✅ AWS (score: 4.2/5.0)

---

## 📋 Context

**Situation:**  
- Enterprise company migrating from on-premises data centers to cloud
- 200+ applications, 50 TB data, 100 engineers
- Need multi-region deployment, compliance (HIPAA, SOC2), 24/7 support

**Constraints:**
- Budget: $2M/year cloud spend
- Timeline: 18-month migration
- Team: 60% AWS-experienced, 30% Azure, 10% GCP
- Must maintain existing PostgreSQL, Redis, RabbitMQ

**Stakes:** High - 5-year commitment, expensive to reverse

---

## 🔬 Process

### Step 1: Generate comprehensive decision plan

```bash
python scripts/search.py "choosing cloud provider for enterprise migration: AWS vs Azure vs GCP with HIPAA compliance" \
  --plan -p "Cloud Migration Strategy" -f markdown
```

**Output:**
```
Decision Type: Multi-Option Selection (Strategic, High Uncertainty)
Recommended Framework: Weighted Criteria Matrix + Sensitivity Analysis
```

**Bias Warnings:**
- ⚠️ **Status Quo Bias** — Team comfortable with on-prem may resist change
- ⚠️ **Anchoring** — First price quote influences all comparisons
- ⚠️ **Affinity Bias** — Team with AWS experience may favor AWS regardless of fit

### Step 2: Get evaluation criteria template

```bash
python scripts/search.py "technology evaluation" --domain criteria -n 1
```

**Output (adapted for cloud providers):**
- Cost optimization (TCO, not just compute)
- Team expertise/learning curve
- Service coverage (managed services we need)
- Enterprise support quality
- Compliance certifications (HIPAA, SOC2)
- Migration tools/assistance program

### Step 3: Generate comparison matrix

```bash
python scripts/search.py --matrix "AWS vs Azure vs GCP" \
  -c "tco_5year,team_skills,service_coverage,enterprise_support,compliance,migration_tools"
```

### Step 4: Score each option

| Criterion | Weight | AWS | Azure | GCP |
|-----------|--------|-----|-------|-----|
| **TCO (5-year)** | 25 | 4 ($2.1M) | 4 ($2.0M) | 5 ($1.8M) |
| **Team Skills** | 20 | 5 (60% exp) | 3 (30% exp) | 2 (10% exp) |
| **Service Coverage** | 20 | 5 (all exists) | 4 (mostly) | 4 (mostly) |
| **Enterprise Support** | 15 | 5 (excellent) | 4 (good) | 3 (adequate) |
| **Compliance** | 10 | 5 (all certs) | 5 (all certs) | 4 (missing 1) |
| **Migration Tools** | 10 | 4 (good) | 5 (Azure Migrate) | 3 (basic) |
| **TOTAL** | 100 | **4.5** | **3.9** | **3.7** |

### Step 5: Sensitivity analysis

**Question:** What if team skills were less important (weight: 10 instead of 20)?

| Provider | Original Score | New Score |
|----------|----------------|-----------|
| AWS | 4.5 | **4.3** ⬇️ |
| Azure | 3.9 | **4.0** ⬆️ |
| GCP | 3.7 | **4.0** ⬆️ |

**Insight:** AWS lead narrows significantly. The decision hinges on whether we value existing team skills.

### Step 6: Group facilitation

Used **Structured Debate** technique:
1. Split team into 3 groups (one champions each provider)
2. Each group presents strongest case for their option
3. Other groups ask challenging questions
4. Anonymous vote before and after debate

**Pre-debate:** AWS (70%), Azure (20%), GCP (10%)  
**Post-debate:** AWS (60%), Azure (25%), GCP (15%)

Debate revealed:
- GCP's cost savings offset by retraining time (6-9 months)
- Azure's migration tools are strong but team lacks Windows expertise
- AWS has mature third-party ecosystem (monitoring, security)

---

## ✅ Decision

**Choice:** AWS

**Rationale:**
1. **Team skills matter** — 18-month migration needs experienced engineers
2. **Risk mitigation** — Mature ecosystem reduces unknowns
3. **Cost difference acceptable** — $300K premium over 5 years ($5K/month) justified by productivity
4. **Proven compliance** — Existing customers in healthcare with similar architecture

**Contingency Plan:**
- Cross-train 10 engineers on Azure (hedge against future)
- Use Terraform (multi-cloud IaC) to reduce lock-in
- Include exit cost analysis in annual review

---

## 📊 Decision Documentation

Created decision journal entry:

```bash
python scripts/search.py --journal "Cloud provider selection: AWS chosen for enterprise migration" \
  -p "Cloud Migration Strategy"
```

**6-Month Retrospective (to be updated):**
```bash
python scripts/search.py --journal --update "cloud-provider-selection" \
  --outcome "Migration 40% complete, on schedule, team velocity high due to AWS expertise"
```

---

## 🎓 Lessons Learned

### Key Insight
**Team skills are a hidden multiplier.** The "best" technology on paper (GCP's cost) loses when you factor in:
- Learning curve delays
- Momentum loss during knowledge transfer
- Higher error rates during learning phase
- Team morale impact

### Pattern Recognition
This is a **Build vs. Buy vs. Partner** pattern applied to infrastructure:
- **Build equivalent:** GCP (cheapest but requires most learning)
- **Buy equivalent:** AWS (premium but proven)
- **Partner equivalent:** Azure (middle ground but Windows-centric)

### Bias Mitigation Tactics

**Anchoring Bias:**
- ❌ **Wrong:** Got AWS quote first ($2.1M), then compared others to it
- ✅ **Right:** Generated independent estimates for all three, revealed in parallel

**Affinity Bias:**
- ❌ **Wrong:** AWS engineers dominated the conversation
- ✅ **Right:** Used anonymous voting + structured debate to surface minority views

**Status Quo Bias:**
- ❌ **Wrong:** Framed as "migrate to cloud"
- ✅ **Right:** Reframed as "what if we keep on-prem?" to reveal true costs ($3.5M/year)

### Sensitivity Analysis Value
The sensitivity test revealed that **team skills was the swing factor**:
- If we had multi-cloud experience → GCP would win
- If we had Azure/.NET shops → Azure would win
- Since we have AWS depth → AWS wins

**Actionable:** For future decisions, identify the "swing criteria" early and validate it thoroughly.

### Applicability
Use this framework for:
- ✅ Database selection (Postgres, MySQL, MongoDB, etc.)
- ✅ Programming language choice for new microservice
- ✅ CI/CD platform (GitHub Actions, GitLab, Jenkins)
- ✅ Monitoring stack (Datadog, New Relic, Prometheus)

---

**Decision Date:** January 15, 2026  
**Review Date:** July 15, 2026 (6 months)  
**Decision Maker:** VP Engineering + 3 Principal Engineers  
**Stakeholders:** 100 engineers, CFO, CTO

**Retrospective (June 2026):**
- ✅ Migration 40% complete, on schedule
- ✅ Team velocity high (existing AWS knowledge pays off)
- ⚠️ Cost tracking: $2.2M run rate (10% over estimate due to data transfer)
- 🔄 Action: Optimize inter-region traffic, implement FinOps dashboard
