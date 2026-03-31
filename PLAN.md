# RealWorld Conduit — Full-Stack Gleam + Lustre Implementation Plan

> A Medium.com clone ("Conduit") built entirely in **Gleam** with a **Lustre** SPA frontend,
> a **Hexagonal Architecture** backend, and **Playwright** E2E tests.
>
> Spec: https://github.com/realworld-apps/realworld

---

## Architecture Overview

### Backend (Gleam — Hexagonal / Ports & Adapters)

```
conduit/
├── src/conduit/
│   ├── domain/           # Pure domain types, value objects, business rules
│   │   ├── user.gleam
│   │   ├── article.gleam
│   │   ├── comment.gleam
│   │   ├── tag.gleam
│   │   └── profile.gleam
│   ├── ports/            # Port interfaces (traits/behaviours)
│   │   ├── user_repo.gleam
│   │   ├── article_repo.gleam
│   │   ├── comment_repo.gleam
│   │   ├── tag_repo.gleam
│   │   ├── password_hasher.gleam
│   │   └── token_provider.gleam
│   ├── app/              # Application services / use-cases (orchestration)
│   │   ├── auth_service.gleam
│   │   ├── user_service.gleam
│   │   ├── article_service.gleam
│   │   ├── comment_service.gleam
│   │   ├── profile_service.gleam
│   │   └── tag_service.gleam
│   ├── adapters/
│   │   ├── web/          # Inbound: HTTP handlers (Wisp)
│   │   │   ├── router.gleam
│   │   │   ├── middleware.gleam
│   │   │   ├── user_handler.gleam
│   │   │   ├── article_handler.gleam
│   │   │   ├── comment_handler.gleam
│   │   │   ├── profile_handler.gleam
│   │   │   ├── tag_handler.gleam
│   │   │   └── json_codec.gleam
│   │   ├── db/           # Outbound: Persistence (sqlight / pgo)
│   │   │   ├── user_repo_db.gleam
│   │   │   ├── article_repo_db.gleam
│   │   │   ├── comment_repo_db.gleam
│   │   │   ├── tag_repo_db.gleam
│   │   │   └── migrations.gleam
│   │   └── crypto/       # Outbound: JWT + password hashing
│   │       ├── jwt_provider.gleam
│   │       └── bcrypt_hasher.gleam
│   └── conduit.gleam     # Entrypoint — wires adapters to ports, starts server
└── test/
```

### Frontend (Gleam + Lustre SPA)

```
conduit_ui/
├── src/conduit_ui/
│   ├── app.gleam         # Lustre application root, top-level Model/Msg/update/view
│   ├── router.gleam      # Client-side routing (URL → Route type)
│   ├── api/              # HTTP client (lustre_http) — one module per resource
│   │   ├── auth_api.gleam
│   │   ├── article_api.gleam
│   │   ├── comment_api.gleam
│   │   ├── profile_api.gleam
│   │   └── tag_api.gleam
│   ├── model/            # Shared types mirroring API response shapes
│   │   ├── user.gleam
│   │   ├── article.gleam
│   │   ├── comment.gleam
│   │   └── session.gleam
│   ├── pages/            # One module per route / page
│   │   ├── home.gleam
│   │   ├── login.gleam
│   │   ├── register.gleam
│   │   ├── settings.gleam
│   │   ├── editor.gleam
│   │   ├── article.gleam
│   │   └── profile.gleam
│   ├── components/       # Reusable view fragments
│   │   ├── navbar.gleam
│   │   ├── footer.gleam
│   │   ├── article_preview.gleam
│   │   ├── tag_list.gleam
│   │   ├── pagination.gleam
│   │   └── error_messages.gleam
│   └── debug.gleam       # window.__conduit_debug__ interface (E2E contract)
└── test/
```

### E2E Tests (Playwright — TypeScript)

