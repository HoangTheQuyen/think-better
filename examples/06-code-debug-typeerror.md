# Use Case 06: Debugging a TypeError After a Deploy

**Problem:** Checkout crashes for customers who pay with a gift card

**Type:** Code change (`debug`)
**Skill Used:** code-solving (`/code.debug`)
**Duration:** 40 minutes
**Outcome:** ✅ Root cause fixed, regression test added, PR merged

---

## 📋 Context

- Node.js shop, Express API, tests with Vitest
- Since yesterday's deploy, `POST /checkout/pay` returns 500 for some orders
- The logs show one stack trace over and over

## 🔬 Process

### Step 1: Ask for a plan

```bash
think-better init --ai claude --skill code-solving
```

In Claude Code, paste the whole error, not a summary:

```
/code.debug Checkout throws after yesterday's deploy when paying with a gift card:
TypeError: Cannot read properties of undefined (reading 'id')
    at orderTotal (src/checkout/total.js:10:33)
    at payHandler (src/checkout/handler.js:4:17)
    at Layer.handle (node_modules/express/lib/router/layer.js:95:5)
Repro: add a gift card, then pay. Save step-by-step.
```

The command runs `search.py --stdin --plan --type debug`. The quotes and parentheses in the
error are passed on stdin, so the shell never touches them. The plan begins with what the
script found in the project (this is the actual output):

```markdown
### Context from the project

Found in the code and git history, not guessed. Read these first in Step 2.
**Where the error points** (project frames only):
- `src/checkout/total.js:10`: `const discount = cart.coupon.id ? cart.coupon.amount : 0;`
- `src/checkout/handler.js:4`: `const total = orderTotal(req.session.cart);`

### Known error: TypeError: Cannot read properties of undefined/null (JavaScript)

Code read a property of a value that is undefined or null.
- **Likely causes:** Data not loaded yet (async state, first render); an API returned a
  different shape or an error body; a wrong key or index; an optional field assumed present.
- **Check first:** Log the object one level up from the property in the message; ...
- **Fix at the root:** Handle the loading and empty states explicitly; validate the response
  shape at the boundary; use optional chaining only where absence is valid.
```

The Express frame is dropped because it is library code. **Project checks** lists
`npm run test`, `npm run lint` and `npm run build` from `package.json`, so Step 6 knows what to run.
"Save step-by-step" creates `coding-plans/checkout-typeerror/` with `00-OVERVIEW.md` and one
file per step, and the four likely causes are already filled into the hypothesis table in `04-LOG.md`.

### Step 2: Work through the gates

| Step | What the AI did | Evidence for the gate |
|------|-----------------|-----------------------|
| 1. Define | Wrote `pays with a gift card and no coupon` in `test/total.test.js` | `npm run test -- test/total.test.js` fails with the same TypeError |
| 2. Decompose | Traced `payHandler` → `orderTotal` → `applyGiftCards`; read the deploy's commits on these files | Change map: `cart.coupon` comes from the session cart, which the deploy stopped filling with `{}` |
| 3–4. Prioritize & Plan | One slice: treat a missing coupon as "no discount" in `orderTotal` | Task list: test from Step 1, rollback = revert one commit |
| 5. Execute | Hypothesis 4 ("an optional field assumed present") confirmed; hypotheses 1–3 ruled out in the log | `04-LOG.md`, one green commit |
| 6. Verify | Step 1 test passes; full suite, lint, build | `npm run test` 48 passed, `npm run lint` clean, `npm run build` OK |
| 7. Communicate | PR description from `06-PR.md` | Root cause, fix, regression test, risk |

After each gate the AI ran `search.py --done <step> -p checkout-typeerror` to tick it in
`00-OVERVIEW.md`. Had the session ended halfway, `/code.resume the checkout bug` in a new
session would list the ticked steps and continue at the first open gate.

### Step 3: The fix

```diff
 export function orderTotal(cart) {
   const subtotal = cart.items.reduce((s, i) => s + i.price * i.qty, 0);
-  const discount = cart.coupon.id ? cart.coupon.amount : 0;
+  // A cart has no coupon unless one was applied (session carts omit it since #212).
+  const discount = cart.coupon ? cart.coupon.amount : 0;
   return applyGiftCards(cart, subtotal - discount);
 }
```

The AI did not wrap the call in `try/catch`, and it did not add `?.` everywhere. The plan's
anti-patterns list both ("catching and swallowing the exception"; "optional chaining only
where absence is valid").

## 📊 Results

- Fixed in 40 minutes. The first test written failed for the same reason as production.
- The plan's "search the codebase for the same faulty pattern" step found the same
  `cart.coupon.id` read in the order-confirmation email. It was fixed in the same PR, with its own test.

## 💡 Key Lessons

1. **Paste the full stack trace.** It is what lets the plan point at `total.js:10` instead of a guess.
2. **Known-error causes are hypotheses.** Here it was cause 4, and the log records why 1–3 were ruled out.
3. **A failing test first is the gate.** Without it, "fixed" would have meant "no longer crashes on my machine".

---

**Related:** [05 - API Race Condition](05-debugging-race-condition.md) (problem-solving-pro) ·
[User Guide: code-solving](../USER-GUIDE.md#skill-3-code-solving)
