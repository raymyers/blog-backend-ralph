# Conduit RealWorld — Agent Knowledge Base

## Project Overview
Full-stack RealWorld "Conduit" blog app. Gleam backend (Wisp/Mist), Lustre frontend (planned),
SQLite database, Hexagonal Architecture, Playwright E2E tests.

## Quick Commands
```bash
cd /workspace/project/conduit
gleam build                          # Compile (0 warnings expected)
gleam test                           # Run 92 unit/integration tests
ERL_FLAGS="-noinput" gleam run       # Start server (port 12000)
gleam format src/ test/              # Format code

cd /workspace/project/e2e
npx playwright test --reporter=line  # Run 14 E2E tests (server must be running)
```

## Server Startup
- Must use `ERL_FLAGS="-noinput"` when running in background (prevents BEAM TTY crash)
- Bind to 0.0.0.0:12000 for external access
- SQLite DB: `conduit.db` in project root (auto-created on startup)
- Use `sqlight.open("conduit.db")` not `sqlight.with_connection` (callback blocks mist)
- Foreign keys enabled via `PRAGMA foreign_keys = ON` in migrations

## Key Dependencies
- wisp 2.x + mist 6.x (requires gleam_erlang 1.x)
- gleam_json 2.x (uses `decode.field`/`decode.success` pattern, NOT old `into`/`parameter`)
- gleam_stdlib 0.70.0 (uses `result.try` NOT `result.then`)
- gleam_crypto 1.5.1 (hmac returns BitArray, base16_encode takes BitArray)

## Gleam Syntax Notes
- No local imports inside function bodies — all imports must be at module level
- `should.be_error(result)` returns the error value (not Nil); use `let _ = should.be_error(x)` in callbacks that must return Nil
- `with_db(fn(db) { ... })` callbacks must return `Nil`

## API Gotchas
- curl to `localhost` may hang on IPv6 — always use `127.0.0.1`
- SPA uses `history.pushState` routing (not hash-based) — URLs are `/login`, `/register`, etc.
- Auth token stored in `localStorage` under key `jwtToken`
- All 18 RealWorld API endpoints implemented and working

## Architecture (Current State)
```
src/conduit/
  conduit.gleam                 # Entry point
  domain/{types,errors,slug}.gleam  # Pure domain
  adapters/web/{router,json_codec}.gleam  # HTTP layer (~461 + 281 LOC)
  adapters/db/{migrations,queries}.gleam  # SQLite (~69 + 423 LOC, parameterized)
  adapters/crypto/{token,password}.gleam  # Auth (timing-safe)
  ports/                        # Empty (M5: extract ports)
  app/                          # Empty (M5: extract services)
```

## Test Infrastructure
```
conduit/test/  — 92 tests total
  conduit/domain/slug_test.gleam           # 6 slug tests
  conduit/adapters/crypto/token_test.gleam # 5 token tests
  conduit/adapters/crypto/password_test.gleam # 4 password tests
  conduit/adapters/web/json_codec_test.gleam  # 12 codec tests
  conduit/adapters/db/queries_test.gleam   # 65 DB integration tests (in-memory SQLite)

e2e/tests/  — 14 tests total
  conduit.spec.ts                          # Layout, auth, articles, tags, profile, comments, settings, favorites
```

## Playwright Notes
- Block external CDN resources (fonts.googleapis.com, ionicframework.com) via `page.route()` to prevent hangs
- Use `{ waitUntil: 'domcontentloaded' }` on `page.goto()` calls
- Inject auth via: `page.evaluate(t => localStorage.setItem("jwtToken", t), token)`
- Use `nav.navbar` (not `nav`) to avoid matching pagination `<nav>` element

## Security Hardening (Completed)
- All SQL queries use parameterized `?` placeholders (no string concatenation)
- Password verify uses `crypto.secure_compare` (timing-safe)
- Router delegates to `domain/slug.from_title()` (no duplicated logic)
- Zero compiler warnings

## Known Issues to Fix (Milestone 5a)
- Timestamps not ISO 8601 (need `T` separator and `Z` suffix)
- Error responses not fully spec-compliant (`{ "errors": { "field": ["msg"] } }`)
- No 409/403 status codes yet
- Password hashing uses SHA256 (should be Argon2/bcrypt for production)
- Article list includes `body` field (spec omits it in list view)
- No `offset`/`limit` query params (frontend uses page numbers)

## Test Data
```bash
# Register
curl -s -X POST http://127.0.0.1:12000/api/users \
  -H 'Content-Type: application/json' \
  -d '{"user":{"username":"test","email":"t@t.com","password":"pw123"}}'

# Login
curl -s -X POST http://127.0.0.1:12000/api/users/login \
  -H 'Content-Type: application/json' \
  -d '{"user":{"email":"t@t.com","password":"pw123"}}'
```
