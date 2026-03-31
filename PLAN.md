# RealWorld Conduit — Full-Stack Gleam Implementation Plan

> A Medium.com clone ("Conduit") built in **Gleam** (backend: Wisp/Mist, frontend: Lustre SPA),
> following **Hexagonal Architecture**, validated with **Playwright** E2E tests.
>
> Spec: https://github.com/realworld-apps/realworld
> OpenAPI: https://github.com/realworld-apps/realworld/blob/main/specs/api/openapi.yml

---

## Current State (as of Milestone 4 — Audit & Testing)

The backend API is **fully functional** — all 18 RealWorld endpoints respond correctly.
A vanilla JS SPA frontend serves as the working presentation layer. Security hardening
and comprehensive testing have been completed.

**Test suite status: ✅ 106 tests passing**
- 92 Gleam unit/integration tests (slug, token, password, json_codec, DB queries)
- 14 Playwright E2E tests (layout, auth, articles, tags, profile, comments, settings, favorites)

**Working features (tested end-to-end):**
- User registration, login, get/update current user
- Article CRUD with slug generation, tag associations
- Comments: create, list, delete
- Favorites: favorite/unfavorite articles
- Profiles: get profile, follow/unfollow
- Feed: articles from followed users
- Filters: by tag, author, favorited
- Tags: list all tags
- Static SPA serving with client-side routing (history.pushState)

**Security hardening completed:**
- All SQL queries use parameterized `?` placeholders (no string concatenation)
- Timing-safe password comparison via `crypto.secure_compare`
- Router uses domain `slug.from_title()` (no duplicated logic)
- Zero compiler warnings

**Known gaps vs. OpenAPI spec:**
- Timestamps use `YYYY-MM-DD HH:mm:ss` instead of ISO 8601 `date-time` format
- Error responses need alignment with `{ "errors": { "field": ["msg"] } }` format
- Missing: 409 Conflict on duplicate username/email, 403 Forbidden on wrong owner
- Article list response includes `body` field (spec omits it in list view)
- `offset`/`limit` pagination params not yet wired (frontend uses page numbers)

---

## Architecture Overview

### Current Backend Structure (Pragmatic MVP)

```
conduit/src/conduit/
  conduit.gleam                       # Entrypoint — mist server on :12000
  domain/
    types.gleam                       # All domain types (User, Article, Comment, etc.)
    errors.gleam                      # AppError union type
    slug.gleam                        # Slug generation from title (with trim_dashes)
  adapters/
    web/
      router.gleam                    # Monolithic router — all 18 endpoints (~461 LOC)
      json_codec.gleam                # All JSON encode/decode (~281 LOC)
    db/
      migrations.gleam                # SQLite schema (7 tables, FK ON)
      queries.gleam                   # All SQL queries (~423 LOC, parameterized)
    crypto/
      token.gleam                     # HMAC-SHA256 token sign/verify
      password.gleam                  # SHA256 hash + timing-safe verify
  ports/                              # (empty — not yet extracted)
  app/                                # (empty — not yet extracted)
```

### Target Backend Structure (Hexagonal)

```
conduit/src/conduit/
  conduit.gleam                       # Wires adapters → services, starts server
  domain/
    user.gleam, article.gleam, comment.gleam, profile.gleam, tag.gleam
    errors.gleam                      # DomainError variants
    slug.gleam                        # Slug generation (pure)
  ports/
    user_repo.gleam                   # UserRepo record type
    article_repo.gleam                # ArticleRepo record type
    comment_repo.gleam                # CommentRepo record type
    tag_repo.gleam                    # TagRepo record type
    password_hasher.gleam             # PasswordHasher record (hash, verify)
    token_provider.gleam              # TokenProvider record (sign, verify)
  app/
    auth_service.gleam                # register, login
    user_service.gleam                # get_current_user, update_user
    article_service.gleam             # CRUD + list + feed + favorite
    comment_service.gleam             # create, list, delete
    profile_service.gleam             # get_profile, follow, unfollow
    tag_service.gleam                 # get_all_tags
  adapters/
    web/
      router.gleam                    # Route dispatch only
      middleware.gleam                # Auth extraction, CORS, logging
      handlers/                       # Per-resource handler modules
      json_codec.gleam                # JSON encode/decode
    db/
      migrations.gleam, user_repo_sqlite.gleam, article_repo_sqlite.gleam,
      comment_repo_sqlite.gleam, tag_repo_sqlite.gleam
    crypto/
      token.gleam, password.gleam
```