```
e2e/
├── playwright.config.ts
├── helpers/
│   └── test_utils.ts
├── auth.spec.ts
├── articles.spec.ts
├── comments.spec.ts
├── navigation.spec.ts
├── profile.spec.ts
├── pagination.spec.ts
└── error-handling.spec.ts
```

---

## Milestones

---

### Milestone 0 — Project Scaffolding & Dev Tooling

> Set up mono-repo structure, tooling, CI-ready dev environment.

- [ ] Initialize Gleam backend project (`conduit`) with `gleam new`
- [ ] Initialize Gleam frontend project (`conduit_ui`) with `gleam new` targeting JavaScript
- [ ] Add backend dependencies: `wisp`, `mist`, `gleam_http`, `gleam_json`, `sqlight` (or `pgo`), `birl` (time), `gleam_crypto`
- [ ] Add frontend dependencies: `lustre`, `lustre_http`, `gleam_json`, `modem` (routing)
- [ ] Set up Lustre dev build pipeline (gleam build → bundle JS → serve)
- [ ] Create `Makefile` / `justfile` with commands: `dev`, `build`, `test`, `fmt`, `e2e`
- [ ] Create Docker Compose for local dev (database + app)
- [ ] Initialize Playwright project in `e2e/` with TypeScript config
- [ ] Set up static asset serving — backend serves the Lustre SPA + RealWorld CSS
- [ ] Create shared RealWorld CSS integration (link Conduit theme stylesheet)
- [ ] Smoke test: backend returns HTML shell, Lustre mounts and renders "Hello Conduit"
- [ ] Write `AGENTS.md` with build commands, project structure, and conventions

#### 🔍 Milestone 0 Assessment — Tooling & Foundation
- [ ] Verify `gleam build`, `gleam test`, and `gleam run` succeed for both projects
- [ ] Verify Playwright can launch browser, navigate to app, and see mounted Lustre app
- [ ] Review project layout — confirm Hexagonal layers are cleanly separated in directory structure
- [ ] Confirm no circular dependencies between `domain/`, `ports/`, `app/`, `adapters/`

---

### Milestone 1 — Domain Core & Hexagonal Skeleton

> Build the pure domain layer and port interfaces — zero I/O, fully testable.

- [ ] Define `domain/user.gleam` — `User`, `NewUser`, `UpdateUser`, `LoginCredentials` types
- [ ] Define `domain/article.gleam` — `Article`, `NewArticle`, `UpdateArticle`, slug generation logic
- [ ] Define `domain/comment.gleam` — `Comment`, `NewComment` types
- [ ] Define `domain/tag.gleam` — `Tag` type
- [ ] Define `domain/profile.gleam` — `Profile` type (username, bio, image, following)
- [ ] Define domain error types — `DomainError` (not_found, unauthorized, forbidden, validation, conflict)
- [ ] Define `ports/user_repo.gleam` — type alias / record for user repository operations
- [ ] Define `ports/article_repo.gleam` — type alias / record for article CRUD + queries
- [ ] Define `ports/comment_repo.gleam` — type alias / record for comment operations
- [ ] Define `ports/tag_repo.gleam` — type alias / record for tag listing
- [ ] Define `ports/password_hasher.gleam` — hash / verify port
- [ ] Define `ports/token_provider.gleam` — sign / verify JWT port
- [ ] Implement slug generation — `title_to_slug` with transliteration and uniqueness suffix
- [ ] Write unit tests for domain types (construction, validation, slug generation)

#### 🔍 Milestone 1 Assessment — Domain Purity & Modularity
- [ ] Run `gleam test` — all domain unit tests pass
- [ ] Audit: domain modules import **nothing** from `adapters/` or `app/`
- [ ] Audit: port definitions are abstract — no concrete DB or HTTP references
- [ ] Confirm domain types are exhaustive per OpenAPI spec (User, Profile, Article, Comment, Tag)

---

### Milestone 2 — Database & Outbound Adapters

