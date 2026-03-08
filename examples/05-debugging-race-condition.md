# Use Case 05: Debugging API Race Condition

**Problem:** API sometimes returns stale data after updates

**Type:** Problem-Solving (Root Cause Analysis)  
**Skill Used:** problem-solving-pro  
**Duration:** 4 hours (discovery + fix + validation)  
**Outcome:** ✅ Root cause identified and fixed

---

## 📋 Context

**Situation:**  
- Production API serving 10K req/sec
- Intermittent reports: "I updated my profile but API still shows old data"
- Happens ~2% of requests (200/sec affected)
- No pattern by time of day, user, or endpoint

**Stack:**
- Node.js API (Express)
- PostgreSQL primary + read replica (streaming replication)
- Redis cache (cache-aside pattern)
- CDN in front (CloudFront)

**Constraints:**
- Must fix without downtime
- Can't reproduce consistently in staging
- Customer escalations mounting

**Stakes:** High — customer trust, potential data integrity perception issue

---

## 🔬 Process

### Step 1: Install problem-solving skill

```bash
make-decision init --ai claude --skill problem-solving-pro
```

### Step 2: Use skill to guide investigation

In Claude/Cursor AI assistant:
```
@workspace /solve My API sometimes returns stale data after updates. 
POST /users/{id} succeeds (200 OK) but subsequent GET /users/{id} 
returns old data for ~30 seconds, then corrects itself.
```

**Skill responds with structured problem-solving workflow:**

---

### Step 3: Problem Decomposition

Skill breaks problem into layers:

```
┌─────────────────────┐
│   CDN Cache Layer   │ ← Could be serving cached responses?
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Application Cache  │ ← Redis invalidation issue?
│      (Redis)        │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Application Code   │ ← Reading from wrong DB?
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Database Layer     │ ← Replication lag?
│  (Primary/Replica)  │
└─────────────────────┘
```

### Step 4: Hypothesis Generation

Skill generates ranked hypotheses:

| # | Hypothesis | Likelihood | Test |
|---|------------|------------|------|
| 1 | **Redis cache not invalidated on write** | 60% | Check if EXPIRE called after POST |
| 2 | **Read from replica with replication lag** | 25% | Check if GET uses replica, measure lag |
| 3 | **CDN serving cached response** | 10% | Check Cache-Control headers |
| 4 | **Race condition in app code** | 5% | Check if write/read concurrent |

**Prioritization:** Test Hypothesis 1 first (highest likelihood × easiest to test).

### Step 5: Evidence Collection

**Test Hypothesis 1: Redis cache invalidation**

```javascript
// Checked code in PATCH /users/:id handler
app.patch('/users/:id', async (req, res) => {
  const user = await db.users.update(req.params.id, req.body);
  
  // ❌ FOUND THE BUG
  // Cache invalidation is here, but...
  await redis.del(`user:${req.params.id}`);
  
  res.json(user);
});

// Checked GET /users/:id handler
app.get('/users/:id', async (req, res) => {
  // Cache-aside pattern
  let user = await redis.get(`user:${req.params.id}`);
  
  if (!user) {
    // ⚠️ ISSUE: Reads from REPLICA, not primary
    user = await db.replica.users.findById(req.params.id);
    await redis.set(`user:${req.params.id}`, user, 'EX', 300); // 5min TTL
  }
  
  res.json(user);
});
```

**Root Cause Identified:**

**The bug is a combination of Hypothesis 1 + 2:**

1. **PATCH invalidates Redis** ✅ (this works)
2. **GET has cache miss** → reads from **replica** (not primary)
3. **Replica has 2-5 second replication lag** (normal)
4. **GET re-populates Redis with stale data from replica**
5. **Subsequent GETs** serve stale data from Redis for 5 minutes (TTL)

**Race condition sequence:**
```
Time  | Event
------+--------------------------------------------------------
T+0s  | PATCH /users/123 (write to PRIMARY)
T+0s  | Redis cache invalidated → DEL user:123
T+1s  | GET /users/123 (cache miss)
T+1s  | Read from REPLICA (still has old data, lag = 2s)
T+1s  | Re-populate Redis with stale data → SET user:123 (old)
T+1s  | Return stale data ❌
T+2s  | Replica catches up (new data arrives)
T+3s  | GET /users/123 (cache hit, but cached value is stale)
T+3s  | Return stale data ❌ (repeats for 5min until TTL expires)
```

### Step 6: Solution Design

**Option 1:** Read from PRIMARY on cache miss (simple)
```javascript
app.get('/users/:id', async (req, res) => {
  let user = await redis.get(`user:${req.params.id}`);
  if (!user) {
    user = await db.primary.users.findById(req.params.id); // ✅ PRIMARY
    await redis.set(`user:${req.params.id}`, user, 'EX', 300);
  }
  res.json(user);
});
```
**Pros:** Simple, guarantees consistency  
**Cons:** Increases primary DB load

