---
name: testing
description: TDD workflow, behavior-driven test patterns, factory pattern, coverage verification, refactoring discipline, and mutation testing. Non-negotiable for all code changes.
---
# Testing

## TDD Workflow

**Non-negotiable**: no production code without a failing test.

```
RED     → Write failing test (describes expected behavior; fails for the right reason)
GREEN   → Write minimum code to pass (no extras, no premature optimization)
REFACTOR → Improve structure only if it adds value; all tests still pass
```

Commit on green — after GREEN, after REFACTOR, or both. Any point where all tests pass is a valid commit.

Commit history should show RED → GREEN → REFACTOR progression:
```
test: add failing test for user authentication
feat: implement user authentication to pass test
refactor: extract validation logic
```

---

## Test Behavior, Not Implementation

Test through public APIs only. Never test private methods, internal state, or implementation details.

```typescript
// ✅ Tests WHAT — survives refactors
it('rejects negative amounts', () => {
  const result = processPayment(getMockPayment({ amount: -100 }));
  expect(result.success).toBe(false);
  expect(result.error).toContain('Amount must be positive');
});
```

**No 1:1 file mapping** between test files and implementation files. Test files describe behavior (`process-payment.test.ts`), not mirror implementation files (`payment-validator.test.ts`).

---

## Factory Pattern

```typescript
// Always: complete objects · validate with real schema · Partial overrides · no let/beforeEach
const getMockUser = (overrides?: Partial<User>): User =>
  UserSchema.parse({        // use the real schema — never redefine it here
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    ...overrides,
  });

// Compose for nested objects
const getMockOrder = (overrides?: Partial<Order>): Order =>
  OrderSchema.parse({ id: 'order-1', items: [getMockItem()], customer: getMockCustomer(), ...overrides });
```

**Rules**:
- Return complete objects with sensible defaults (never incomplete/partial)
- Validate with the real schema — never redefine it in tests
- `Partial<T>` for type-safe overrides
- One factory call per test — no shared mutable state between tests
- ❌ `let user: User; beforeEach(() => { user = {...} })` — mutation between tests

---

## Coverage

100% required: lines, statements, branches, functions. No exceptions without documented approval.

**Verify yourself** — never trust a claim. Run coverage and confirm all four metrics (lines, statements, branches, functions) show 100%.

When coverage drops, ask: *"What business behavior am I not testing?"* — not *"What line am I missing?"*

**Coverage theater** (100% lines, 0% actual protection):
- ❌ Mock the function being tested
- ❌ Assert only that a function was called, not what it returned
- ❌ Test trivial getters/setters
- ❌ Only test the happy path — no branches, no edge cases

**Exception process**: document current metrics, explain why 100% is unachievable, identify where coverage will come from (integration/E2E), get explicit approval, document in `AGENTS.md`.

---

## Refactoring

Assess after every GREEN — only refactor if it adds value.

| Priority | Action | Examples |
|---|---|---|
| Critical | Fix now | Mutable state, knowledge duplication, >3 levels nesting |
| High | This session | Magic numbers, unclear names, >30-line functions |
| Nice | Later | Minor naming, single-use helpers |
| Skip | Leave it | Already clean |

**DRY = knowledge, not code.** Abstract when concepts would change together. Keep separate when they'd evolve independently.

**No speculative code.** Every line must have a failing test that demanded it. Delete "just in case" logic — if behavior is needed, write the test first.

**When not to refactor**: code works correctly, no test demands the change, would change behavior, premature optimization.

---

## Mutation Testing

Coverage measures execution. Mutation testing measures **detection** — whether tests would catch a real bug introduced here.

A **surviving mutant** = a bug your tests would not catch.

**Process**: for each changed function, mentally apply these operators and ask *"if I changed this, would a test fail?"*

| Type | Mutations | What your test must verify |
|---|---|---|
| Arithmetic | `+↔-`, `*↔/`, `%↔*` | Use non-identity values (not 0 or 1) |
| Conditional | `>=↔>`, `<=↔<`, `>↔<=` | Test the exact boundary value |
| Logical | `&&↔\|\|` | Test where one operand is true, the other false |
| Equality | `===↔!==` | Both equal and not-equal cases |
| Boolean | `true↔false`, `!a↔a` | Both true and false outcomes |
| Method | `some↔every`, `startsWith↔endsWith`, `min↔max` | Both sides of the distinction |
| Block | `{ code }↔{}` | Side effects and return values explicitly asserted |
| Array literal | `[1,2,3]↔[]` | Non-empty array behavior |

**Red flags** (likely surviving mutants):
- Only the happy path tested
- Identity values in assertions: `0`, `1`, `""`, `[]`, `true && true`
- Only verifying a function was called, not what it returned
- Boundary not tested at the exact value

**Strengthening patterns:**
```typescript
// ❌ 10 * 1 = 10 / 1 — can't distinguish * from /
expect(calculateTotal(10, 1)).toBe(10);
// ✅
expect(calculateTotal(10, 3)).toBe(30);

// ❌ true || true = true && true
expect(canAccess(true, true)).toBe(true);
// ✅ test each branch independently
expect(canAccess(true,  false)).toBe(true);
expect(canAccess(false, true )).toBe(true);
expect(canAccess(false, false)).toBe(false);

// ❌ boundary not at exact value
expect(isAdult(17)).toBe(false);
expect(isAdult(25)).toBe(true);
// ✅
expect(isAdult(17)).toBe(false);
expect(isAdult(18)).toBe(true);  // at boundary — kills >= vs > mutation
expect(isAdult(19)).toBe(true);
```

---

## Anti-Patterns

- ❌ Writing production code without a failing test
- ❌ Testing implementation details (spies on internal methods)
- ❌ Mocking the function being tested
- ❌ `let`/`beforeEach` for test data
- ❌ Redefining schemas in test files
- ❌ Incomplete factory objects
- ❌ Trusting coverage claims without running verification yourself
- ❌ Speculative code (untested "just in case" paths)

---

## Checklist

- [ ] Every production code line has a failing test that demanded it
- [ ] Tests verify behavior through public API (not implementation details)
- [ ] No mocks of the function under test
- [ ] Factory functions return complete objects validated with the real schema
- [ ] No `let`/`beforeEach` for test data — factory per test
- [ ] 100% coverage verified (or exception documented and approved)
- [ ] Commits made on green (after GREEN, after REFACTOR, or both)
- [ ] Refactoring assessed; applied only if it adds value
- [ ] No speculative code
- [ ] Commit history shows RED → GREEN → REFACTOR
- [ ] For each changed function: operator mutations would be caught by a test
- [ ] Boundary values tested at the exact boundary (not just above/below)
- [ ] Both branches of `&&`/`||` tested with one side true, one false
- [ ] Non-identity values used in assertions (not `0`, `1`, `""`, `[]`)
