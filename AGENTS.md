# AGENTS.md

## Project Context
This is a Python FastAPI backend for the RealWorld Conduit API.

## Skills

### Process
The core workflow for incremental planning and development.
Reference: [agent-quality-skills/process/SKILL.md](https://github.com/raymyers/agent-quality-skills/blob/main/process/SKILL.md)

Key points:
- Work in small, known-good increments (single sentence, single commit)
- Plan files in `plans/` directory
- Commit on green
- Document gotchas and learnings
- CI debugging with hypothesis-first approach

### Architecture
Hexagonal and DDD are **ON** for this project.
Reference: [agent-quality-skills/architecture/SKILL.md](https://raw.githubusercontent.com/raymyers/agent-quality-skills/refs/heads/main/architecture/SKILL.md)

Key points:
- Functional style (immutability, pure functions, composition)
- TypeScript-like patterns adapted to Python
- DDD: Start with ubiquitous language and value objects
- Hexagonal: Dependencies point inward, adapters → ports → domain
- Repository pattern for data access

### Testing
TDD workflow is non-negotiable.
Reference: [agent-quality-skills/testing/SKILL.md](https://github.com/raymyers/agent-quality-skills/blob/main/testing/SKILL.md)

Key points:
- RED → GREEN → REFACTOR workflow
- Test behavior, not implementation
- Factory pattern with complete objects
- 100% coverage required
- Commit on green

## Current Plan
See [docs/plans/BACKEND.md](docs/plans/BACKEND.md) for the implementation roadmap.

## Status (python-fastapi-3)
**All 13 Hurl test files pass — 149/149 requests.** Branch `python-fastapi-3` is complete.

## Key Gotchas & Lessons Learned

### Dependency Versions
- **bcrypt**: Must be `<5` — bcrypt 5.x breaks passlib `CryptContext`. Pin `bcrypt<5` in `pyproject.toml`.
- **hurl**: Tests use `isList` predicate which requires hurl **7.x** (not 6.x). Install from GitHub releases.

### RealWorld API Conventions
- **Auth header**: `Authorization: Token <jwt>` (NOT `Bearer`). Use custom `Request`-based extraction, not FastAPI's `HTTPBearer`.
- **Error format**: Always `{"errors": {"field": ["message"]}}` — never `{"detail": ...}`. Register both `RequestValidationError` and `HTTPException` handlers in `main.py` to unwrap to this format.
- **Validation messages**: Empty/null fields → `"can't be blank"`. Duplicates → `"has already been taken"`. Bad credentials → `{"errors": {"credentials": ["invalid"]}}`. Missing token → `{"errors": {"token": ["is missing"]}}`.
- **HTTP status codes**: 409 for duplicate email/username (not 422). 403 for forbidden. `{"errors": {"article": ["forbidden"]}}` pattern.
- **articlesCount**: Must be the TOTAL count matching the filter, NOT the count of paginated results. Add separate `count_*` queries without `LIMIT`/`OFFSET`.
- **camelCase responses**: All article/comment fields must be camelCase: `tagList`, `createdAt`, `updatedAt`, `favoritesCount`, `articlesCount`. Use camelCase field names directly in Pydantic models.
- **Nullable bio/image**: Use `model_fields_set` to distinguish "field not provided" vs "field explicitly set to null". null/empty bio/image normalizes to DB null. null/empty email/username must be rejected with 422.
- **tagList null**: `PUT /api/articles/:slug` with `tagList: null` must return 422.

### FastAPI Patterns
- **Route ordering**: Declare `GET /api/articles/feed` BEFORE `GET /api/articles/{slug}` to prevent route shadowing.
- **Manual model instantiation**: When you call `MySchema(**data)` inside an endpoint (not as a FastAPI parameter), Pydantic raises `ValidationError` (not `RequestValidationError`). Must wrap in `try/except` and raise `HTTPException` with the correct format.
- **Session management**: Never create a second `Session` inside a service that already runs within a session-scoped dependency — SQLite locks. Use `self.session` everywhere.

### Testing Workflow
- Run tests: `HOST=http://localhost:3000 bash realworld/specs/api/run-api-tests-hurl.sh realworld/specs/api/hurl/*.hurl`
- Server: `python -m uvicorn app.main:app --host 0.0.0.0 --port 3000`
- Fresh DB: `rm -f data.db` before test runs to avoid state pollution between test runs.
