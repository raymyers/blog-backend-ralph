# Conduit RealWorld -- Agent Knowledge Base

## Project Overview
Full-stack RealWorld "Conduit" blog app. Gleam backend (Wisp/Mist), Lustre frontend (planned),
SQLite database, Hexagonal Architecture, Playwright E2E tests.

## Quick Commands
```bash
cd /workspace/project/conduit
gleam build                          # Compile
gleam test                           # Run tests
ERL_FLAGS="-noinput" gleam run       # Start server (port 12000)
gleam format src/                    # Format code
```

## Server Startup
- Must use `ERL_FLAGS="-noinput"` when running in background (prevents BEAM TTY crash)
- Bind to 0.0.0.0:12000 for external access
- SQLite DB: `conduit.db` in project root (auto-created on startup)
- Use `sqlight.open("conduit.db")` not `sqlight.with_connection` (callback blocks mist)

## Key Dependencies
- wisp 2.x + mist 6.x (requires gleam_erlang 1.x)
- gleam_json 2.x (uses `decode.field`/`decode.success` pattern, NOT old `into`/`parameter`)
- gleam_stdlib 0.70.0 (uses `result.try` NOT `result.then`)
- gleam_crypto 1.5.1 (hmac returns BitArray, base16_encode takes BitArray)

## API Gotchas
- curl to `localhost` may hang on IPv6 -- always use `127.0.0.1`
- POST requests to mist/wisp work fine; earlier issues were IPv6-related
- All 18 RealWorld API endpoints implemented and working

## Architecture (Current State)
```
src/conduit/
  conduit.gleam                 # Entry point
  domain/{types,errors,slug}.gleam  # Pure domain
  adapters/web/{router,json_codec}.gleam  # HTTP layer (~485 + 281 LOC)
  adapters/db/{migrations,queries}.gleam  # SQLite (~67 + 403 LOC)
  adapters/crypto/{token,password}.gleam  # Auth
  ports/                        # Empty (M5: extract ports)
  app/                          # Empty (M5: extract services)
```

## Known Issues to Fix
- Timestamps not ISO 8601 (need `T` separator and `Z` suffix)
- Error responses not fully spec-compliant
- No 409/403 status codes yet
- Password hashing uses SHA256 (should be Argon2/bcrypt)
- Article list includes `body` (spec omits it)

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