### Frontend Target (Lustre SPA)

```
conduit_ui/src/
  app.gleam                           # Lustre root (Model/Msg/update/view)
  router.gleam                        # Client-side routing (URL → Route)
  api/{auth,article,comment,profile,tag}_api.gleam
  model/{user,article,comment,session}.gleam
  pages/{home,login,register,settings,editor,article,profile}.gleam
  components/{navbar,footer,article_preview,tag_list,pagination,error_messages}.gleam
```

### Test Infrastructure

```
conduit/test/
  conduit_test.gleam                  # gleeunit main
  conduit/domain/
    slug_test.gleam                   # 6 tests: basic, special chars, unicode, empty, trim, unique
  conduit/adapters/crypto/
    token_test.gleam                  # 5 tests: sign/verify, tamper, format, different tokens
    password_test.gleam               # 4 tests: hash length, verify, wrong pw, distinct hashes
  conduit/adapters/web/
    json_codec_test.gleam             # 12 tests: decode/encode roundtrips for all request types
  conduit/adapters/db/
    queries_test.gleam                # 65 tests: full CRUD for users, articles, comments,
                                      #   favorites, follows, tags, feed (in-memory SQLite)

e2e/
  playwright.config.ts                # Chromium, base URL localhost:12000
  tests/
    helpers.ts                        # API helpers (registerUser, createArticle)
    conduit.spec.ts                   # 14 tests: layout, auth, articles, tags, profile,
                                      #   comments, settings, favorites
```

---

## Milestones

---

### Milestone 0 — Project Scaffolding & Dev Tooling ✅

> Set up the Gleam backend project, dependencies, and dev environment.

- [x] Initialize Gleam backend project (`conduit`) with `gleam new`
- [x] Add backend deps: wisp 2.x, mist 6.x, gleam_http, gleam_json 2.x, sqlight, birl, gleam_crypto, simplifile, gleam_erlang 1.x, gleam_otp
- [x] Resolve dependency version conflicts (gleam_erlang 1.x requires mist 6.x, wisp 2.x)
- [x] Set up static asset serving — backend serves SPA HTML + JS from `priv/static/`
- [x] Create Quint formal spec (`spec/conduit.qnt`) — types, state, actions, invariants
- [x] Smoke test: `gleam build` compiles, `gleam run` starts server on port 12000
- [ ] Initialize Lustre frontend project (`conduit_ui`) targeting JavaScript
- [ ] Add frontend deps: lustre, lustre_http, gleam_json, modem
- [ ] Set up Lustre dev build pipeline (gleam build → bundle JS → serve from backend)
- [ ] Create `Makefile` with commands: dev, build, test, e2e
- [x] Initialize Playwright project in `e2e/` with TypeScript config
- [x] Integrate RealWorld Conduit CSS theme
- [x] Write `AGENTS.md` with build commands and conventions

#### Assessment: Milestone 0
- [x] `gleam build` and `gleam run` succeed — server starts and responds
- [x] Playwright can launch browser and navigate to running app (14 E2E tests pass)
- [x] Project layout has `domain/`, `adapters/` directories
- [ ] Lustre frontend project compiles to JS and mounts in browser

---

### Milestone 1 — Domain Core & Formal Spec ✅

> Pure domain types, value objects, business rules. Zero I/O, maps 1:1 to Quint spec.

