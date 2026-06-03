# Go Code Review Checklist

Use during the review of each modified file. 27 checks divided into 7 categories.

---

## Error Handling (5 checks)

- [ ] **E1 — Ignored Error**: Error returned by a function being ignored with `_`? Always handle or document why you ignore it
- [ ] **E2 — Error without Wrap**: Error propagated without context (`return err`)? Use `fmt.Errorf("context: %w", err)`
- [ ] **E3 — Direct Comparison**: Error compared with `==` instead of `errors.Is()`? Does not work with wrapped errors
- [ ] **E4 — Log + Return**: Error logged AND returned in the same layer? Log only in the handler, propagate with wrap in inner layers
- [ ] **E5 — Panic in Lib**: `panic()` used in library/service code? Return `error` instead of panic

---

## Concurrency (4 checks)

- [ ] **C1 — Goroutine Leak**: Goroutine without termination mechanism (context, done channel, WaitGroup)? Ensure lifecycle
- [ ] **C2 — Data Race**: Shared state accessed by multiple goroutines without Mutex/channel? Use `-race` flag
- [ ] **C3 — Mutex Copied**: Struct with `sync.Mutex` being copied (by value)? Pass by pointer
- [ ] **C4 — Channel without Close**: Channel never closed by the producer? Receiver may block forever

---

## Security (4 checks)

- [ ] **S1 — SQL Injection**: Query built with string concatenation? Use prepared statements with `$1`, `?`
- [ ] **S2 — Exposed Secrets**: Hardcoded passwords, tokens, API keys in the code? Use env vars or secrets manager
- [ ] **S3 — Input Validation**: External input used without validation? Validate before processing
- [ ] **S4 — Path Traversal**: User input used in `os.Open()` or `filepath.Join()` without sanitization?

---

## Performance (3 checks)

- [ ] **P1 — Preallocate**: Slice growing via `append` in a loop without `make([]T, 0, cap)`? Preallocate when size is known
- [ ] **P2 — Allocation in Loop**: Heavy allocation (large struct, map) inside a hot loop? Move outside the loop or use a pool
- [ ] **P3 — Query in Loop**: Database/HTTP call inside a for? Extract to batch or IN clause

---

## Testing (3 checks)

- [ ] **T1 — Coverage**: New business logic without a corresponding test? Happy path + error paths
- [ ] **T2 — Table-Driven**: Multiple scenarios tested with separate tests instead of table-driven? Use `[]struct` + `t.Run`
- [ ] **T3 — Race Flag**: CI runs `go test` without `-race`? Always use `-race` to detect data races

---

## Code Quality (5 checks)

- [ ] **Q1 — Naming**: Non-idiomatic names (getId vs GetID, userlist vs userList)? Follow Go conventions
- [ ] **Q2 — Bloated Interface**: Interface with too many methods (>5)? Break into smaller, focused interfaces
- [ ] **Q3 — Missing Context**: Function that does I/O (DB, HTTP, file) without `context.Context`? Always propagate context
- [ ] **Q4 — init() with Side Effects**: `init()` doing I/O, connecting to database, etc.? Move to explicit constructor
- [ ] **Q5 — Logging**: Using `fmt.Println`, `log.Println` instead of `slog`? Use structured logging with slog

---

## Architecture (3 checks)

- [ ] **A1 — Repository in Handler**: Handler accessing database directly (bypassing the service)?
- [ ] **A2 — Logic in Handler**: Business rules, calculations, domain validations in the handler?
- [ ] **A3 — Circular Import**: Circular import between packages? Restructure with interfaces or extract a package

---

## How to Use

1. For each `.go` file in the diff, go through the 27 checks above
2. For each failing check, create a comment using `assets/comment.md`
3. Classify severity as described in `SKILL.md`
4. Include reference to the `arch-go` skill when applicable
5. At the end of the file, compile a summary with count by severity
