# Nordic Project Structure

Standard directory layout for MercadoLibre Nordic SSR applications with BFF pattern.

---

## Full Reference Structure

```
project-root/
├── api/                          # BFF API layer (Express, Clean Architecture)
│   ├── index.ts                  # API Router aggregator + global middleware chain
│   ├── <module>/                 # One folder per domain feature
│   │   ├── application/
│   │   │   └── use-cases/        # Use cases: pure business logic
│   │   ├── domain/
│   │   │   ├── entities/         # Domain objects (plain TypeScript)
│   │   │   └── repositories/     # Repository interfaces (contracts)
│   │   └── infra/
│   │       ├── controller/       # Wires use cases, no business logic
│   │       ├── repositories/     # Implements domain interfaces (HTTP, DB)
│   │       ├── schemas/          # Input validation schemas (@meli/input-validation)
│   │       └── router.ts         # Express Router for this module
│   └── shared/                   # Cross-module shared code
│       ├── domain/
│       │   └── errors/           # DomainError base + typed subclasses
│       ├── infra/
│       │   ├── middleware/        # contextMiddleware, errorHandler, inputValidator
│       │   └── services/         # ExternalApiService (HTTP client wrapper)
│       └── utils/                # ContextManager (AsyncLocalStorage), resolve helpers
│
├── app/                          # Frontend (React SSR with Nordic)
│   ├── components/               # Shared UI components across pages
│   │   └── layouts/              # Layout wrappers (header, nav, content)
│   ├── nordic-pages/             # Page-level components (one folder = one route)
│   │   └── <feature>/
│   │       ├── index.tsx         # Page root component
│   │       ├── components/       # Page-specific sub-components
│   │       └── __tests__/        # Jest + Testing Library tests
│   ├── server/
│   │   └── index.ts              # SSR server setup (appRouter + Kraken wiring)
│   ├── services/                 # Client-side API service layer (calls BFF)
│   ├── styles/                   # Global SCSS
│   └── translations/             # i18n JSON files (pt-BR.json, es.json, en.json)
│
├── config/
│   └── default.js                # Nordic config (APIs, permissions, storage, routing)
│
├── configs/
│   └── latest/                   # Fury environment configs
│       ├── prod.json
│       └── test.json
│
├── mocks/                        # API mocks for local development
├── tests/                        # Server-side unit tests (alternative location)
├── types/                        # Global TypeScript type declarations (.d.ts)
├── utils/                        # Global utility functions
├── vendor/                       # Vendored dependencies (e.g., xlsx.tgz)
│
├── index.ts                      # Entry point: loads dotenv, newrelic, babel → init.ts
├── init.ts                       # Creates Ragnar server with apiRouter + appRouter
├── newrelic.js                   # New Relic configuration
├── package.json
├── tsconfig.json
├── eslint.config.mjs             # ESLint 9 flat config
├── .stylelintrc                  # Stylelint config for SCSS
└── Dockerfile                    # distroless-node:24-mini
```

---

## Key Conventions

### API Module Layout

Every feature module in `api/` must follow Clean Architecture strictly:

| Layer | Allowed dependencies | Forbidden |
|-------|---------------------|-----------|
| `domain/` | Nothing (pure TypeScript) | Express, HTTP, DB |
| `application/` | `domain/` only | Express, HTTP, infra |
| `infra/` | `application/`, `domain/`, `shared/` | Direct DB in controllers |

### Shared Module

The `api/shared/` module is for cross-cutting concerns only:
- `DomainError` hierarchy — one class per error type
- `handleError` middleware — maps DomainError/AxiosError/unknown to HTTP responses
- `ContextManager` — `AsyncLocalStorage` wrapper for request context
- `ExternalApiService` — HTTP client wrapper (Nordic restclient or axios)

### Frontend Page Convention

Each page in `app/nordic-pages/` maps to a URL route configured in `config/default.js`.
Page folders should be self-contained: component + sub-components + tests in the same tree.

### Test Co-location

```
app/nordic-pages/my-feature/
  index.tsx
  components/
    SearchBox.tsx
    SearchBox.test.tsx    ← co-located OR in __tests__/
  __tests__/
    index.test.tsx
```

Both patterns (co-located and `__tests__/` folder) are acceptable, but be consistent within a module.

---

## What Belongs Where

| Code type | Location |
|-----------|----------|
| HTTP route definitions | `api/<module>/infra/router.ts` |
| Business logic | `api/<module>/application/use-cases/` |
| Domain entities | `api/<module>/domain/entities/` |
| Repository interfaces | `api/<module>/domain/repositories/` |
| HTTP calls to downstream services | `api/<module>/infra/repositories/` |
| Input validation schemas | `api/<module>/infra/schemas/` |
| React page components | `app/nordic-pages/<feature>/` |
| Shared UI components | `app/components/` |
| Calls from frontend to BFF | `app/services/` |
| Global SCSS | `app/styles/` |
| Translations | `app/translations/` |
| Global types | `types/` |
| Global utils | `utils/` |
