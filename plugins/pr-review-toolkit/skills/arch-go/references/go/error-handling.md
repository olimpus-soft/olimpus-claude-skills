# Error Handling in Go

---

## Core Principle

In Go, errors are values. Handle them explicitly, always.

```go
// Basic pattern: if err != nil
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doing something: %w", err)
}
```

---

## Custom Errors

```go
// Sentinel errors: predefined errors for comparison
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrConflict     = errors.New("conflict")
)

// Error types: when additional context is needed
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error on field %s: %s", e.Field, e.Message)
}

// Domain error with code
type AppError struct {
    Code    string
    Message string
    Err     error // root cause
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error {
    return e.Err
}

// Factory functions for domain errors
func NewNotFoundError(resource string, id any) *AppError {
    return &AppError{
        Code:    "NOT_FOUND",
        Message: fmt.Sprintf("%s with id %v not found", resource, id),
    }
}

func NewBusinessRuleError(msg string) *AppError {
    return &AppError{
        Code:    "BUSINESS_RULE_VIOLATION",
        Message: msg,
    }
}
```

---

## Error Wrapping with fmt.Errorf

```go
// Use %w for wrapping (enables errors.Is and errors.As)
func (s *UserService) FindByID(ctx context.Context, id int64) (*User, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("finding user %d: %w", id, err)
    }
    return user, nil
}

// Chain of wrapping creates error chain
// "creating order: finding user 42: sql: no rows in result set"

// Use %v when you do NOT want the caller to inspect the cause
func (s *Service) Process() error {
    err := s.internal()
    if err != nil {
        return fmt.Errorf("processing: %v", err) // hides internal details
    }
    return nil
}
```

---

## errors.Is and errors.As

```go
// errors.Is: checks if a specific error is in the chain
if errors.Is(err, ErrNotFound) {
    // handle not found
    return nil, nil // or return default
}

if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrNotFound
}

if errors.Is(err, context.DeadlineExceeded) {
    log.Warn("request timed out")
}

// errors.As: extracts typed error from the chain
var validErr *ValidationError
if errors.As(err, &validErr) {
    // use validErr.Field, validErr.Message
    return validErr.Field, validErr.Message
}

var appErr *AppError
if errors.As(err, &appErr) {
    switch appErr.Code {
    case "NOT_FOUND":
        w.WriteHeader(http.StatusNotFound)
    case "BUSINESS_RULE_VIOLATION":
        w.WriteHeader(http.StatusUnprocessableEntity)
    default:
        w.WriteHeader(http.StatusInternalServerError)
    }
}

// WRONG: comparing directly instead of using errors.Is
if err == ErrNotFound { ... }     // WRONG: does not work with wrapped errors
if errors.Is(err, ErrNotFound) {} // CORRECT
```

---

## Error Handling Pattern in HTTP Handlers

```go
// Centralized error middleware
func ErrorMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        next.ServeHTTP(w, r)
    })
}

// Handler that returns error (pattern with adapter)
type AppHandler func(w http.ResponseWriter, r *http.Request) error

func (fn AppHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    if err := fn(w, r); err != nil {
        var appErr *AppError
        if errors.As(err, &appErr) {
            writeJSON(w, appErr.HTTPStatus(), map[string]string{
                "code":    appErr.Code,
                "message": appErr.Message,
            })
            return
        }
        // Generic error = 500
        slog.Error("unhandled error", "error", err, "path", r.URL.Path)
        writeJSON(w, http.StatusInternalServerError, map[string]string{
            "code":    "INTERNAL_ERROR",
            "message": "internal server error",
        })
    }
}
```

---

## Best Practices

```go
// Add context when propagating errors
// CORRECT: adds context at each layer
func (s *OrderService) Create(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    user, err := s.userRepo.FindByID(ctx, req.UserID)
    if err != nil {
        return nil, fmt.Errorf("finding user for order: %w", err)
    }
    // ...
}

// WRONG: returning error without context
func (s *OrderService) Create(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    user, err := s.userRepo.FindByID(ctx, req.UserID)
    if err != nil {
        return nil, err  // WRONG: caller doesn't know it was about "finding user"
    }
}

// Never silently ignore errors
result, _ := riskyOperation()  // WRONG: if error occurs, 'result' may be invalid

// If intentionally ignoring, document the reason
_ = conn.Close() // best-effort close; error logged by caller

// Log only at the highest level (handler/main), not at every layer
// WRONG: log + return err at every layer
func (s *Service) Do() error {
    err := s.repo.Save(ctx, entity)
    if err != nil {
        log.Error("failed to save", "error", err)  // log here
        return fmt.Errorf("saving: %w", err)        // AND propagate
        // result: error is logged N times
    }
}

// CORRECT: propagate errors, log in handler/entrypoint
func (s *Service) Do() error {
    if err := s.repo.Save(ctx, entity); err != nil {
        return fmt.Errorf("saving entity: %w", err)  // only propagates
    }
    return nil
}
```

---

## Panic and Recover

```go
// Panic: ONLY for unrecoverable errors (bug, impossible state)
func MustCompileRegex(pattern string) *regexp.Regexp {
    re, err := regexp.Compile(pattern)
    if err != nil {
        panic(fmt.Sprintf("invalid regex %q: %v", pattern, err))
    }
    return re
}

// Recover: at boundaries (HTTP handlers, goroutines)
func safeGo(fn func()) {
    go func() {
        defer func() {
            if r := recover(); r != nil {
                slog.Error("goroutine panicked", "panic", r, "stack", string(debug.Stack()))
            }
        }()
        fn()
    }()
}

// NEVER use panic for flow control
// NEVER use panic in libraries (return error)
// NEVER recover to silently swallow panics
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `if err == ErrX` | Does not work with wrapped errors | `errors.Is(err, ErrX)` |
| Log + return err | Error logged multiple times | Log only in handler, propagate with wrap |
| `panic()` in library | Breaks the caller | Return `error` |
| Ignoring error with `_` | Silent invalid state | Handle or document why you ignore it |
| `err.Error()` for comparison | Fragile, depends on message | Use sentinel errors or `errors.As` |
| Error without context | Impossible to trace origin | `fmt.Errorf("context: %w", err)` |
| Catch-all `recover()` | Hides bugs | Recover only at boundaries |
