---
name: arch-frontend
description: >
  MercadoLibre frontend architecture skill — Nordic SSR framework (v9+), Andes Design System,
  Kraken auth, BFF pattern with Clean Architecture, TypeScript strict, Jest + Testing Library.
  Use as quality baseline for development, code review and analysis of MercadoLibre frontend projects.
triggers:
  - arch-frontend
  - nordic
  - andes
  - frontend architecture
  - typescript frontend
  - meli frontend
---

# Arch-Frontend Skill

Knowledge base for MercadoLibre frontend architecture using Nordic SSR, Andes UI, and Kraken.
Used as a baseline by the `explorer`, `dev-frontend`, and `review-frontend` agents.

## Communication Principles

- **Verifiability**: never present inferences as facts. Use `[Inference]` for unverified content
- **Specificity**: always cite file and line when pointing out problems
- **Actionability**: each problem must have a concrete recommendation
- Code and comments in **English**; discussions in **English**

---

## Core Concepts

### 1. Nordic SSR Framework

**Reference**: `references/nordic/ssr-patterns.md`

Nordic is MercadoLibre's internal SSR framework built on React + Express + Webpack (v9.7.x).

Key primitives:
- **Ragnar server**: main server instance combining `apiRouter` (BFF) + `appRouter` (SSR pages)
- **Nordic pages** (`app/nordic-pages/`): page-level React components, one folder per route
- **`config/default.js`**: Nordic configuration file (routing, APIs, permissions, CDN)
- **`@meli/express-server`**: MeLi Express wrapper used for the BFF layer
- **i18n**: built-in translation support via Nordic; translation files in `app/translations/`
- **SSR data fetching**: data is fetched server-side in page components before render
- **CDN**: assets are auto-uploaded to MeLi CDN on build

### 2. Project Structure

**Reference**: `references/nordic/project-structure.md`

Standard dual-layer layout:

```
app/                          # Frontend (React SSR)
  components/                 # Shared UI components
  nordic-pages/               # Route-based page components (one folder per route)
    <feature>/                #   Page component + sub-components
      __tests__/              #   Jest + Testing Library tests co-located
  server/                     # SSR server setup (app router, Kraken auth wiring)
  services/                   # Client-side API service layer (calls BFF endpoints)
  styles/                     # Global SCSS styles
  translations/               # i18n files (pt-BR, es, en...)

api/                          # BFF API layer (Express, Clean Architecture per module)
  <module>/
    application/use-cases/    # Use cases (business logic)
    domain/entities/          # Domain entities
    domain/repositories/      # Repository interfaces
    infra/controller/         # Controller (wires use cases)
    infra/repositories/       # Repository implementations (HTTP to downstream services)
    infra/router.ts           # Express Router for this module
  shared/                     # Shared middleware, services, utils
  index.ts                    # API router aggregator + global middleware chain

config/
  default.js                  # Nordic configuration (routing, API hosts, permissions)

configs/
  latest/                     # Fury environment configs (prod.json, test.json)
```

### 3. Andes Design System

**Reference**: `references/andes/components.md`

`@andes/*` is the MercadoLibre design system for web. Current version: 9.1.x.

- Import components from their individual packages: `@andes/button`, `@andes/card`, etc.
- Always prefer Andes components over raw HTML or custom-styled elements
- Never override Andes CSS directly — use the component's API (props/classNames) instead
- Andes components are SSR-compatible with Nordic

### 4. Authentication — Kraken

**Reference**: `references/bff/clean-architecture.md`

`@kraken/core` handles session, permissions, and attributes for back-office apps.

- **`krakenSessionResolver()`**: middleware that resolves the user session from cookie `session_id`
- **`kraken.releaseOnMiddleend()`**: middleware that enforces application-level authorization
- **`apiAuthorization()`**: per-module permission check using `adminFeaturesPermissions` config
- Always apply Kraken middleware **before** any route handler that requires authentication
- Authorization config lives in `config/default.js` under `adminFeaturesPermissions`

---

## BFF Layer (Clean Architecture)

### 5. Clean Architecture in the API Layer

**Reference**: `references/bff/clean-architecture.md`

Each API module follows strict Clean Architecture:

```
module/
  application/use-cases/   # Pure business logic. No HTTP, no DB, no framework.
  domain/entities/         # Domain objects (plain TypeScript classes/interfaces)
  domain/repositories/     # Repository interfaces (contracts only)
  infra/controller/        # Wires use cases. No business logic.
  infra/repositories/      # Implements repository interfaces (HTTP clients, DB)
  infra/router.ts          # Express routes → controller methods
```