- [x] Define domain types — User, Article, Comment, Profile, NewUser, NewArticle, NewComment, UpdateUser, UpdateArticle in `domain/types.gleam`
- [x] Define domain error type — AppError (NotFound, Unauthorized, Forbidden, Validation, Conflict) in `domain/errors.gleam`
- [x] Implement slug generation — lowercase, hyphenated, alphanumeric, trimmed in `domain/slug.gleam`
- [x] Create Quint spec with full type definitions, state variables, actions, and invariants
- [ ] Split `domain/types.gleam` into per-resource files (user.gleam, article.gleam, comment.gleam, profile.gleam, tag.gleam)
- [ ] Add domain validation functions — email format, required fields, string length limits
- [x] Write unit tests for slug generation edge cases (unicode, empty, collisions, trim)
- [ ] Write unit tests for domain validation functions

#### Assessment: Milestone 1
- [x] Domain types cover all OpenAPI schema types (User, Profile, Article, Comment, Tag)
- [x] Slug generation produces URL-safe slugs from titles (6 tests)
- [x] `gleam test` — all domain unit tests pass
- [ ] Audit: domain modules import **nothing** from `adapters/`
- [ ] Domain types validate against Quint spec type definitions

---

### Milestone 2 — Database & Persistence Adapter ✅

> SQLite schema, migrations, and query implementations.

- [x] Design SQL schema: users, articles, tags, article_tags, comments, follows, favorites
- [x] Implement `adapters/db/migrations.gleam` — create all 7 tables with constraints
- [x] Enable `PRAGMA foreign_keys = ON` for ON DELETE CASCADE support
- [x] Implement `adapters/db/queries.gleam` — all CRUD operations (parameterized queries):
  - [x] Users: insert, find_by_email, find_by_id, find_by_username, update
  - [x] Articles: insert, find_by_slug, update, delete, list (global + feed + filters)
  - [x] Comments: insert, find_by_article, find_by_id, delete
  - [x] Tags: insert, find_by_article, list_all
  - [x] Favorites: insert, delete, check, count
  - [x] Follows: insert, delete, check
- [x] Write integration tests for each query function (65 tests with in-memory SQLite)
- [ ] Split `queries.gleam` into per-resource repo files
- [ ] Add `PRAGMA journal_mode=WAL` for concurrent read safety
- [ ] Add `offset`/`limit` support to article list queries

#### Assessment: Milestone 2
- [x] All 7 tables created on startup with foreign keys and indices
- [x] Basic CRUD for all resources works end-to-end via curl
- [x] Integration tests pass for all query functions (65 tests)
- [ ] Audit: queries import only from `domain/` — no web/HTTP imports

---

### Milestone 3 — Crypto Adapters & Authentication ✅

> Token signing/verification and password hashing.

- [x] Implement `adapters/crypto/token.gleam` — HMAC-SHA256 token: `user_id.signature`
- [x] Implement `adapters/crypto/password.gleam` — SHA256 hash + timing-safe verify
- [x] Token extraction from `Authorization: Token <value>` header in router
- [x] Auth middleware: required-auth vs optional-auth endpoint handling
- [x] Timing-safe password comparison via `crypto.secure_compare`
- [x] Write unit tests for token sign → verify round-trip (5 tests)
- [x] Write unit tests for password hash → verify round-trip (4 tests)
- [ ] Upgrade password hashing to Argon2 or bcrypt (SHA256 is not production-safe)
- [ ] Add token expiration (current tokens never expire)

#### Assessment: Milestone 3
- [x] Register → login → authenticate flow works end-to-end
- [x] Token verification correctly rejects invalid/tampered tokens (tested)
- [x] Audit: crypto modules are self-contained — no DB or HTTP imports ✅
- [x] Password hashing uses timing-safe comparison ✅

---

### Milestone 4 — HTTP API & Testing ✅

> Complete REST API + comprehensive test suites.

