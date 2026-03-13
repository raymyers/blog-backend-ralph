# Backend Implementation Plan

Tech-agnostic plan for the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" backend API.

Spec references:
- Endpoint & response specs: [`realworld/docs/src/content/docs/specifications/backend/`](../../realworld/docs/src/content/docs/specifications/backend/)
- API test suite: [`realworld/specs/api/`](../../realworld/specs/api/)

---

## Milestone 1: Auth & Users ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md) · [error-handling.md](../../realworld/docs/src/content/docs/specifications/backend/error-handling.md) · [cors.md](../../realworld/docs/src/content/docs/specifications/backend/cors.md)

### Data model
- [x] User: `email` (unique), `username` (unique), `password` (hashed), `bio` (nullable), `image` (nullable)

### Endpoints
- [x] Refresh your understanding of AGENTS.md expectations.
- [x] `POST /api/users` — register; required: `email`, `username`, `password`; returns user + JWT; HTTP 201
- [x] `POST /api/users/login` — login; required: `email`, `password`; returns user + JWT
- [x] `GET /api/user` — auth required; returns current user with fresh token
- [x] `PUT /api/user` — auth required; accepted: `email`, `username`, `password`, `bio`, `image`; empty string for `bio`/`image` normalizes to `null`; reject empty or null `email`/`username` with 422

### Auth middleware
- [x] Parse `Authorization: Token <jwt>` header on protected routes
- [x] Return 401 when token is absent or invalid

### Error handling
- [x] 422 with `{ "errors": { "body": [...] } }` for validation failures
- [x] 401 for unauthenticated requests to protected routes
- [x] 403 for authenticated requests that lack permission
- [x] 404 for resources that do not exist

### CORS
- [x] Handle `OPTIONS` preflight requests
- [x] Return appropriate `Access-Control-Allow-Origin` and `Access-Control-Allow-Headers` headers

### Tests
- [x] Pass [`realworld/specs/api/hurl/auth.hurl`](../../realworld/specs/api/hurl/auth.hurl)
- [x] Pass [`realworld/specs/api/hurl/errors_auth.hurl`](../../realworld/specs/api/hurl/errors_auth.hurl)

---

## Milestone 2: Articles ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md)

### Data model
- [x] Article: `slug` (unique), `title`, `description`, `body`, `tagList`, `createdAt`, `updatedAt`, author (User ref), `favoritesCount`
- [x] Slug derived from title; append a unique suffix on collision
- [x] Slug updates when title is changed via `PUT`

### Endpoints
- [x] `POST /api/articles` — auth required; required: `title`, `description`, `body`; optional: `tagList`; HTTP 201
- [x] `GET /api/articles/:slug` — auth optional; returns single article
- [x] `PUT /api/articles/:slug` — auth required, owner only; optional: `title`, `description`, `body`, `tagList`; 403 for non-owner; `tagList: null` → 422
- [x] `DELETE /api/articles/:slug` — auth required, owner only; 403 for non-owner; HTTP 204
- [x] `GET /api/tags` — no auth; returns list of all distinct tags

### Tests
- [x] Pass [`realworld/specs/api/hurl/articles.hurl`](../../realworld/specs/api/hurl/articles.hurl)
- [x] Pass [`realworld/specs/api/hurl/tags.hurl`](../../realworld/specs/api/hurl/tags.hurl)
- [x] Pass [`realworld/specs/api/hurl/errors_articles.hurl`](../../realworld/specs/api/hurl/errors_articles.hurl)

---

## Milestone 3: Profiles & Following ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md)

### Data model
- [x] Follow relationship: User → User (many-to-many)
- [x] `following` field on all Profile responses reflects whether the requesting user follows that profile

### Endpoints
- [x] `GET /api/profiles/:username` — auth optional; 404 for unknown username
- [x] `POST /api/profiles/:username/follow` — auth required; 404 for unknown username
- [x] `DELETE /api/profiles/:username/follow` — auth required; 404 for unknown username

### Tests
- [x] Pass [`realworld/specs/api/hurl/profiles.hurl`](../../realworld/specs/api/hurl/profiles.hurl)
- [x] Pass [`realworld/specs/api/hurl/errors_profiles.hurl`](../../realworld/specs/api/hurl/errors_profiles.hurl)

---

## Milestone 4: Article Listing & Pagination ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md)

### Endpoints
- [x] `GET /api/articles` — auth optional; filter by `tag`, `author`, `favorited`; `limit` (default 20), `offset` (default 0); ordered most-recent first; response includes `articlesCount`; article objects omit `body`
- [x] `GET /api/articles/feed` — auth required; returns articles by followed users only; same pagination parameters and response shape

### Tests
- [x] Pass [`realworld/specs/api/hurl/pagination.hurl`](../../realworld/specs/api/hurl/pagination.hurl)
- [x] Pass [`realworld/specs/api/hurl/feed.hurl`](../../realworld/specs/api/hurl/feed.hurl)

---

## Milestone 5: Comments ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md)

### Data model
- [x] Comment: `id`, `body`, `createdAt`, `updatedAt`, author (User ref), article (Article ref)

### Endpoints
- [x] `POST /api/articles/:slug/comments` — auth required; required: `body`; blank body → 422; 404 for unknown slug; HTTP 201
- [x] `GET /api/articles/:slug/comments` — auth optional; 404 for unknown slug
- [x] `DELETE /api/articles/:slug/comments/:id` — auth required, comment owner only; 403 for non-owner; 404 for unknown slug or comment; HTTP 204

### Tests
- [x] Pass [`realworld/specs/api/hurl/comments.hurl`](../../realworld/specs/api/hurl/comments.hurl)
- [x] Pass [`realworld/specs/api/hurl/errors_comments.hurl`](../../realworld/specs/api/hurl/errors_comments.hurl)
- [x] Pass [`realworld/specs/api/hurl/errors_authorization.hurl`](../../realworld/specs/api/hurl/errors_authorization.hurl)

---

## Milestone 6: Favorites ✅

**Spec refs:** [endpoints.md](../../realworld/docs/src/content/docs/specifications/backend/endpoints.md) · [api-response-format.md](../../realworld/docs/src/content/docs/specifications/backend/api-response-format.md)

### Data model
- [x] Favorite relationship: User ↔ Article (many-to-many)
- [x] `favoritesCount` on Article reflects total favorites across all users
- [x] `favorited` on all Article responses reflects the requesting user's status

### Endpoints
- [x] `POST /api/articles/:slug/favorite` — auth required; returns updated article; idempotent
- [x] `DELETE /api/articles/:slug/favorite` — auth required; returns updated article; idempotent
- [x] Filter `GET /api/articles?favorited=:username` returns articles favorited by that user

### Tests
- [x] Pass [`realworld/specs/api/hurl/favorites.hurl`](../../realworld/specs/api/hurl/favorites.hurl)
- [x] Pass full suite: all 13 hurl files, 149 requests, 100% pass rate