**Rules:**
- Use cases receive repositories via constructor injection
- Controllers instantiate use cases at the bottom of the file (manual DI)
- Repositories use **singleton pattern** (`getInstance()`) — never instantiate per request
- External HTTP calls go through `ExternalApiService` — one instance per repository
- Route handlers are thin: validate input → call controller → send response

### 6. Input Validation

- Use `@meli/input-validation` middleware for all routes that receive query params or body
- Define schemas in `infra/schemas/` within each module
- Routes without parameters still benefit from validation middleware (blocks unexpected input)
- Validation errors should return `400 Bad Request`

### 7. Error Handling

- Centralize error handling with a shared `handleError` middleware
- Use a `DomainError` base class with typed subclasses per error scenario
- Never catch just to re-throw a generic error (loses original stack)
- Route handlers: `try { ... } catch (err) { handleError(err, res) }`
- Never disable ESLint rules to avoid fixing error handling issues

### 8. Context Propagation

- Use `AsyncLocalStorage` via `ContextManager` for request context (auth headers, tracing)
- All downstream HTTP calls must include `x-auth` and `x-api-scope` headers from context
- Apply `contextMiddleware` globally on all API routes

---

## TypeScript Conventions

**Reference**: `references/typescript/conventions.md`

- **Strict TypeScript**: no `any` unless absolutely unavoidable — use `unknown` + narrowing
- **Type-only imports**: `import type { Foo }` for type-only dependencies
- **Naming**: camelCase for variables/functions, PascalCase for classes/components/types, kebab-case for files
- **DTOs**: define request/response DTOs explicitly — never use `req.body as SomeType` without validation
- **Express typing**: use `Request<Params, ResBody, ReqBody, Query>` generics on route handlers
- **Formidable**: type results with `Fields` and `Files` from formidable types

---

## Testing

**Reference**: `references/testing/testing-patterns.md`

- **Framework**: Jest + ts-jest + Testing Library (`@testing-library/react`)
- **Co-location**: test files in `__tests__/` directories next to the code they test
- **Coverage targets**: use cases, controllers, critical middleware (auth, error handler)
- **Component tests**: React Testing Library — test behavior, not implementation
- **BFF tests**: mock downstream HTTP with `jest.mock()` or `nock`; never mock `@meli/express-server` internals
- **Auth tests**: always test authorization middleware with both authorized and unauthorized cases
- **Linting**: ESLint 9 flat config + `@meli-lint/eslint-config-base-ts`, Prettier, Stylelint (for SCSS)

---

## Essential Commands

| Category | Command | Purpose |
|----------|---------|---------|
| Dev | `npm run dev` | Start Nordic dev server with Fast Refresh |
| Build | `npm run build` | Production build + CDN upload |
| Test | `npm test` | Run Jest test suite |
| Test (watch) | `npm run test:watch` | Jest in watch mode |
| Lint | `npm run lint` | ESLint + Stylelint |
| Type check | `npx tsc --noEmit` | TypeScript type check without emit |

---

## Recommended Workflow

```
UNDERSTAND → DESIGN (contracts) → TEST → IMPLEMENT → VALIDATE → REVIEW
```

1. **Understand**: read `config/default.js`, `context.md`, existing module patterns
2. **Design**: define DTOs, repository interfaces, use case signatures before coding
3. **Test**: write Jest tests for use cases and critical route handlers first
4. **Implement**: follow Clean Architecture — use case logic, then infra, then route
5. **Validate**: `npm test` + `npm run lint` + `npx tsc --noEmit`
6. **Review**: self-review against this skill baseline

---

## References

### Nordic
- `references/nordic/ssr-patterns.md` — Ragnar server, SSR data fetching, i18n, CDN
- `references/nordic/project-structure.md` — Dual-layer layout, Nordic pages, config

### Andes
- `references/andes/components.md` — Design system usage, component patterns, SSR compatibility

### BFF
- `references/bff/clean-architecture.md` — Clean Architecture layers, Kraken auth, error handling, context propagation

### TypeScript
- `references/typescript/conventions.md` — Strict TypeScript, naming, DTOs, Express typing

### Testing
- `references/testing/testing-patterns.md` — Jest, Testing Library, co-location, auth tests