- [x] Implement router with all OpenAPI routes:
  - [x] `POST /api/users` — register (201)
  - [x] `POST /api/users/login` — login (200)
  - [x] `GET /api/user` — current user (200, auth required)
  - [x] `PUT /api/user` — update user (200, auth required)
  - [x] `GET /api/profiles/:username` — get profile (200)
  - [x] `POST /api/profiles/:username/follow` — follow (200, auth required)
  - [x] `DELETE /api/profiles/:username/follow` — unfollow (200, auth required)
  - [x] `GET /api/articles` — list articles with filters (200)
  - [x] `GET /api/articles/feed` — feed (200, auth required)
  - [x] `POST /api/articles` — create (201, auth required)
  - [x] `GET /api/articles/:slug` — get article (200)
  - [x] `PUT /api/articles/:slug` — update (200, auth required)
  - [x] `DELETE /api/articles/:slug` — delete (204, auth required)
  - [x] `POST /api/articles/:slug/comments` — add comment (201, auth required)
  - [x] `GET /api/articles/:slug/comments` — list comments (200)
  - [x] `DELETE /api/articles/:slug/comments/:id` — delete comment (204, auth required)
  - [x] `POST /api/articles/:slug/favorite` — favorite (200, auth required)
  - [x] `DELETE /api/articles/:slug/favorite` — unfavorite (200, auth required)
  - [x] `GET /api/tags` — list tags (200)
- [x] Implement JSON encode/decode for all request/response shapes (12 codec tests)
- [x] Implement CORS headers (`Access-Control-Allow-Origin: *`)
- [x] Wire entrypoint: conduit.gleam opens SQLite, runs migrations, starts mist on 0.0.0.0:12000
- [x] Security: all SQL queries use parameterized `?` placeholders
- [x] Security: router uses `domain/slug.from_title()` (no duplicated logic)
- [x] Write 14 Playwright E2E tests covering all major UI flows
- [ ] Fix timestamp format — use ISO 8601 date-time (`2026-03-31T17:20:48.000Z`)
- [ ] Fix error response format — align with `{ "errors": { "field": ["msg"] } }` spec
- [ ] Add 409 Conflict response for duplicate username/email on register
- [ ] Add 403 Forbidden for article/comment operations by non-owner
- [ ] Omit `body` field from article list responses (present only on single article)
- [ ] Add `offset`/`limit` query parameter handling
- [ ] Run official RealWorld Hurl API test suite — fix all failures

#### Assessment: Milestone 4
- [x] All 18 endpoints respond with correct JSON shapes (verified via curl and E2E)
- [x] Registration → article creation → comment → favorite → feed flow works end-to-end
- [x] 92 Gleam tests + 14 Playwright tests all pass ✅
- [ ] Official RealWorld Hurl test suite passes
- [ ] Audit: status codes match OpenAPI spec (200/201/204/401/403/404/409/422)

---

### Milestone 5 — Hexagonal Refactor (Ports & Services)

> Extract port interfaces and application services from the monolithic router/queries.
> Key architectural milestone — enforces dependency inversion.

- [ ] Define `ports/user_repo.gleam` — UserRepo record type with function fields
- [ ] Define `ports/article_repo.gleam` — ArticleRepo record type
- [ ] Define `ports/comment_repo.gleam` — CommentRepo record type
- [ ] Define `ports/tag_repo.gleam` — TagRepo record type
- [ ] Define `ports/password_hasher.gleam` — PasswordHasher record (hash, verify)
- [ ] Define `ports/token_provider.gleam` — TokenProvider record (sign, verify)
- [ ] Split `queries.gleam` into per-resource repo files — each returning a port record
- [ ] Implement `app/auth_service.gleam` — register, login
- [ ] Implement `app/user_service.gleam` — get_current_user, update_user
- [ ] Implement `app/profile_service.gleam` — get_profile, follow, unfollow
- [ ] Implement `app/article_service.gleam` — CRUD + list + feed + favorite/unfavorite
- [ ] Implement `app/comment_service.gleam` — create, list_by_article, delete
- [ ] Implement `app/tag_service.gleam` — get_all_tags
- [ ] Refactor `router.gleam` — thin dispatch layer calling service functions (no direct SQL)
- [ ] Update `conduit.gleam` — construct port records, inject into services, inject into router
- [ ] Write unit tests for services using in-memory stub repos (test doubles)
- [ ] Verify `gleam build` still compiles, all existing tests still pass

