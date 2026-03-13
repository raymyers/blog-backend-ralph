## PR Review: python-fastapi-4 — FastAPI RealWorld backend (all milestones)

| Category | Status | Issues |
|---|---|---|
| TDD Compliance | ❌ | 2 |
| Testing Quality | ⚠️ | 3 |
| Architecture | ❌ | 4 |
| Functional Patterns | ⚠️ | 2 |
| General Quality | ❌ | 2 |

**Recommendation: REQUEST CHANGES**

---

### Issues

🔴 **TDD Compliance**: `ArticleService`, `ProfileService`, `CommentService` have zero unit tests — `app/use_cases/article_service.py`, `profile_service.py`, `comment_service.py`. The testing skill is explicit: *"no production code without a failing test."* All business logic in these three files — slug generation, ownership checks, follow/unfollow, 404 handling — is only exercised via the hurl integration suite, not Python tests. Add `tests/test_article_service.py` and `tests/test_comment_and_profile_service.py` with in-memory fakes for the repositories, the same pattern used for `UserService`.

🔴 **TDD Compliance**: No tests for any route handler. Auth enforcement (401 for missing token, 403 for wrong owner), validation rejection (422 for blank title), and 404 paths in routes are untested at the Python level. These are the most likely places to regress silently. Use FastAPI's `TestClient` with an in-memory SQLite DB or the existing in-memory doubles.

🔴 **Architecture**: `ProfileService` imports `SQLModelUserRepository` directly — `profile_service.py:5`. A use-case class must not depend on an adapter; it breaks the hexagonal rule that dependencies point inward (routes → use_cases → ports ← adapters). Inject a `UserRepository` port instead and let the route's dependency-injection wire in the concrete adapter.

🔴 **Architecture**: `CommentService` bypasses the port layer entirely — `comment_service.py:3–5`. It holds a raw `sqlmodel.Session`, calls `select(Article)` directly, and has an unused `User` import on line 5 that reveals this class was never fully adapted. Extract a `CommentRepository` port (or re-use `ArticleRepository`) and follow the same pattern as `ArticleService`.

⚠️ **Architecture**: Routes reach through the service into the repository — `routes/articles.py:58, 62, 85, 108, 180`. `svc.article_repository.count_feed(...)` and `svc.article_repository.is_favorited(...)` are called directly from the route, exposing the repo as a public attribute of the service. Add `count_articles(...)` and `is_favorited(...)` methods to `ArticleService` so the route is not aware of the persistence layer.

⚠️ **Architecture**: `routes/auth.py` imports private symbols `_SECRET_KEY, _ALGORITHM` from `app/adapters/token.py` (line 3). The leading underscore signals "not public API". The JWT decoding key belongs in `app/config.py`'s `Settings`; read it there and pass it explicitly to both the token generator and the auth dependency.

⚠️ **Functional Patterns**: The 10-key article response dict is copy-pasted seven times across `routes/articles.py` (lines 64–69, 110–115, 130–136, 153–159, 182–188, 217–223, 237–243). A private `_article_dict(article, favorited, following)` helper would eliminate this duplication and make the one real difference per call-site (the `favorited` value) obvious.

⚠️ **Testing Quality**: `test_user_service.py` follows the 1:1 file-naming anti-pattern the testing skill flags. The file name mirrors the implementation (`user_service.py`). Rename to describe the behaviour being specified (e.g., `test_registration.py`, `test_authentication.py`) and split the scenarios accordingly — this also forces smaller, more focused files.

💡 **Testing Quality**: `test_update_user_bio_and_image` asserts `updated.bio == "A bio"` and `updated.image == "..."` in a single test. These are two distinct behaviors; split them. Also missing: `bio="   "` (whitespace-only) should normalize to `None` — the `strip()` call in `user_service.py:79` has no boundary test, leaving a surviving mutant.

💡 **Testing Quality**: `test_update_user_duplicate_username_raises` is absent. The duplicate-email path is tested but the symmetric username path is not. Both `DuplicateEmailError` and `DuplicateUsernameError` in `update_user` need coverage.

🔴 **General Quality**: `_SECRET_KEY = "your-secret-key-change-in-production"` at module level in `app/adapters/token.py:7` is a hardcoded secret. `app/config.py` already defines `Settings.jwt_secret_key` for exactly this purpose. Remove the module-level constant; read `get_settings().jwt_secret_key` inside `JWTTokenGenerator.__init__` when no argument is supplied.

⚠️ **General Quality**: `datetime.utcnow()` is deprecated in Python 3.12 and scheduled for removal. It appears in `user_service.py:83` and in model `Field(default_factory=datetime.utcnow)`. It produces 22 deprecation warnings on every test run. Replace with `datetime.now(timezone.utc)` throughout.

---

✅ Hexagonal structure (`domain / ports / adapters / use_cases / routes`) is cleanly layered where it's applied.  
✅ `UserService` follows the port/adapter contract correctly and is fully testable in isolation.  
✅ `make_service()` and `make_user_data()` factory helpers are exactly right — fresh instances per test, no shared mutable state.  
✅ Route ordering gotcha (feed before slug), `articlesCount` total-vs-page, and the CORS + error-shape handling are all correct and well-documented.

---

## Farley Review: `tests/test_user_service.py`

| Property | Score | Evidence |
|---|---|---|
| Understandable | 7/10 | Names read like a spec (`test_register_creates_user_with_token`, `test_login_wrong_password_raises`). Section comments help. Forty lines of test-double setup in the same file hurts the signal-to-noise ratio. |
| Maintainable | 7/10 | Tests the public API; `make_user_data()` factory shields tests from field changes. `InMemoryUserRepo.create` mutates the passed `User` object in place (`user.id = self._next_id`) — a subtle implementation-coupling that could break if the service ever relies on the original object being unchanged after `create`. |
| Repeatable | 9/10 | Pure in-memory, no I/O, no network, no time-dependent assertions. Fully deterministic. |
| Atomic | 8/10 | `make_service()` constructs a fresh service per test — no shared state. Minor: `InMemoryUserRepo.create` mutates its argument rather than returning a new instance, which can produce surprising aliasing. |
| Necessary | 8/10 | All 10 tests cover distinct scenarios. Missing: `update_user` with duplicate username, and the whitespace-only bio boundary. |
| Granular | 7/10 | `test_register_creates_user_with_token` asserts `email`, `username`, and `token` — three things. `test_update_user_bio_and_image` asserts two fields. Both are mild but separable. |
| Fast | 9/10 | 10 tests in 0.28 s. In-memory only. |
| First (TDD) | 4/10 | All 31 production and test files landed in a single commit. No RED→GREEN→REFACTOR progression visible in git history. Commit message claims the intent but the evidence is absent. |

### Farley Score: 7.3/10 — **Good**

`(7×1.5 + 7×1.5 + 9×1.25 + 8 + 8 + 7 + 9×0.75 + 4) / 9 = 66/9 = 7.3`

### Top Recommendations

1. **Split the single commit into RED → GREEN steps.** The test file is good enough that it deserves visible TDD provenance. Even one "test: add failing tests for UserService" commit before "feat: implement UserService" would move T from 4 to 7 and raise the score into the excellent band.
2. **Add tests for ArticleService and CommentService** using the same in-memory double pattern. Slug uniqueness, ownership checks, and 404 paths in those services are high-value, fast-to-test behaviors that the hurl suite cannot isolate.
3. **Split `test_register_creates_user_with_token` and `test_update_user_bio_and_image`** into single-assertion tests. This also forces you to name the missing boundary cases (`whitespace_bio_normalizes_to_null`, `duplicate_username_raises`), which are currently surviving mutants.
