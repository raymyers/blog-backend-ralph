# AGENTS.md

## Process

**Process is the primary expectation.** Before writing any code, read `.agents/skills/process/SKILL.md`.

All work moves in small, known-good increments — one commit, one sentence, all tests green. Plans live in `docs/plans/`. Document gotchas after significant work.

## Skills

- [process](.agents/skills/process/SKILL.md) — always; governs how all work is done
- [testing](.agents/skills/testing/SKILL.md) — any code change; TDD is non-negotiable
- [architecture](.agents/skills/architecture/SKILL.md) — design decisions, new modules, refactoring
- [review](.agents/skills/review/SKILL.md) — PR review or test suite quality assessment

---

## Project: Python FastAPI RealWorld Backend

**Stack**: Python 3.12, FastAPI, SQLModel (SQLite), passlib/bcrypt, python-jose JWT, uv

**Architecture**: Hexagonal — `domain/` → `ports/` → `adapters/` + `use_cases/` → `routes/`

### Status (python-fastapi-4)

**All 13 Hurl test files pass — 149/149 requests.** Branch `python-fastapi-4` is complete.

### Running the server

```bash
rm -f data.db
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000
```

### Running tests

Unit tests:
```bash
uv run pytest tests/ -v
```

Integration tests (requires hurl 7.x at `~/hurl`):
```bash
PATH="$HOME:$PATH" HOST=http://localhost:3000 bash realworld/specs/api/run-api-tests-hurl.sh realworld/specs/api/hurl/*.hurl
```

Always restart the server with a fresh `data.db` before running the full suite — tests share state.

### Key Gotchas

#### Gotcha: bcrypt version
**Context**: Installing passlib with bcrypt  
**Issue**: bcrypt 5.x breaks passlib `CryptContext`  
**Solution**: Pin `bcrypt<5` in `pyproject.toml`

#### Gotcha: Authorization header format
**Context**: RealWorld API auth  
**Issue**: Header is `Authorization: Token <jwt>` not `Bearer`  
**Solution**: Custom extraction function; check for both `"Token "` and `"Bearer "` prefixes

#### Gotcha: Error response shape
**Context**: All API errors  
**Issue**: Must return `{"errors": {"field": ["message"]}}`, not FastAPI's default `{"detail": ...}`  
**Solution**: Register `RequestValidationError`, `HTTPException`, and `PydanticValidationError` handlers in `main.py`

#### Gotcha: Route ordering — /feed vs /{slug}
**Context**: `GET /api/articles/feed` and `GET /api/articles/{slug}`  
**Issue**: FastAPI matches `{slug}` before `/feed` if declared first  
**Solution**: Declare `/feed` route before `/{slug}` in the same router

#### Gotcha: articlesCount is total, not page count
**Context**: `GET /api/articles` and `GET /api/articles/feed`  
**Issue**: `articlesCount` must be the total matching count, not `len(page)`  
**Solution**: Run separate `count_*` queries without LIMIT/OFFSET

#### Gotcha: hurl version
**Context**: Running API test suite  
**Issue**: `isList` predicate requires hurl 7.x (not 6.x)  
**Solution**: Install from GitHub releases: https://github.com/Orange-OpenSource/hurl/releases

#### Gotcha: setuptools package discovery
**Context**: `uv sync` with both `app/` and `realworld/` subdirectories  
**Issue**: setuptools finds multiple top-level packages and refuses to build  
**Solution**: Add `[tool.setuptools.packages.find] include = ["app*"]` to `pyproject.toml`
