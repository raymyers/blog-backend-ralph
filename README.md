# blog-backend-ralph

A backend implementation of the [RealWorld](https://github.com/realworld-apps/realworld) API spec — a Medium.com clone ("Conduit") used to demonstrate real-world usage of frameworks and languages.

## API Spec

The backend spec lives in [`realworld/specs/api/`](realworld/specs/api/), included as a git submodule from [realworld-apps/realworld](https://github.com/realworld-apps/realworld). It includes:

- [`realworld/specs/api/openapi.yml`](realworld/specs/api/openapi.yml) — OpenAPI specification
- [`realworld/specs/api/hurl/`](realworld/specs/api/hurl/) — [Hurl](https://hurl.dev) API test suite (source of truth)
- [`realworld/specs/api/bruno/`](realworld/specs/api/bruno/) — [Bruno](https://www.usebruno.com) collection (generated from Hurl)

### Setup

```bash
git submodule update --init
```

### Running API tests

**With Hurl:**

```bash
HOST=http://localhost:3000/api ./realworld/specs/api/run-api-tests-hurl.sh
```

**With Bruno:**

```bash
HOST=http://localhost:3000/api ./realworld/specs/api/run-api-tests-bruno.sh
```

## Credits

API spec and test suite from [realworld-apps/realworld](https://github.com/realworld-apps/realworld), used under the [MIT License](https://github.com/realworld-apps/realworld/blob/main/LICENSE).
