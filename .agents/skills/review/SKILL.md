---
name: review
description: PR review and test suite quality scoring. Covers TDD compliance, code quality checks across five categories, and Farley Score for deep test suite analysis.
---
# Review

## PR Review

Five categories. For testing quality, TypeScript, and functional patterns the rules live in the `testing` and `architecture` skills — the entries below are the violations most likely to slip through in a PR.

**Severity**:
- 🔴 Must fix before merge
- ⚠️ Should fix; discuss if not
- 💡 Nice to have

**Output format**:
```
## PR Review: #[number] — [title]

| Category | Status | Issues |
|---|---|---|
| TDD Compliance      | ✅/❌ | n |
| Testing Quality     | ✅/❌ | n |
| TypeScript          | ✅/❌ | n |
| Functional Patterns | ✅/❌ | n |
| General Quality     | ✅/❌ | n |

**Recommendation**: APPROVE / REQUEST CHANGES

🔴 [Category]: [issue] — `file.ts:line` — [fix]
⚠️ [Category]: [issue] — [suggestion]
💡 [suggestion]

✅ [what's good]
```

### TDD Compliance
Every production file changed must have a corresponding test change.
- ❌ New or modified behaviour with no test update
- ❌ Tests that appear written after the fact (covering implementation detail rather than behaviour)

### Testing Quality
See `testing` skill. Key violations:
- ❌ Spying on internal methods
- ❌ `let`/`beforeEach` for test data
- ❌ Test names reference implementation ("should call X")
- ❌ 1:1 file mapping (test mirrors implementation file)

### TypeScript
See `architecture` skill. Key violations:
- ❌ `any` — no exceptions
- ❌ `as Type` without a justifying comment
- ❌ `interface` for data structures (use `type`)
- ❌ Missing `readonly`; `@ts-ignore` without explanation

### Functional Patterns
See `architecture` skill. Key violations:
- ❌ `.push()`, `.splice()`, direct property assignment
- ❌ Nested `if/else` instead of early returns
- ❌ `for`/`while` loops where array methods apply
- ❌ Inline comments (rename or extract instead)

### General Quality
- ❌ `console.log` or debug statements left in
- ❌ TODO comments without a linked issue
- ❌ Hardcoded secrets or credentials
- ❌ PR not summarisable in 1–3 sentences
- ❌ Changes outside the stated scope of the PR

---

## Farley Score

For deep test suite analysis. Score each property 1–10:

**Farley Score** = `(U×1.5 + M×1.5 + R×1.25 + A + N + G + F×0.75 + T) / 9`

| # | Property | Weight | Key question |
|---|---|---|---|
| U | Understandable | 1.5× | Does this read like a specification? |
| M | Maintainable | 1.5× | Do implementation changes break these tests? |
| R | Repeatable | 1.25× | Same result every time, anywhere? |
| A | Atomic | 1× | Completely isolated; no shared state; parallelizable? |
| N | Necessary | 1× | Does every test add unique value? |
| G | Granular | 1× | Does each test assert exactly one thing? |
| F | Fast | 0.75× | Milliseconds, not seconds? |
| T | First (TDD) | 1× | Evidence of test-first approach? |

**Score bands**: <4.5 critical · 4.5–6.0 fair · 6.0–7.5 good · 7.5–9.0 excellent · 9.0+ exemplary

**Output format**:
```
## Farley Review: [File/Suite Name]

| Property | Score | Evidence |
|---|---|---|
| Understandable | X/10 | ... |
...

### Farley Score: X.X/10 [Band]

### Top Recommendations
1. [Highest-impact improvement]
2. ...
```

Reference: https://www.linkedin.com/pulse/tdd-properties-good-tests-dave-farley-iexge/

---

## Checklist

**PR Review**
- [ ] Every production change has a corresponding test change
- [ ] No `any`, no unjustified assertions, no data mutation
- [ ] No debug statements, TODO comments, or out-of-scope changes
- [ ] PR summarisable in 1–3 sentences

**Farley Score**
- [ ] Each property scored with specific evidence from the code
- [ ] Score calculated and band identified
- [ ] Top recommendations prioritised by impact
