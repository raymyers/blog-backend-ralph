# Review: Session python-fastapi-5

Reviewed against commit `8178f03` — "feat: all 13 hurl milestones passing — 144 tests green"

---

## PR Review: python-fastapi-5 — Complete Conduit backend (hurl milestones 2–6)

| Category | Status | Issues |
|---|---|---|
| TDD Compliance  | ⚠️ | 1 |
| Testing Quality | ⚠️ | 3 |
| Type Safety     | ⚠️ | 2 |
| Clean Code      | ⚠️ | 2 |
| General Quality | ✅ | 0 |

**Recommendation**: APPROVE (with notes)

---

### Issues

⚠️ **TDD Compliance**: Route error-shape fixes were driven by failing hurl integration tests, not by Python tests first. `test_article_routes.py`, `test_profile_routes.py`, and `test_comment_routes.py` were written *after* the route code was corrected — reversing the RED→GREEN flow at the route layer. Unit-layer changes (tag_list sentinel, blank body validation, `CommentNotFoundError`) correctly followed TDD.

⚠️ **Testing Quality**: `test_create_article_returns_article_data` asserts four distinct things (title, slug, description, body) in a single test — each should be its own test so failures point to one broken behaviour. Same pattern in `test_add_comment_returns_comment_data` (body, id, author username). — `test_article_routes.py:34`, `test_comment_routes.py:27`

⚠️ **Testing Quality**: Several error-path tests assert two things at once — status code and error body field — e.g. `test_create_article_blank_title_returns_422`. One assertion per test is the goal. — `test_article_routes.py:50–54`

⚠️ **Testing Quality**: 1:1 file mapping — `test_article_routes.py` mirrors `articles.py`, `test_article_operations.py` mirrors `article_service.py`. The skill flags this as a signal that tests were written to cover implementations rather than to specify behaviour. Consider grouping by behaviour (e.g. `test_tag_management.py`) where multiple service+route interactions belong together.

⚠️ **Type Safety**: `tag_list: object = _UNSET` in `article_service.update()` drops all type information for the parameter — the caller gets no IDE/mypy guidance. A typed sentinel (e.g. a private `@dataclass` or `typing.Literal`) or an explicit `list[str] | type[_UNSET]` overload would preserve safety. — `article_service.py:79`

⚠️ **Clean Code**: `_resolve_comment()` in `comments.py` reaches into `profile_svc._users` and `profile_svc._follows` directly — breaking the service abstraction boundary. This was pre-existing but surfaces again here as new tests cover `_resolve_comment`'s output. The fix is to add a `get_profile(user_id)` method to `ProfileService` that returns `(User, following: bool)`. — `comments.py:32–36`

---

### What's good

✅ `_UNSET = object()` sentinel correctly distinguishes "not provided" from `[]` — the only safe way to handle an optional list-replace without breaking idempotency.

✅ `CommentNotFoundError(NotFoundError)` subclass is the right tool — lets route handlers catch article-not-found and comment-not-found at different scopes without an error-type field.

✅ `replace(article, ...)` from `dataclasses` keeps the update immutable — no mutation of the domain object.

✅ Hurl upgrade path (6.1.1 → 7.1.0) was the correct fix; patching spec files would have created drift with the upstream spec.

✅ All 144 Python tests and 149 hurl requests pass with clean isolation (StaticPool, per-test DB).

---

## Farley Review: backend/tests/ (full suite, 144 tests)

| Property | Score | Evidence |
|---|---|---|
| Understandable | 7/10 | Behaviour-focused names and section comments. Multi-assertion tests (`returns_article_data`, `returns_comment_data`) blur what exactly is being specified. |
| Maintainable | 7/10 | Tests hit HTTP contract, not internals. Error string literals (`"can't be blank"`) are stable spec strings. Assertions on exact JSON paths (`$.errors.article[0]`) are coupled to the error-shape convention — any restructuring there breaks tests. |
| Repeatable | 9/10 | StaticPool in-memory SQLite per fixture; no clock, no random, no network. Fully deterministic. |
| Atomic | 9/10 | Fresh DB per test via `client` fixture. No shared state. Tests are parallelisable. |
| Necessary | 7/10 | `test_create_article_returns_201` is made redundant by `test_create_article_returns_article_data` (if data comes back, status was 201). Minor duplication across unit and route layers for tag-list behaviour — defensible as different test levels. |
| Granular | 6/10 | Several tests assert 2–4 things: `returns_article_data` (4 assertions), `returns_comment_data` (3), most error tests (2: status + body). The norm should be one assertion per test. |
| Fast | 5/10 | 144 tests in ~17 s = ~118 ms/test average. Route tests require multiple round-trips (register → create article → act → assert). Unit tests are fast; the drag is the route layer needing full-stack setup per test. |
| First (TDD) | 5/10 | Service-layer unit tests were written before implementation (tag_list, blank body, CommentNotFoundError). Route error-shape tests were written *after* hurl failures revealed the bugs — the Python tests followed the fixes, not preceded them. |

### Farley Score: 7.0 / 10 — Good

`(7×1.5 + 7×1.5 + 9×1.25 + 9 + 7 + 6 + 5×0.75 + 5) / 9 = 63.0 / 9 = 7.0`

### Top Recommendations

1. **Split multi-assertion tests** — `test_create_article_returns_article_data` should become four separate tests (title, slug, description, body). This is the highest-impact change: it moves U, G, and N all up.

2. **Write route tests before the route fix** — When hurl reveals an error-shape bug, write a failing Python test *first*, then fix the route. One extra step but it locks in the RED→GREEN discipline at every layer.

3. **Add a `ProfileService.get_by_id(user_id)` method** — remove the `profile_svc._users`/`profile_svc._follows` reach-through in `_resolve_comment`. This also makes `_resolve_comment` testable in isolation without needing a full `ProfileService` object.

4. **Type the sentinel properly** — replace `tag_list: object = _UNSET` with a typed overload or a `_Unset` singleton class so mypy can check callers.

5. **Route test speed** — Extract a `registered_client(token)` fixture variant that pre-registers a user, reducing per-test round-trips from 2+ to 1 for the common case.
