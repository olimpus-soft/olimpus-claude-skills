# Go Code Review Comment Template

Use this template for EACH issue found during the review.
Fill in all `{...}` placeholders with specific information from the diff.

---

## Base Template

```markdown
---

**File:** `{filepath}`
**Lines:** {start_line}-{end_line}
**Category:** {category}
**Severity:** {severity}

**Issue:**
{clear and objective description of the problem in 1-2 sentences}

**Current Code:**
```go
{problematic code extracted from the diff — exactly as it appears}
```

**Suggested Code:**
```go
{corrected code — must compile and follow arch-go standards}
```

**Rationale:**
{technical explanation of why this is a problem}
{impact if not fixed: performance, security, maintainability}

**Reference:**
- Arch-Go Skill: [{file name}](../arch-go/{path})
{other references if applicable}
```

---

## Examples of Filled-in Comments

### Example 1 — Ignored Error (HIGH)

```markdown
---

**File:** `internal/service/order_service.go`
**Lines:** 45-48
**Category:** Error Handling
**Severity:** HIGH

**Issue:**
The error from `repo.Save()` is being ignored with `_`. If persistence fails,
the service returns success with inconsistent data.

**Current Code:**
```go
_ = s.repo.Save(ctx, order)
return order, nil
```

**Suggested Code:**
```go
if err := s.repo.Save(ctx, order); err != nil {
    return nil, fmt.Errorf("saving order: %w", err)
}
return order, nil
```

**Rationale:**
Ignoring persistence errors can cause silent data loss. The caller
believes the operation succeeded when the data was not saved.

**Reference:**
- Arch-Go Skill: [Error Handling](../arch-go/references/go/error-handling.md)
```

---

### Example 2 — Goroutine Leak (CRIT)

```markdown
---

**File:** `internal/worker/processor.go`
**Lines:** 23-35
**Category:** Concurrency
**Severity:** CRIT

**Issue:**
Goroutine started without lifecycle control. If the context is cancelled before
the channel is written, the goroutine hangs indefinitely.

**Current Code:**
```go
go func() {
    result := heavyComputation(data)
    ch <- result  // blocks if nobody reads
}()
```

**Suggested Code:**
```go
go func() {
    result := heavyComputation(data)
    select {
    case ch <- result:
    case <-ctx.Done():
        return
    }
}()
```

**Rationale:**
Goroutine leak causes progressive memory leak. In production with high throughput,
this can exhaust the container's memory within hours or days.

**Reference:**
- Arch-Go Skill: [Concurrency](../arch-go/references/concurrency/goroutines-channels.md)
```

---

### Example 3 — Non-Idiomatic Naming (LOW)

```markdown
---

**File:** `internal/handler/user_handler.go`
**Lines:** 12-15
**Category:** Code Quality
**Severity:** LOW

**Issue:**
Function `GetUserById` uses non-idiomatic naming for Go. Acronyms must be
all uppercase or all lowercase.

**Current Code:**
```go
func (h *UserHandler) GetUserById(w http.ResponseWriter, r *http.Request) {
```

**Suggested Code:**
```go
func (h *UserHandler) GetUserByID(w http.ResponseWriter, r *http.Request) {
```

**Rationale:**
Go conventions require that acronyms like ID, HTTP, URL be all uppercase
when exported. `Id` violates this convention and is flagged by `golangci-lint`.

**Reference:**
- Arch-Go Skill: [Go Idioms](../arch-go/references/go/idioms.md)
```

---

## Positive Points Section (Always Include)

At the end of the review for each file:

```markdown
### Positive Points

1. {well-implemented aspect — be specific}
2. {good practice followed}
3. {quality worth highlighting}
```
