# Use Case 01: CLI Product Strategy

**Decision:** Should we bundle many skills in the CLI tool or keep it minimal?

**Type:** Binary Choice  
**Skill Used:** make-decision  
**Duration:** ~30 minutes  
**Outcome:** ✅ Keep minimal (2 skills)

---

## 📋 Context

**Situation:**  
- Built a CLI tool that packages AI assistant skills into a single binary
- Currently bundles 2 skills: `make-decision` (11 files) and `problem-solving-pro` (14 files)
- Considering whether to add 8+ more skills to increase immediate value

**Constraints:**
- Binary size grows with each skill added (~0.5 MB per skill)
- Maintenance burden increases (keeping skills updated)
- Build/test cycles get slower
- Want simple distribution (single binary)

**Stakes:** Medium - affects user experience, maintenance cost, and project scalability

---

## 🔬 Process

### Step 1: Install the skill

```bash
make-decision init --ai copilot --skill make-decision
```

### Step 2: Generate decision plan

```bash
cd .github/prompts/make-decision
python scripts/search.py "Should we add more bundled skills to the CLI tool or keep it minimal with 2 skills" \
  --plan -p "CLI Product Strategy" -f markdown
```

**Output:**
```
Decision Type: Binary Choice
Recommended Framework: Pros-Cons-Fixes Analysis
```

**Bias Warnings:**
- ⚠️ **Overconfidence** [High] — Don't assume you know what users need
- ⚠️ **Loss Aversion** [Medium] — Fear of missing features shouldn't override simplicity
- ⚠️ **Sunk Cost Fallacy** [High] — Past work on other skills shouldn't drive the decision

### Step 3: Create comparison matrix

```bash
python scripts/search.py --matrix "Keep minimal (2 skills) vs Add more skills (10 bundled)" \
  -c "binary_size,maintenance_burden,user_value,distribution_complexity,update_frequency"
```

### Step 4: Apply Pros-Cons-Fixes Analysis

#### Option A: Keep Minimal (2 skills)

**Pros:**
- ✅ Small binary size (~2.5 MB)
- ✅ Low maintenance burden
- ✅ Fast build times
- ✅ Simple distribution
- ✅ Easy to test comprehensively

**Cons:**
- ❌ Lower immediate value to users
- ❌ Users must find/add other skills themselves
- ❌ Doesn't showcase full capability of packaging system

**Can the cons be fixed?**
- ✅ **"Lower immediate value"** → FIXABLE via documentation + skill discovery feature
- ✅ **"Users must find skills"** → FIXABLE via `make-decision discover --remote` (future)
- ✅ **"Doesn't showcase capability"** → FIXABLE: 2 skills actually cover highest-value universal use cases

#### Option B: Add More Skills (10 bundled)

**Pros:**
- ✅ Higher immediate value
- ✅ Demonstrates versatility
- ✅ Users don't hunt for skills

**Cons:**
- ❌ Larger binary (5-7 MB)
- ❌ High maintenance burden
- ❌ Slower builds
- ❌ Version coupling (one skill forces rebuild)

**Can the cons be fixed?**
- ⚠️ **"Larger binary"** → PARTIALLY: Could split into lite/full versions (adds complexity)
- ❌ **"Maintenance burden"** → NOT FIXABLE: More skills = more work, period
- ❌ **"Version coupling"** → NOT FIXABLE: Nature of embedded content
- ⚠️ **"Slower builds"** → PARTIALLY: Can optimize CI/CD, but fundamental issue remains

---

## 📊 Weighted Scoring

| Criterion | Weight | Keep Minimal | Add More |
|-----------|--------|--------------|----------|
| Binary Size | 20 | 5 (2.5 MB) | 2 (5-7 MB) |
| Maintenance Burden | 20 | 5 (low) | 2 (high) |
| User Value | 20 | 4 (focused) | 5 (comprehensive) |
| Distribution Complexity | 20 | 5 (simple) | 3 (versioning) |
| Update Frequency | 20 | 5 (infrequent) | 2 (frequent) |
| **TOTAL** | 100 | **4.8 / 5.0** | **2.8 / 5.0** |

---

## ✅ Decision

**Choice:** Keep minimal (2 skills)

**Rationale:**
1. **All cons of "Keep Minimal" are fixable** — Documentation, templates, and discovery features solve them
2. **Most cons of "Add More" are permanent** — Maintenance and version coupling cannot be eliminated
3. **The 2 current skills are high-value** — Decision-making and problem-solving are universal needs
4. **Aligns with tool's purpose** — Users should be able to add their own skills easily

**Action Items:**
- ✅ Document skill creation guide in README
- ✅ Create example custom skill template
- 🔄 Consider `make-decision discover --remote` (future feature)
- 🔄 Build skill registry/marketplace (future)

---

## 🎓 Lessons Learned

### Key Insight
**Fixable cons beat permanent cons.** When comparing options, distinguish between:
- **Fixable cons** — Can be addressed with documentation, features, or process changes
- **Permanent cons** — Fundamental trade-offs that cannot be eliminated

### Pattern Recognition
This is a classic **Build vs. Feature Creep** decision:
- Adding more features feels like providing more value
- But it often creates permanent maintenance burden
- The minimal viable product with extensibility beats feature-rich product with rigidity

### Bias Mitigation
**Loss Aversion** was the key bias to watch:
- Fear: "Users won't see the value with only 2 skills"
- Reality: Users who need specialized skills will add them anyway
- Remedy: Reframe as **opportunity cost** — what do we lose by NOT keeping it simple?

### Applicability
Use this pattern for:
- ✅ Open-source library design (bundle everything vs. minimal + plugins)
- ✅ SaaS pricing tiers (single plan vs. many)
- ✅ API endpoints (comprehensive vs. minimal surface area)
- ✅ CI/CD pipelines (monorepo vs. separate repos)

---

**Decision Date:** March 3, 2026  
**Review Date:** June 2026 (3 months)  
**Status:** Implemented ✅

**Retrospective (to be updated):**
- Did users request more bundled skills?
- Did the skill discovery feature get built?
- Was maintenance burden manageable?