#### Assessment: Milestone 5
- [ ] **Dependency rule enforced:**
  - [ ] `domain/` imports nothing from `ports/`, `app/`, or `adapters/`
  - [ ] `ports/` imports only from `domain/`
  - [ ] `app/` imports from `domain/` and `ports/` — never `adapters/`
  - [ ] `adapters/web/` imports from `app/` and `domain/` — never `adapters/db/`
  - [ ] `adapters/db/` imports from `domain/` and `ports/` — never `adapters/web/`
- [ ] All service functions return `Result(T, DomainError)`
- [ ] Services are stateless — all deps passed as function params
- [ ] In-memory stub repos work — proving ports are truly abstract
- [ ] All existing API tests still pass after refactor (no regressions)
- [ ] 92 Gleam tests + 14 Playwright E2E tests still pass

---

### Milestone 5a — API Spec Compliance

> Fix remaining gaps between current API and the official OpenAPI spec.

- [ ] Fix timestamp format — use ISO 8601 date-time (`2026-03-31T17:20:48.000Z`)
- [ ] Fix error response format — align with `{ "errors": { "field": ["msg"] } }` format
- [ ] Add 409 Conflict response for duplicate username/email on register
- [ ] Add 403 Forbidden for article/comment operations by non-owner
- [ ] Omit `body` field from article list responses (present only on single article)
- [ ] Add `offset`/`limit` query parameter handling (replace page-based pagination)
- [ ] Ensure `articlesCount` included in multi-article responses
- [ ] Run official RealWorld Hurl API test suite — fix all failures
- [ ] Update Playwright E2E tests for any changed response shapes

#### Assessment: Milestone 5a
- [ ] Official RealWorld Hurl test suite passes
- [ ] All error responses match `{ "errors": { "field": ["msg"] } }` format
- [ ] Status codes match OpenAPI spec (200/201/204/401/403/404/409/422)
- [ ] All 92 Gleam + 14 Playwright tests still pass

---

### Milestone 6 — Lustre Frontend: Shell, Routing & Auth

> Replace vanilla JS with Gleam + Lustre SPA. Start with auth flows.

- [ ] Initialize `conduit_ui/` Gleam project targeting JavaScript
- [ ] Add dependencies: lustre, lustre_http, gleam_json, modem
- [ ] Implement `app.gleam` — top-level Lustre application (init, update, view)
- [ ] Implement `router.gleam` — URL → Route type for all pages
- [ ] Implement `model/session.gleam` — auth state (JWT in localStorage)
- [ ] Implement `components/navbar.gleam` — conditional nav links based on auth
- [ ] Implement `components/footer.gleam` — standard footer
- [ ] Implement `pages/login.gleam` — sign-in form with error display
- [ ] Implement `pages/register.gleam` — sign-up form
- [ ] Implement `pages/settings.gleam` — settings form + logout button
- [ ] Implement `api/auth_api.gleam` — register, login, get_user, update_user
- [ ] Implement `components/error_messages.gleam` — .error-messages ul
- [ ] Store JWT in localStorage under `jwtToken` key
- [ ] Set up build pipeline: compile Lustre → copy JS to conduit/priv/static/
- [ ] Update HTML shell to load Lustre-compiled JS instead of vanilla app.mjs
- [ ] Playwright: update auth tests for Lustre-rendered UI

#### Assessment: Milestone 6
- [ ] Playwright auth tests pass — full auth lifecycle
- [ ] Page modules are self-contained (own Msg, update, view)
- [ ] API modules return `Effect(Msg)` — no scattered JS interop
- [ ] CSS theme renders correctly
- [ ] All 92 Gleam + Playwright tests still pass

---

### Milestone 7 — Lustre Frontend: Home, Articles & Tags

