# Use Case 02: Cloud Provider Selection

**Decision:** Choose between AWS, Azure, and GCP for enterprise cloud migration

**Type:** Multi-Option Selection (Strategic)  
**Skill Used:** make-decision  
**Duration:** ~2 hours (with stakeholder input)  
**Outcome:** ✅ AWS (weighted score 4.75 of 5)

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

Commands run from the project root. `$DECIDE` is the skill's script, for a Claude Code install
`DECIDE=.claude/skills/make-decision/scripts/search.py` (other tools: see the
[User Guide](../USER-GUIDE.md#running-the-scripts-yourself)). In a chat, `/decide <question>`
runs the same plan for you.

### Step 1: Generate comprehensive decision plan

```bash
python3 $DECIDE "AWS vs Azure vs GCP for our enterprise migration with HIPAA workloads" \
  --plan -p "Cloud Migration Strategy" -f markdown
```

**Output (shortened):**
```
Decision type: Multi-Option Selection (matched: 3 options)
Options: AWS | Azure | GCP
Recommended framework: Weighted Criteria Matrix
  (alternatives: Logic Tree Option Decomposition, Sensitivity Analysis Decision)
Evaluation criteria (Tech Stack / Framework Choice): team expertise 25, ecosystem 20,
  performance 20, maintainability 20, cost and licensing 15
```

**Bias warnings** (from the plan, with how they applied here):
- ⚠️ **Anchoring Effect** [High]: the first price quote influences all comparisons
- ⚠️ **Availability Heuristic** [Medium]: one vivid outage story about a provider outweighs the base rates
- ⚠️ **Confirmation Bias** [High]: a team with AWS experience looks for evidence that AWS fits

### Step 2: Adapt the criteria

The template's five criteria are a starting point. For a regulated migration we kept five, at most
(merging "migration tools" into service coverage):

- TCO over 5 years (not just compute)
- Team skills and learning curve
- Service coverage (managed services we need, migration tooling)
- Enterprise support quality
- Compliance certifications (HIPAA, SOC2)

`python3 $DECIDE "technology vendor cloud" --domain criteria` shows other templates
(Technology Selection, Vendor / Partner Selection) to borrow from.

### Step 3: Score each option

```bash
python3 $DECIDE --matrix "AWS vs Azure vs GCP" -f markdown \
  -c "TCO (5-year):25,Team skills:25,Service coverage:20,Enterprise support:15,Compliance:15" \
  --scores "AWS:4,5,5,5,5;Azure:4,3,4,4,5;GCP:5,2,4,3,4"
```

| Criterion | Weight | AWS | Azure | GCP |
|-----------|--------|-----|-------|-----|
| **TCO (5-year)** | 25 | 4 ($2.1M) | 4 ($2.0M) | 5 ($1.8M) |
| **Team skills** | 25 | 5 (60% exp) | 3 (30% exp) | 2 (10% exp) |
| **Service coverage** | 20 | 5 (all exists) | 4 (mostly) | 4 (mostly) |
| **Enterprise support** | 15 | 5 (excellent) | 4 (good) | 3 (adequate) |
| **Compliance** | 15 | 5 (all certs) | 5 (all certs) | 4 (missing 1) |
| **Weighted (script)** | 100 | **4.75** | **3.90** | **3.60** |

### Step 4: Sensitivity analysis

The same command prints the sensitivity check (this is the actual output):

```
Winner: AWS ahead of Azure by 0.85 (weighted average of the scores).
Smallest change that flips the winner: if the weight of TCO (5-year) rises from 25 to 140
(+115; its share of the total goes from 25% to 65%), GCP ties with AWS; beyond that it wins.
Team skills, Service coverage, Enterprise support, Compliance: no single change flips it.
```

We also asked: what if team skills mattered less (weight 10 instead of 25)? Re-running gives
AWS 4.71, Azure 4.06, GCP 3.88: the lead narrows but AWS still wins.

**Insight:** The result is robust. Only cost, weighted at about two thirds of the decision,
would make GCP the winner.

### Step 5: Group facilitation

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
python3 $DECIDE --journal "Cloud provider selection: AWS chosen for enterprise migration" \
  -p "Cloud Migration Strategy" --confidence 75 --review-in 6m
```

**6-Month Retrospective (to be updated):**
```bash
python3 $DECIDE --journal --update "cloud-provider-selection" \
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

**Confirmation Bias:**
- ❌ **Wrong:** AWS engineers dominated the conversation and argued only for AWS
- ✅ **Right:** Used anonymous voting + structured debate to surface minority views

**Status Quo Bias:**
- ❌ **Wrong:** Framed as "migrate to cloud"
- ✅ **Right:** Reframed as "what if we keep on-prem?" to reveal true costs ($3.5M/year)

### Sensitivity Analysis Value
The sensitivity test showed that **no reasonable weight change flips the result**: only cost,
at about two thirds of the total weight, would make GCP the winner. Team skills widen AWS's lead,
but even without them AWS wins on support, coverage and compliance. Had the team's experience been
on Azure, the Team skills scores (not the weights) would change and Azure could win.

**Actionable:** Read the "smallest change that flips the winner" line before debating weights;
if no plausible change flips it, spend the time on the scores instead.

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