> Implement persistence adapters that satisfy port interfaces.

- [ ] Design SQL schema: `users`, `articles`, `tags`, `article_tags`, `comments`, `follows`, `favorites`
- [ ] Implement `adapters/db/migrations.gleam` — create tables on startup
- [ ] Implement `adapters/db/user_repo_db.gleam` — insert, find_by_email, find_by_id, find_by_username, update
- [ ] Implement `adapters/db/article_repo_db.gleam` — insert, find_by_slug, update, delete, list (with filters), feed
- [ ] Implement `adapters/db/comment_repo_db.gleam` — insert, find_by_article, find_by_id, delete
- [ ] Implement `adapters/db/tag_repo_db.gleam` — list all, find_or_create, attach to article
- [ ] Implement follow/unfollow persistence in user repo
- [ ] Implement favorite/unfavorite persistence in article repo
- [ ] Implement `adapters/crypto/bcrypt_hasher.gleam` (or argon2 via FFI)
- [ ] Implement `adapters/crypto/jwt_provider.gleam` — sign and verify JWT tokens (`HS256`)
- [ ] Write integration tests for each repo adapter (real DB, seeded data)

#### 🔍 Milestone 2 Assessment — Adapter Isolation & Tests
- [ ] Run integration tests — all DB adapters pass
- [ ] Audit: adapter modules only import from `domain/` and `ports/` — never from `app/` or other adapters
- [ ] Verify repo adapters are injectable (passed as function records, not hard-coded)
- [ ] Confirm JWT round-trip: sign → verify → extract user ID

---

### Milestone 3 — Application Services (Use-Cases)

> Orchestration layer connecting ports — business workflows with no HTTP or SQL awareness.

- [ ] Implement `app/auth_service.gleam` — register, login (returns User + token)
- [ ] Implement `app/user_service.gleam` — get_current_user, update_user
- [ ] Implement `app/profile_service.gleam` — get_profile, follow, unfollow
- [ ] Implement `app/article_service.gleam` — create, get, update, delete, list, feed
- [ ] Implement `app/comment_service.gleam` — create, list_by_article, delete
- [ ] Implement `app/tag_service.gleam` — get_all_tags
- [ ] Implement favorite/unfavorite in article_service
- [ ] Handle authorization: article owner checks for update/delete, comment owner for delete
- [ ] Handle conflict detection: duplicate username/email on register, duplicate slug
- [ ] Write unit tests for services using in-memory stub repos (test doubles, not mocks)

#### 🔍 Milestone 3 Assessment — Service Layer Quality
- [ ] Run all service unit tests — pass
- [ ] Audit: service modules import from `domain/` and `ports/` only — never `adapters/`
- [ ] Confirm each service function returns `Result(T, DomainError)` — clean error propagation
- [ ] Check services are stateless — all state passed via function parameters

---

### Milestone 4 — HTTP API (Inbound Web Adapter)

> Wisp-based HTTP layer: routing, JSON serialization, auth middleware, error responses.

- [ ] Implement `adapters/web/router.gleam` — map routes per OpenAPI spec
- [ ] Implement `adapters/web/middleware.gleam` — extract JWT from `Authorization: Token ...` header
- [ ] Implement `adapters/web/json_codec.gleam` — encode/decode all request/response shapes
- [ ] Implement `adapters/web/user_handler.gleam` — POST /api/users/login, POST /api/users, GET /api/user, PUT /api/user
- [ ] Implement `adapters/web/profile_handler.gleam` — GET /api/profiles/:username, POST/DELETE follow
- [ ] Implement `adapters/web/article_handler.gleam` — full CRUD + list + feed
- [ ] Implement `adapters/web/comment_handler.gleam` — POST, GET, DELETE comments
- [ ] Implement `adapters/web/tag_handler.gleam` — GET /api/tags
- [ ] Implement proper HTTP status codes: 200, 201, 204, 401, 403, 404, 409, 422
- [ ] Implement error response format: `{ "errors": { "field": ["message"] } }`
- [ ] Add CORS headers for cross-origin requests
- [ ] Wire everything in `conduit.gleam` — inject adapters into services, services into handlers
- [ ] Test API with Hurl test suite from RealWorld spec (`run-api-tests-hurl.sh`)

