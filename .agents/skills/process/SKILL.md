---
name: process
description: Development workflow. Covers incremental planning, plan files, PR discipline, documentation practices (gotchas, learnings), and CI debugging.
---
# Process

## Incremental Planning

All work in **small, known-good increments**. Each step must:
- Leave all tests passing and be independently deployable
- Fit in a single commit, describable in one sentence
- Have clear done criteria

**Too big**: takes more than one session, requires multiple commits, has multiple "and"s in the description, unclear how to test it.

**If you can't describe a step in one sentence, break it down further.**

---

## Plan Files

Plans live in `plans/` at the project root. Each is a self-contained file named descriptively (e.g., `plans/gift-tracking.md`). When planning, prefer the simplest high-quality answer to the request - avoid embellishing on the requirements.

```markdown
# Plan: [Feature Name]
**Branch**: feat/feature-name
**Status**: Active

## Goal
[One sentence]

## Acceptance Criteria
- [ ] ...

## Steps
### Step 1: [One sentence]
**Test**: What failing test will we write?
**Implementation**: What code will we write?
**Done when**: How do we know it's complete?

## Pre-PR Quality Gate
- Mutation testing (load `testing` skill)
- Typecheck and lint pass
```

Delete the plan file when complete. When changing the plan, note what changed and why in a changes section.

---

## Commits

Commit on green — any point where all tests pass is a valid commit. Verify static analysis passes before committing. Doc and plan changes should also be commited immediately.

---

## Documentation

After significant work, ask: *"What do I wish I'd known at the start?"*

Document if it would: save future developers meaningful time, prevent a class of bugs, reveal non-obvious behavior or constraints, capture architectural rationale, or identify effective/problematic patterns.

**Gotcha format**:
```markdown
#### Gotcha: [Descriptive Title]
**Context**: When this occurs
**Issue**: What goes wrong
**Solution**: How to handle it
```

Keep `AGENTS.md` (or equivalent) current when introducing meaningful changes.

---

## CI Debugging

**Hypothesis-first**: list at least 3 possible root causes before investigating. Tackle them systematically.

**Reproduce locally** with the exact failing command before pushing any fix. If it passes locally, the environment delta is the bug.

**Environment delta — check all of these**:

| Factor | Check |
|---|---|
| Runtime version | CI config vs `node -v` locally |
| OS | Linux CI vs macOS local |
| Dependencies | `npm ci` (fresh install) vs cached `node_modules` |
| Env vars | CI secrets/config vs local `.env` |
| Parallelism | CI may run tests differently |
| Network | CI may block external access |
| File system | Case sensitivity: Linux (sensitive) vs macOS (insensitive) |

**Read the full error output from the top** — not just the last line. Stack traces and earlier warnings often contain the real cause.

**Anti-patterns**:
- ❌ Adding retries or sleeps — hides race conditions; fix the root cause
- ❌ Re-running without investigating — masks real issues
- ❌ Pushing speculative fixes — wastes CI cycles; reproduce locally first
- ❌ Fixing symptoms — the problem will recur

**Flakiness requires evidence**: multiple independent runs in identical environments showing different results, *and* an identified non-deterministic source. Without both, treat every failure as a real bug.

---

## Checklist

- [ ] Work broken into single-sentence, single-commit steps
- [ ] Plan file created in `plans/`, reviewed and approved before starting
- [ ] PRs are the smallest independently mergeable units
- [ ] CI failures approached with 3+ hypotheses before investigating
- [ ] Failure reproduced locally with exact command before pushing a fix
- [ ] Root cause fixed (not symptoms, not retries)
- [ ] Gotchas and learnings documented after significant work
- [ ] `AGENTS.md` updated if meaningful changes were introduced