**Option 2:** Write-through cache (populate on write)
```javascript
app.patch('/users/:id', async (req, res) => {
  const user = await db.users.update(req.params.id, req.body);
  // ✅ Populate cache immediately with fresh data
  await redis.set(`user:${req.params.id}`, user, 'EX', 300);
  res.json(user);
});
```
**Pros:** Read path unchanged, no extra primary load  
**Cons:** Must implement for all write paths (PATCH, POST, DELETE)

**Decision:** Implement BOTH
- Option 2 (write-through) for common case
- Option 1 (read from primary) as fallback for edge cases

---

## ✅ Solution Implemented

### Code Changes

```diff
// Write path: populate cache on update
app.patch('/users/:id', async (req, res) => {
  const user = await db.users.update(req.params.id, req.body);
  
- await redis.del(`user:${req.params.id}`);
+ // Write-through: populate cache with fresh data
+ await redis.set(`user:${req.params.id}`, JSON.stringify(user), 'EX', 300);
  
  res.json(user);
});

// Read path: fallback to primary if cache miss
app.get('/users/:id', async (req, res) => {
  let user = await redis.get(`user:${req.params.id}`);
  
  if (!user) {
-   user = await db.replica.users.findById(req.params.id);
+   // Read from primary to avoid replication lag
+   user = await db.primary.users.findById(req.params.id);
    await redis.set(`user:${req.params.id}`, JSON.stringify(user), 'EX', 300);
  } else {
    user = JSON.parse(user);
  }
  
  res.json(user);
});
```

### Testing

**Test 1: Rapid write-read**
```bash
# Write
curl -X PATCH https://api.example.com/users/123 \
  -d '{"name": "Updated Name"}'

# Immediate read (within 1 second)
curl https://api.example.com/users/123
# ✅ Returns "Updated Name" (was returning old name before fix)
```

**Test 2: Load test**
```bash
k6 run load-test.js
# 10K req/sec for 5 minutes
# Result: 0 stale data reports ✅
```

### Monitoring Added

```javascript
// Track cache hit rate
app.get('/users/:id', async (req, res) => {
  let user = await redis.get(`user:${req.params.id}`);
  
  if (!user) {
    metrics.increment('cache.miss');
    user = await db.primary.users.findById(req.params.id);
    // ...
  } else {
    metrics.increment('cache.hit');
    // ...
  }
});

// Alert if cache hit rate drops below 95%
// (indicates Redis issues or cache invalidation problems)
```

---

## 🎓 Lessons Learned

### Key Insight
**Cache + eventual consistency = potential staleness.** The bug required TWO conditions:
1. Cache invalidation (was working)
2. Read from replica (was creating race condition)

Removing either condition fixes the issue.

### Problem-Solving Pattern

**Hypothesis-Driven Investigation** > random debugging:
- ❌ **Random:** "Let's check logs... try increasing cache TTL... restart Redis..."
- ✅ **Structured:** Rank hypotheses by likelihood → test highest-probability first → found in 30 minutes

### Root Cause Template

Use **5 Whys** technique:
1. **Why stale data?** → Redis cached it
2. **Why cached stale?** → Read from replica on cache miss
3. **Why read from replica?** → Code configured to use replica for reads (load distribution)
4. **Why replica has old data?** → Replication lag (2-5 seconds, normal)
5. **Why is lag a problem?** → Cache invalidation + immediate read = race condition

**Root cause:** Cache-aside pattern + read replica + replication lag = race condition window

### Architectural Lessons

**Cache patterns:**
- **Cache-aside** (read-through): Vulnerable to replication lag
- **Write-through**: More consistent, but must implement on all writes
- **Write-behind**: Complex, async

**Consistency vs. Performance:**
- Reading from replica = better performance, eventual consistency
- Reading from primary = worse performance, strong consistency
- Write-through cache = best of both (when implemented correctly)

### Documentation

Created incident post-mortem:

```markdown
## Post-Mortem: Stale User Data (2024-03-03)

**Impact:** 2% of requests returned stale data for 30-300 seconds
**Duration:** 2 weeks (undetected) + 4 hours (detection to fix)
**Root Cause:** Cache-aside + read replica + replication lag

**Timeline:**
- T+0: Cache invalidated on write
- T+1s: Read from replica (stale due to replication lag)
- T+1s: Re-populated cache with stale data
- T+300s: Cache expires, cycle repeats

**Fix:** Write-through cache + fallback to primary on miss

**Prevention:**
- [ ] Add staleness detector (compare cached vs. primary)
- [ ] Alert on cache hit rate drop
- [ ] Document cache consistency guarantees
```

### Applicability
Use this structured approach for:
- ✅ Any production incident (database, API, infrastructure)
- ✅ Performance regression debugging
- ✅ Flaky test investigation
- ✅ Customer-reported bugs (intermittent issues)

---

**Incident Date:** March 3, 2026  
**Resolution Time:** 4 hours (detection to deploy)  
**Investigator:** Senior Backend Engineer + SRE  
**Validation:** 48-hour monitoring post-fix

**Outcome:**
- ✅ **0 stale data reports** in 48 hours post-fix
- ✅ **Cache hit rate: 98%** (healthy)
- ✅ **Primary DB load increase: +5%** (acceptable)
- 📖 **Runbook created** for similar cache consistency issues