#### 🔍 Milestone 4 Assessment — API Compliance & Modularity
- [ ] Run the official RealWorld Hurl API test suite — all tests pass
- [ ] Verify every OpenAPI endpoint returns correct response shape with `Content-Type: application/json`
- [ ] Audit: handler modules only call service functions — no direct DB access
- [ ] Audit: JSON codec is centralized — no scattered encode/decode across handlers
- [ ] Confirm auth middleware correctly handles optional-auth vs required-auth endpoints

---

### Milestone 5 — Lustre Frontend: Shell, Routing & Auth Pages

> Lustre SPA skeleton with client-side routing, auth state, and sign-in / sign-up / settings.

- [ ] Implement `app.gleam` — top-level Lustre application (`init`, `update`, `view`)
- [ ] Implement `router.gleam` — URL parsing with `modem`, `Route` custom type matching all pages
- [ ] Implement `model/session.gleam` — auth state (token in localStorage, current user)
- [ ] Implement `model/user.gleam` — User, Profile types for frontend
- [ ] Implement `api/auth_api.gleam` — register, login, get_current_user, update_user HTTP calls
- [ ] Implement `components/navbar.gleam` — conditional nav links based on auth state, `.navbar`, `.nav-link`, `.user-pic` classes
- [ ] Implement `components/footer.gleam` — site footer
- [ ] Implement `pages/login.gleam` — sign-in form (`input[name="email"]`, `input[name="password"]`), error display
- [ ] Implement `pages/register.gleam` — sign-up form (`input[name="username"]`, `input[name="email"]`, `input[name="password"]`)
- [ ] Implement `pages/settings.gleam` — settings form (image, username, bio, email, password), logout button
- [ ] Implement `components/error_messages.gleam` — `.error-messages` ul for validation errors
- [ ] Implement `debug.gleam` — expose `window.__conduit_debug__` (getToken, getAuthState, getCurrentUser)
- [ ] Store JWT in localStorage under `jwtToken` key
- [ ] Handle auth redirects — protected pages redirect to `/login` when unauthenticated
- [ ] Playwright: write `auth.spec.ts` — register, login, logout, settings update

#### 🔍 Milestone 5 Assessment — Frontend Foundation & E2E
- [ ] Playwright `auth.spec.ts` passes — register, login, view settings, update, logout
- [ ] Verify `window.__conduit_debug__` contract matches E2E spec (getToken, getAuthState, getCurrentUser)
- [ ] Audit: page modules are self-contained — each has its own Msg type, update, view
- [ ] Audit: API modules return `Effect(Msg)` — no raw JS interop scattered in pages
- [ ] Confirm CSS classes match SELECTORS.md contract (`.navbar`, `.nav-link`, `.error-messages`, etc.)

---

### Milestone 6 — Home Page: Feeds, Tags & Article Previews

> Global feed, your feed, tag filtering, sidebar, pagination.

