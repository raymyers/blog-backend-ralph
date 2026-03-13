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