> Home page feeds, article CRUD, tag sidebar, pagination.

- [ ] Implement `api/article_api.gleam` — list, get, create, update, delete
- [ ] Implement `api/tag_api.gleam` — get tags
- [ ] Implement `model/article.gleam` — Article, ArticleList frontend types
- [ ] Implement `pages/home.gleam` — Global Feed / Your Feed toggle, article list
- [ ] Implement `components/article_preview.gleam` — article card with meta
- [ ] Implement `components/tag_list.gleam` — sidebar tags
- [ ] Implement `components/pagination.gleam` — page buttons
- [ ] Implement tag filtering — click tag → filter feed
- [ ] Implement `pages/editor.gleam` — create/edit article form
- [ ] Implement `pages/article.gleam` — article detail with markdown body
- [ ] Implement favorite button toggle on article previews and detail
- [ ] Playwright: write `articles.spec.ts` — create, edit, delete, list, favorite
- [ ] Playwright: write `navigation.spec.ts` — feed tabs, tag filter, pagination

#### Assessment: Milestone 7
- [ ] Playwright `articles.spec.ts` and `navigation.spec.ts` pass
- [ ] Feed toggle correctly switches between global/following feeds
- [ ] Pagination renders correct page count and uses offset/limit
- [ ] Article editor supports both create and edit modes
- [ ] Components reused across pages (article_preview, tag_list, pagination)
- [ ] All Gleam + Playwright tests pass

---

### Milestone 8 — Lustre Frontend: Comments, Profiles & Social

> Complete social features — comments, profiles, follow system.

- [ ] Implement `api/comment_api.gleam` — create, list, delete comments
- [ ] Implement `api/profile_api.gleam` — get profile, follow, unfollow
- [ ] Implement comment section in `pages/article.gleam` — form + list
- [ ] Implement `pages/profile.gleam` — profile page with article tabs
- [ ] Implement "My Articles" / "Favorited Articles" tabs on profile page
- [ ] Implement follow/unfollow button on profile and article pages
- [ ] Implement default avatar when `image` is null
- [ ] Route `/profile/:username` shows authored, `/profile/:username/favorites` shows favorited
- [ ] Playwright: write `comments.spec.ts` — post, view, delete comment
- [ ] Playwright: write `profiles.spec.ts` — view profile, follow/unfollow, tabs

#### Assessment: Milestone 8
- [ ] Playwright `comments.spec.ts` and `profiles.spec.ts` pass
- [ ] Delete button only appears for comment author
- [ ] Follow/unfollow toggles correctly
- [ ] Profile reuses article_preview and pagination components
- [ ] All Gleam + Playwright tests pass

---

### Milestone 9 — Error Handling & Edge Cases

> Robust error handling, validation feedback, 404s, edge-case coverage.

- [ ] Implement client-side validation — required fields, email format
- [ ] Implement server-side validation error display — .error-messages from 422 responses
- [ ] Handle 401 responses globally — clear token, redirect to login
- [ ] Handle 404 — show "not found" UI for missing articles/profiles
- [ ] Handle network errors gracefully — display feedback to user
- [ ] Handle null bio/image fields per spec (nullable fields in JSON)
- [ ] Implement conflict error handling (409) — duplicate username/email on register
- [ ] Playwright: write `error-handling.spec.ts` — invalid login, duplicate register, validation errors

#### Assessment: Milestone 9
- [ ] Playwright `error-handling.spec.ts` passes
- [ ] All API error responses match `{ "errors": { ... } }` format
- [ ] Error handling is centralized — single `handle_api_error` function
- [ ] No unhandled promise rejections or Gleam panics in browser console
- [ ] All Gleam + Playwright tests pass

---

### Milestone 10 — Full E2E Suite & Official Spec Compliance

> Run complete official test suites, polish, verify full compliance.

