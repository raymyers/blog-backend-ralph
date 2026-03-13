---
name: architecture
description: Code architecture patterns. Covers functional style (immutability, pure functions, composition), TypeScript strict mode (no any, type vs interface, schema-first), and opt-in DDD and hexagonal architecture.
---
# Architecture

## Functional Style

**Immutability** — never mutate data:
```typescript
// ❌ items.push(x) / items.sort() / user.name = 'new' / Object.assign(user, ...)
// ✅ [...items, x]                          add to end
// ✅ items.filter(i => i.id !== id)         remove
// ✅ items.map(i => i.id === id ? x : i)    replace
// ✅ [...items].sort()                       sort (copy first)
// ✅ { ...user, name: 'new' }               update object
```

**Pure functions** — same input → same output, no side effects. Isolate impure operations (I/O, randomness, `Date.now()`) at system boundaries. Keep domain logic pure.

**Array methods over loops** — `map`/`filter`/`reduce` for transformations. Loops only when early termination or side effects are essential.

**Options objects** for 3+ parameters. Positional params fine for 1–2.

**Early returns** over nested conditions. Max 2 levels of nesting — extract functions beyond that:
```typescript
// ❌ if (user) { if (user.isActive) { if (user.hasPermission) { ... } } }
// ✅
if (!user) return;
if (!user.isActive) return;
if (!user.hasPermission) return;
```

**Result type** for recoverable errors:
```typescript
type Result<T, E = Error> =
  | { readonly success: true;  readonly data: T  }
  | { readonly success: false; readonly error: E };
```

**No comments** — rename or extract instead. JSDoc on public APIs only.

**Functional Light** — no fp-ts/Ramda/category theory unless the project already uses them.

---

## TypeScript Strict Mode

**Rules**:
- No `any` — use `unknown` when the type is genuinely unknown
- No type assertions (`as Type`) without a justifying comment
- `type` for data structures — with `readonly` on all properties, `ReadonlyArray` for arrays
- `interface` for behavior contracts (what must be implemented)
- No `@ts-ignore` without an explanatory comment
- Rules apply to test code as well as production code

**Schema-first at trust boundaries** (API responses, user input, external data): define the schema once, derive the type from it, import both everywhere. Never redefine the same schema in a different file.

No schema needed for: internal utility types, `Result` types, TypeScript utility types (`Partial`, `Pick`), or component props never sourced from external data.

**Branded types** for type-safe primitives:
```typescript
type UserId = string & { readonly brand: unique symbol };
// ❌ processPayment('raw-string', 100)
// ✅ processPayment('user-123' as UserId, 100 as PaymentAmount)
```

**tsconfig**: `strict: true` is the minimum. Enable additional safety flags the codebase supports — notably `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`.

---

## DDD — opt-in only

*Apply only to projects that explicitly use DDD. Do not use for simple CRUD.*

**Start simple**: begin with ubiquitous language and value objects. Add aggregates, domain events, and bounded contexts only when the domain demands it.

### Ubiquitous Language & Glossary

Maintain a glossary file (`docs/glossary.md`). All type names, function names, and test descriptions must use glossary terms. New concept → update glossary first.

```markdown
| Term        | Definition                                         |
|-------------|----------------------------------------------------|
| Occasion    | A future event that may involve gift-giving        |
| Gift Idea   | A potential gift for a specific person/occasion    |
| Contributor | A person who contributes money toward a group gift |
```

```typescript
// ✅ type GiftIdea, const addGiftIdea — domain language
// ❌ type Item, const addItem, type Entity, type Record — generic technical names
```

### Value Objects & Entities

**Value objects**: immutable, no identity, equality by value. Enforce invariants on construction.
**Entities**: stable branded ID, immutable updates via spread.

```typescript
type OccasionId = string & { readonly __brand: 'OccasionId' };
type GiftIdeaId = string & { readonly __brand: 'GiftIdeaId' };
// Compiler prevents accidental ID swapping: findGiftIdea(occasionId, giftIdeaId)
```

### Make Illegal States Unrepresentable

Use discriminated unions to prevent invalid domain states at compile time:

```typescript
// ❌ shippedAt can be set when status is 'draft'
type Order = { status: 'draft' | 'placed' | 'shipped'; shippedAt?: Date };

// ✅ invalid combinations are unrepresentable
type Order =
  | { readonly status: 'draft';   readonly items: ReadonlyArray<OrderItem> }
  | { readonly status: 'placed';  readonly items: ReadonlyArray<OrderItem>; readonly placedAt: Date }
  | { readonly status: 'shipped'; readonly items: ReadonlyArray<OrderItem>; readonly placedAt: Date; readonly shippedAt: Date; readonly trackingNumber: string };
```

