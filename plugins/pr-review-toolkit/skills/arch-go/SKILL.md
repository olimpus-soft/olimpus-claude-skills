---
name: arch-go
description: >
  Go architecture skill — idiomatic Go 1.22+ patterns, error handling,
  concurrency (goroutines, channels, errgroup), testing with table-driven tests
  and testify/mockery, HTTP patterns (net/http, Gin), and project structure.
  Current as of Go 1.26 (February 2026). Use as quality baseline for development,
  code review and analysis of Go projects.
triggers:
  - arch-go
  - go architecture
  - go best practices
  - golang patterns
  - modern go
---

# Arch-Go Skill

Knowledge base for modern idiomatic Go architecture and patterns.
Used as a baseline by the `explorer`, `dev-go` and `review-go` agents.

## Communication Principles

- **Verifiability**: never present inferences as facts. Use `[Inference]` for unverified content
- **Specificity**: always cite the file and line when pointing out problems
- **Actionability**: each problem must have a concrete recommendation
- Code and comments in **English**; discussions in **English**

---

## Core Concepts

### 1. Go Idioms

**Reference**: `references/go/idioms.md`

Mandatory patterns:
- **Naming conventions**: PascalCase exported, camelCase unexported, consistent acronyms
- **Small interfaces** (1-3 methods), defined where they are consumed
- **Constructor functions**: `NewXxx()` returns struct or pointer
- **Functional options** for complex configuration
- **Context propagation**: `context.Context` always as the first parameter
- **Iterators** (Go 1.23+): `iter.Seq[V]` / `iter.Seq2[K,V]` for lazy sequences with `for range`
- **Useful zero values**: design structs so the zero value is valid
- **Accept interfaces, return structs**

### 2. Error Handling

**Reference**: `references/go/error-handling.md`

- `if err != nil` on every function return that can fail
- **Error wrapping** with `fmt.Errorf("context: %w", err)`
- **Sentinel errors** (`var ErrNotFound = errors.New(...)`) for comparison
- **Error types** with `Unwrap()` for errors with context
- `errors.Is()` and `errors.As()` for inspecting error chains
- Never silently ignore errors (`_, _ = ...`)
- Log only at the highest level (handler/main), propagate errors in inner layers

### 3. Concurrency

**Reference**: `references/concurrency/goroutines-channels.md`

- **Goroutines** with controlled lifecycle (context, WaitGroup, errgroup)
- **Channels** for communication between goroutines (close on the producer side)
- **errgroup** for fan-out/fan-in with error handling
- **WaitGroup.Go** (Go 1.25+): simplified goroutine spawning without manual Add/Done
- **sync.Mutex/RWMutex** for shared state
- **sync.Once** for thread-safe lazy initialization
- Never `time.Sleep` for synchronization
- Services should be stateless (no mutable state in service structs)

---

## HTTP Patterns

### 4. HTTP API

**Reference**: `references/http/http-patterns.md`

- **net/http with ServeMux** (Go 1.22+): native pattern routing with method + path params
- **Handler structs** with dependencies injected via constructor
- **Middleware chain**: logging, recovery, request ID, auth
- **Centralized JSON helpers**: `writeJSON`, `writeError`, `decodeJSON`
- **Graceful shutdown** with `signal.NotifyContext` and `srv.Shutdown`
- **Timeouts** configured: ReadTimeout, WriteTimeout, IdleTimeout
- Popular alternative: **Gin** for projects needing integrated binding/validation

### 5. Validation

- `go-playground/validator` for struct validation with tags
- Validation in the handler before delegating to the service
- Validation errors return 400 Bad Request with details

---

## Testing

### 6. Testing Patterns

**Reference**: `references/testing/testing-patterns.md`

- **Table-driven tests**: idiomatic Go pattern with `[]struct` + `t.Run`
- **testify**: `assert` for verifications, `require` for fatal preconditions
- **Mocks via interfaces**: manual mocks or generated with mockery
- **httptest**: `httptest.NewRequest` + `httptest.NewRecorder` for handlers
- **t.Helper()** for setup functions
- **t.Cleanup()** for automatic teardown
- **t.Parallel()** for independent tests
- **testing/synctest** (Go 1.24+): virtual time for testing timers, retries, TTL — no real `time.Sleep`
- `-race` flag mandatory in CI

---

## Architecture

### 7. Project Structure

**Reference**: `references/architecture/project-structure.md`

Mandatory separation:
```
cmd/         -> Entry point, wiring
internal/
  handler/   -> HTTP handlers (input layer)
  service/   -> Business logic (domain)
  repository/-> Data access
  domain/    -> Domain entities
  dto/       -> Request/Response structs
  config/    -> Configuration
  platform/  -> Shared infrastructure (database, cache)
pkg/         -> Public reusable code
```

- **Handler**: deserializes request, validates, delegates to service, serializes response. Zero business logic.
- **Service**: business logic, coordinates repositories, transforms domain <-> DTO
- **Repository**: data access, SQL queries, no business logic
- **internal/** for private code, **pkg/** for reusable code
- **Manual DI** via constructors in main.go (no DI framework)

### 8. Logging

- Use **log/slog** (Go 1.21+) — structured logging from the stdlib
- `slog.Info()`, `slog.Warn()`, `slog.Error()` with key-value attributes
- Never `fmt.Println()` or `log.Println()` in production
- Request ID in logs via context values
- Log in handler/main, not in inner layers (propagate errors)

---

## Essential Tools

| Category | Tool | Purpose | Command |
|----------|------|---------|---------|
| Build | go build | Compilation | `go build ./...` |
| Test | go test | Test framework | `go test ./...` |
| Test | testify | Assertions + mocks | (via dependency) |
| Mock | mockery | Mock generation | `mockery` |
| Lint | golangci-lint | Aggregated linter | `golangci-lint run` |
| Vet | go vet | Built-in static analysis | `go vet ./...` |
| Format | gofmt/goimports | Mandatory formatting | `gofmt -w .` |
| Deps | go mod | Module management | `go mod tidy` |
| Race | go test -race | Data race detector | `go test -race ./...` |
| Vuln | govulncheck | Vulnerability scanner | `govulncheck ./...` |
| Docs | godoc | Documentation | `go doc` |

---

## Recommended Workflow

```
DESIGN -> TYPE (interfaces) -> TEST -> IMPLEMENT -> VALIDATE -> REVIEW
```

1. **Design**: define interfaces and DTOs (request/response structs)
2. **Type**: domain structs, service/repository interfaces
3. **Test**: table-driven tests with testify before implementing
4. **Implement**: code that passes the tests
5. **Validate**: `go test -race ./...` + `golangci-lint run`
6. **Review**: self-review against this skill

---

## References

### Go Core
- `references/go/idioms.md` — Naming, interfaces, constructors, context, zero values
- `references/go/error-handling.md` — Error wrapping, sentinel errors, errors.Is/As

### Concurrency
- `references/concurrency/goroutines-channels.md` — Goroutines, channels, errgroup, sync primitives

### HTTP
- `references/http/http-patterns.md` — net/http, handlers, middleware, Gin, graceful shutdown

### Testing
- `references/testing/testing-patterns.md` — Table-driven tests, testify, mockery, httptest

### Architecture
- `references/architecture/project-structure.md` — cmd/internal/pkg, layers, manual DI