- [ ] Run official RealWorld Hurl API test suite — fix any remaining failures
- [ ] Write smoke test Playwright spec — app loads, basic navigation works
- [ ] Verify all API response shapes match OpenAPI spec exactly
- [ ] Verify all frontend routes are navigable and render correctly
- [ ] Verify `localStorage.jwtToken` is set/cleared correctly
- [ ] Verify default avatar behavior for all avatar locations
- [ ] Verify button state conventions (favorite toggle, follow text toggle)
- [ ] Performance check — feed loads under 2s, no memory leaks in SPA
- [ ] Code quality: `gleam format` no changes, zero compiler warnings

#### Assessment: Milestone 10 — Final Compliance & Architecture Review
- [ ] **All** official Hurl API tests pass
- [ ] **All** Playwright E2E tests pass (auth, articles, comments, profiles, navigation, errors)
- [ ] Full Hexagonal Architecture audit:
  - [ ] `domain/` has zero imports from `adapters/`
  - [ ] `ports/` define abstract interfaces only
  - [ ] `app/` depends only on `domain/` and `ports/`
  - [ ] `adapters/web/` never imports `adapters/db/`
  - [ ] `adapters/db/` never imports `adapters/web/`
  - [ ] All adapters are injectable via function parameters
- [ ] Frontend modularity audit:
  - [ ] Each Lustre page module is independently testable
  - [ ] Shared components reused across pages
  - [ ] API layer is decoupled — swapping base URL is one-line change
  - [ ] Router is exhaustive — all routes handled
- [ ] Code quality: `gleam format` no changes, zero compiler warnings
- [ ] Test quality: no mocks in tests — all tests exercise real code paths

---

## API Endpoints Summary

| Method | Path | Auth | Status |
|--------|------|------|--------|
| POST | `/api/users` | No | 201 |
| POST | `/api/users/login` | No | 200 |
| GET | `/api/user` | Required | 200 |
| PUT | `/api/user` | Required | 200 |
| GET | `/api/profiles/:username` | Optional | 200 |
| POST | `/api/profiles/:username/follow` | Required | 200 |
| DELETE | `/api/profiles/:username/follow` | Required | 200 |
| GET | `/api/articles` | Optional | 200 |
| GET | `/api/articles/feed` | Required | 200 |
| POST | `/api/articles` | Required | 201 |
| GET | `/api/articles/:slug` | No | 200 |
| PUT | `/api/articles/:slug` | Required | 200 |
| DELETE | `/api/articles/:slug` | Required | 204 |
| POST | `/api/articles/:slug/comments` | Required | 201 |
| GET | `/api/articles/:slug/comments` | Optional | 200 |
| DELETE | `/api/articles/:slug/comments/:id` | Required | 204 |
| POST | `/api/articles/:slug/favorite` | Required | 200 |
| DELETE | `/api/articles/:slug/favorite` | Required | 200 |
| GET | `/api/tags` | No | 200 |

## Frontend Routes

| Route | Page | Auth |
|-------|------|------|
| `/` | Home -- Global Feed | No |
| `/?feed=following` | Home -- Your Feed | Required |
| `/login` | Sign In | No |
| `/register` | Sign Up | No |
| `/settings` | User Settings | Required |
| `/editor` | New Article | Required |
| `/editor/:slug` | Edit Article | Required |
| `/article/:slug` | Article Detail | No |
| `/profile/:username` | User Profile | No |
| `/profile/:username/favorites` | User Favorites | No |

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | Wisp 2.x + Mist 6.x | Idiomatic Gleam HTTP |
| Database | SQLite via sqlight | Zero-config, single-file |
| Auth tokens | HMAC-SHA256 | Simple, stateless, per spec |
| Password hash | SHA256 (MVP) -> Argon2 | Upgrade before production |
| Frontend | Lustre (target) | Official Gleam UI framework |
| Frontend (MVP) | Vanilla JS | Fast iteration, replaceable |
| CSS | RealWorld Conduit theme | Shared spec CSS |
| E2E testing | Playwright (TypeScript) | Per requirement |
| Formal spec | Quint | Types/invariants drive impl |
| Build | gleam build | Erlang (backend) + JS (frontend) |