- [ ] Implement `api/article_api.gleam` — list articles, feed articles (with query params)
- [ ] Implement `api/tag_api.gleam` — get tags
- [ ] Implement `model/article.gleam` — Article, ArticleList types
- [ ] Implement `pages/home.gleam` — Global Feed / Your Feed toggle (`.feed-toggle`, `.nav-link`)
- [ ] Implement `components/article_preview.gleam` — article card (`.article-preview`, `.article-meta`, `.preview-link`, `.author`)
- [ ] Implement `components/tag_list.gleam` — sidebar tags (`.sidebar`, `.tag-list`, `.tag-default`, `.tag-pill`)
- [ ] Implement `components/pagination.gleam` — page buttons (`.pagination`, `.page-item`, `active` class)
- [ ] Implement tag filtering — click tag → navigate to `/tag/:tag`, show filtered results
- [ ] Implement feed toggle — "Global Feed" vs "Your Feed" tabs, tag tab when filtering
- [ ] Implement pagination — `?page=N` query param, limit/offset calculation
- [ ] Implement `.banner` hero section on home page
- [ ] Implement `.empty-feed-message` when no articles
- [ ] Playwright: write `navigation.spec.ts` — home page loads, feed tabs work, tag click filters
- [ ] Playwright: write pagination section of `articles.spec.ts`

#### 🔍 Milestone 6 Assessment — Feed & Navigation E2E
- [ ] Playwright `navigation.spec.ts` passes
- [ ] Verify feed toggle switches between global/your feed correctly
- [ ] Verify pagination renders correct page count and navigates properly
- [ ] Audit: home page component is composed from small, reusable sub-components
- [ ] Confirm all CSS selectors from SELECTORS.md are present (`.feed-toggle`, `.article-preview`, `.sidebar`, `.pagination`)

---

### Milestone 7 — Article Detail, Editor & CRUD

> Create, read, update, delete articles with the editor and article detail page.

- [ ] Implement `api/article_api.gleam` — get article, create, update, delete
- [ ] Implement `pages/editor.gleam` — new article form (`input[name="title"]`, `input[name="description"]`, `textarea[name="body"]`, tag input)
- [ ] Implement editor tag input — `input[placeholder="Enter tags"]`, add/remove tag pills
- [ ] Implement `pages/article.gleam` — article detail page (`.article-page`, `.article-content`, `.article-meta`)
- [ ] Implement markdown rendering for article body (client-side)
- [ ] Implement edit article — `/editor/:slug` pre-fills form, "Publish Article" button updates
- [ ] Implement delete article — "Delete Article" button (only shown to author)
- [ ] Implement "Edit Article" link (only shown to author)
- [ ] Implement favorite button on article detail — `.btn-outline-primary` / `.btn-primary` toggle
- [ ] Implement `api/article_api.gleam` — favorite / unfavorite
- [ ] Implement favorite button on article previews in feed
- [ ] Playwright: write `articles.spec.ts` — create article, view, edit, delete, favorite/unfavorite

#### 🔍 Milestone 7 Assessment — Article CRUD & E2E
- [ ] Playwright `articles.spec.ts` passes — full article lifecycle
- [ ] Verify editor handles tag input correctly (add, remove, persist)
- [ ] Verify article body renders as markdown
- [ ] Verify author-only actions (edit, delete) are hidden for non-authors
- [ ] Audit: editor page reuses form logic for both create and edit modes (no duplication)

---

### Milestone 8 — Comments

> Comment section on article detail — create, list, delete.