TypeScript exhaustive switch catches missing cases automatically.

### Aggregates

Consistency boundary. Only the root is referenced externally. Reference other aggregates by ID, never by embedding. All invariants enforced by the root before persisting.

### Domain Events

Past tense (`OccasionCreated`, not `createOccasion`). Domain operations return new state + events:

```typescript
type DomainResult<T> = { readonly state: T; readonly events: ReadonlyArray<DomainEvent> };

const addGiftIdea = (occasion: Occasion, idea: NewGiftIdea): DomainResult<Occasion> => ({
  state: { ...occasion, giftIdeas: [...occasion.giftIdeas, { ...idea, id: createGiftIdeaId() }] },
  events: [{ type: 'GiftIdeaAdded', occasionId: occasion.id, occurredAt: new Date() }],
});
```

### Repository Pattern

See the Repository Pattern section below — repositories are the primary application of the port pattern to aggregate access.

### Bounded Contexts

Each context owns its model. Communicate via events or explicit contracts — never share internal types. Shared kernel minimal (only shared value objects like `UserId`, `Money`).

```
packages/
  occasions/     src/domain/   # Occasion, GiftIdea
  contributions/ src/domain/   # Contribution, Pledge
  shared/        src/domain/   # UserId, Money (minimal)
```

### DDD + TDD

Organise tests by domain concept, not by implementation file:
```
tests/occasions/add-gift-idea.test.ts    # ✅ domain behavior
tests/occasions/occasion-budget.test.ts  # ✅ domain behavior
# ❌ tests/gift-idea-service.test.ts     # implementation mirror
```

Test factories and test descriptions must use domain language.

### Anti-Patterns

- **Anemic domain model**: data bags with all logic in services, mutation outside the type — move behavior into pure domain functions
- **Generic technical names**: `Item`, `Entity`, `Record`, `Data` instead of glossary terms
- **Leaking domain logic**: business rules in adapters, controllers, or DB queries — keep in domain layer
- **Over-engineering**: start with glossary + value objects; add aggregates and domain events only when needed

---

## Hexagonal Architecture — opt-in only

*Apply only to projects that explicitly use hexagonal architecture.*

Dependencies point **inward**: adapters → ports → domain. Domain has zero framework or infrastructure dependencies.

**Ports** = `interface` types (what operations exist).
**Adapters** = classes/objects implementing ports for specific technologies.

The Repository Pattern section below is the primary example of ports and adapters in practice.

**Always inject dependencies via parameters** — never create implementations internally:
```typescript
// ✅
export const createOrderService = ({
  orderRepository,
  paymentGateway,
}: {
  orderRepository: OrderRepository;
  paymentGateway: PaymentGateway;
}): OrderService => ({ ... });
```

**File layout**: `domain/` (pure logic + types) · `ports/` (interfaces) · `schemas/` (shared validation) · `adapters/` (implementations) · `use-cases/` (application logic)

Schemas live in `domain/` or shared — never duplicated in adapters. Prefer factory functions over classes for services.

---

## Repository Pattern

Repositories sit at the intersection of DDD and hexagonal architecture: they give the domain collection-like access to aggregates (DDD) through a port implemented by interchangeable adapters (hexagonal).

```typescript
// Port — domain layer defines what it needs
interface OccasionRepository {
  findById(id: OccasionId): Promise<Occasion | undefined>;
  save(occasion: Occasion): Promise<void>;
}

// Adapters — infrastructure layer delivers it
class PostgresOccasionRepository implements OccasionRepository { ... }  // production
class InMemoryOccasionRepository implements OccasionRepository { ... }  // tests
```

The in-memory adapter is a test double for free — no mocking frameworks needed. Inject via parameters; never instantiate inside domain logic.

---

## Checklist

- [ ] No data mutation — spread operators for all updates
- [ ] `readonly` on all `type` properties; `ReadonlyArray` for arrays
- [ ] Pure functions; impure operations isolated at system boundaries
- [ ] Array methods over loops; max 2 nesting levels; early returns
- [ ] Options objects for 3+ parameters
- [ ] No `any`; no unexplained `as Type`
- [ ] `type` for data, `interface` for behavior contracts
- [ ] Schemas defined once, imported everywhere
- [ ] `strict: true` in tsconfig (plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` where supported)
- [ ] (DDD) Domain terms match glossary; aggregates enforce invariants
- [ ] (Hexagonal) Dependencies point inward; all injected via parameters