- [ ] Implement `api/comment_api.gleam` — get comments, post comment, delete comment
- [ ] Implement `model/comment.gleam` — Comment type for frontend
- [ ] Implement comment form on article page — `textarea[placeholder="Write a comment..."]`, "Post Comment" button
- [ ] Implement comment list — `.card`, `.card-block`, `.comment-author-img`
- [ ] Implement comment form wrapper — `.comment-form` class
- [ ] Implement delete comment — `.mod-options` with `.ion-trash-a` icon (only for comment author)
- [ ] Show user avatar in comment form (logged-in user's image)
- [ ] Hide comment form when not authenticated
- [ ] Playwright: write `comments.spec.ts` — post comment, view, delete

#### 🔍 Milestone 8 Assessment — Comments E2E
- [ ] Playwright `comments.spec.ts` passes — full comment lifecycle
- [ ] Verify delete button only appears for comment author
- [ ] Verify comment form hidden for unauthenticated users
- [ ] Audit: comment component is decoupled from article page — reusable section

---

### Milestone 9 — Profiles & Following

> Profile pages, following system, favorites tab.

- [ ] Implement `api/profile_api.gleam` — get profile, follow, unfollow
- [ ] Implement `pages/profile.gleam` — `.profile-page`, `.user-info`, `.user-img`
- [ ] Implement "My Articles" and "Favorited Articles" tabs on profile page
- [ ] Implement follow/unfollow button — text toggles `Follow {username}` / `Unfollow {username}`
- [ ] Implement "Edit Profile Settings" link (shown when viewing own profile)
- [ ] Implement follow/unfollow button on article detail page (in `.article-meta`)
- [ ] Route `/profile/:username` shows authored articles, `/profile/:username/favorites` shows favorited
- [ ] Implement default avatar — when `image` is null, show `default-avatar.svg`
- [ ] Playwright: write `profile.spec.ts` — view profile, follow/unfollow, tab switch

#### 🔍 Milestone 9 Assessment — Profiles & Social E2E
- [ ] Playwright `profile.spec.ts` passes — follow, unfollow, tab navigation
- [ ] Verify "Your Feed" on home page shows articles only from followed users
- [ ] Verify default avatar is used when user has no image set
- [ ] Audit: profile page reuses `article_preview` and `pagination` components
- [ ] Confirm all `.user-info`, `.user-img`, `.user-pic` CSS classes present

---

### Milestone 10 — Error Handling & Edge Cases

> Robust error handling, validation feedback, 404s, and edge-case coverage.

- [ ] Implement client-side validation — required fields, email format
- [ ] Implement server-side validation error display — `.error-messages` populated from 422 responses
- [ ] Handle 401 responses globally — clear token, redirect to login
- [ ] Handle 404 — show "not found" UI for missing articles/profiles
- [ ] Handle network errors gracefully — display feedback to user
- [ ] Handle null bio/image fields per spec (nullable fields in JSON)
- [ ] Implement conflict error handling (409) — duplicate username/email on register
- [ ] Implement slug update when article title changes
- [ ] Playwright: write `error-handling.spec.ts` — invalid login, duplicate register, validation errors
- [ ] Playwright: write `null-fields.spec.ts` — null bio/image handling

#### 🔍 Milestone 10 Assessment — Robustness & Error E2E
- [ ] Playwright `error-handling.spec.ts` passes
- [ ] Playwright `null-fields.spec.ts` passes
- [ ] Verify all API error responses match `{ "errors": { ... } }` format
- [ ] Audit: error handling is centralized — single `handle_api_error` function, not per-page
- [ ] Confirm no unhandled promise rejections or Gleam panics in browser console

---

### Milestone 11 — Full E2E Suite & Official Spec Compliance

> Run the complete official test suites, polish, and verify full compliance.

- [ ] Run official RealWorld Hurl API test suite — fix any remaining failures
- [ ] Run official RealWorld E2E Playwright suite from `specs/e2e/` — fix any failures
- [ ] Write `health.spec.ts` — basic health/smoke test
- [ ] Verify all routes from SELECTORS.md are implemented and navigable
- [ ] Verify all CSS classes from SELECTORS.md are present in rendered HTML
- [ ] Verify all `name` attributes from SELECTORS.md are on form inputs
- [ ] Verify all required text content (button labels, headings) from SELECTORS.md
- [ ] Verify `window.__conduit_debug__` fully implemented per contract
- [ ] Verify `localStorage.jwtToken` is set/cleared correctly
- [ ] Verify default avatar behavior for all avatar locations
- [ ] Verify button state conventions (favorite toggle classes, follow text toggle)
- [ ] Performance check — feed loads under 2s, no obvious memory leaks in SPA

#### 🔍 Milestone 11 Assessment — Final Compliance & Architecture Review
- [ ] **All** official Hurl API tests pass
- [ ] **All** official Playwright E2E tests pass
- [ ] **All** custom Playwright tests pass
- [ ] Full Hexagonal Architecture audit:
  - [ ] `domain/` has zero imports from `adapters/` or external libraries (except gleam stdlib)
  - [ ] `ports/` define abstract interfaces with no implementation details
  - [ ] `app/` services depend only on `domain/` and `ports/`
  - [ ] `adapters/web/` depends on `app/` and `domain/` — never on `adapters/db/`
  - [ ] `adapters/db/` depends on `domain/` and `ports/` — never on `adapters/web/`
  - [ ] All adapters are injectable via function parameters (no global state)
- [ ] Frontend modularity audit:
  - [ ] Each page module is independently testable
  - [ ] Shared components are reused across pages (no copy-paste)
  - [ ] API layer is decoupled — swapping base URL requires one-line change
  - [ ] Router is exhaustive — all routes handled, no catch-all fallthrough
- [ ] Code quality: `gleam format` produces no changes, zero compiler warnings

---

## API Endpoints Summary

| Method | Path | Auth | Handler |
|--------|------|------|---------|
| POST | `/api/users/login` | No | `user_handler` |
| POST | `/api/users` | No | `user_handler` |
| GET | `/api/user` | Required | `user_handler` |
| PUT | `/api/user` | Required | `user_handler` |
| GET | `/api/profiles/:username` | Optional | `profile_handler` |
| POST | `/api/profiles/:username/follow` | Required | `profile_handler` |
| DELETE | `/api/profiles/:username/follow` | Required | `profile_handler` |
| GET | `/api/articles` | Optional | `article_handler` |
| GET | `/api/articles/feed` | Required | `article_handler` |
| POST | `/api/articles` | Required | `article_handler` |
| GET | `/api/articles/:slug` | No | `article_handler` |
| PUT | `/api/articles/:slug` | Required | `article_handler` |
| DELETE | `/api/articles/:slug` | Required | `article_handler` |
| POST | `/api/articles/:slug/comments` | Required | `comment_handler` |
| GET | `/api/articles/:slug/comments` | Optional | `comment_handler` |
| DELETE | `/api/articles/:slug/comments/:id` | Required | `comment_handler` |
| POST | `/api/articles/:slug/favorite` | Required | `article_handler` |
| DELETE | `/api/articles/:slug/favorite` | Required | `article_handler` |
| GET | `/api/tags` | No | `tag_handler` |

## Frontend Routes Summary

| Route | Page | Auth |
|-------|------|------|
| `/` | Home — Global Feed | No |
| `/?feed=following` | Home — Your Feed | Required |
| `/?page=N` | Home — Paginated | No |
| `/tag/:tag` | Home — Filtered by Tag | No |
| `/login` | Sign In | No |
| `/register` | Sign Up | No |
| `/settings` | User Settings | Required |
| `/editor` | New Article | Required |
| `/editor/:slug` | Edit Article | Required |
| `/article/:slug` | Article Detail | No |
| `/profile/:username` | User Profile | No |
| `/profile/:username/favorites` | User Favorites | No |

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | **Wisp** + **Mist** | Idiomatic Gleam HTTP, production-ready |
| Database | **SQLite** via `sqlight` | Zero-config dev, single-file persistence |
| Auth | **JWT (HS256)** | Per RealWorld spec, `Token` scheme |
| Password hashing | **Argon2** or **bcrypt** via FFI | Security best practice |
| Frontend framework | **Lustre** | Official Gleam UI framework, Elm-like architecture |
| Routing (frontend) | **modem** | Standard Lustre routing companion |
| HTTP client (frontend) | **lustre_http** | Lustre-integrated effects |
| CSS | **RealWorld Conduit theme** | Shared spec CSS, no custom styles needed |
| E2E testing | **Playwright** (TypeScript) | Per requirement, matches official E2E suite |
| Build | **gleam build** + bundler | Gleam compiles to JS for frontend |
