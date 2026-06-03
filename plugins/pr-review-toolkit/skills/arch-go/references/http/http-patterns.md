# HTTP Patterns in Go

---

## net/http (Standard Library — Go 1.22+)

Go 1.22 added pattern routing to `http.ServeMux`, making the use of third-party routers
less necessary for many cases.

```go
// Routing with method and path params (Go 1.22+)
mux := http.NewServeMux()

mux.HandleFunc("GET /api/v1/users", h.ListUsers)
mux.HandleFunc("GET /api/v1/users/{id}", h.GetUser)
mux.HandleFunc("POST /api/v1/users", h.CreateUser)
mux.HandleFunc("PUT /api/v1/users/{id}", h.UpdateUser)
mux.HandleFunc("DELETE /api/v1/users/{id}", h.DeleteUser)

// Extract path param
func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
    idStr := r.PathValue("id")
    id, err := strconv.ParseInt(idStr, 10, 64)
    if err != nil {
        writeError(w, http.StatusBadRequest, "invalid user id")
        return
    }

    user, err := h.service.FindByID(r.Context(), id)
    if err != nil {
        handleError(w, err)
        return
    }

    writeJSON(w, http.StatusOK, user)
}
```

---

## Handler Pattern

```go
// Handler struct with injected dependencies
type UserHandler struct {
    service UserService
    logger  *slog.Logger
}

func NewUserHandler(service UserService, logger *slog.Logger) *UserHandler {
    return &UserHandler{service: service, logger: logger}
}

// RegisterRoutes centralizes route definition
func (h *UserHandler) RegisterRoutes(mux *http.ServeMux) {
    mux.HandleFunc("GET /api/v1/users/{id}", h.GetUser)
    mux.HandleFunc("POST /api/v1/users", h.CreateUser)
    mux.HandleFunc("GET /api/v1/users", h.ListUsers)
    mux.HandleFunc("PUT /api/v1/users/{id}", h.UpdateUser)
    mux.HandleFunc("DELETE /api/v1/users/{id}", h.DeleteUser)
}

// Complete handler with validation, error handling, and response
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req dto.CreateUserRequest
    if err := decodeJSON(r, &req); err != nil {
        writeError(w, http.StatusBadRequest, "invalid request body")
        return
    }

    if err := validate(req); err != nil {
        writeError(w, http.StatusBadRequest, err.Error())
        return
    }

    user, err := h.service.Create(r.Context(), req)
    if err != nil {
        handleError(w, err)
        return
    }

    writeJSON(w, http.StatusCreated, user)
}
```

---

## JSON Helpers

```go
func writeJSON(w http.ResponseWriter, status int, data any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    if err := json.NewEncoder(w).Encode(data); err != nil {
        slog.Error("encoding response", "error", err)
    }
}

func writeError(w http.ResponseWriter, status int, message string) {
    writeJSON(w, status, map[string]string{
        "error":   http.StatusText(status),
        "message": message,
    })
}

func decodeJSON[T any](r *http.Request, dest *T) error {
    dec := json.NewDecoder(r.Body)
    dec.DisallowUnknownFields()
    if err := dec.Decode(dest); err != nil {
        return fmt.Errorf("decoding request body: %w", err)
    }
    return nil
}

// Centralized error handler
func handleError(w http.ResponseWriter, err error) {
    var appErr *AppError
    if errors.As(err, &appErr) {
        switch appErr.Code {
        case "NOT_FOUND":
            writeError(w, http.StatusNotFound, appErr.Message)
        case "CONFLICT":
            writeError(w, http.StatusConflict, appErr.Message)
        case "BUSINESS_RULE_VIOLATION":
            writeError(w, http.StatusUnprocessableEntity, appErr.Message)
        default:
            writeError(w, http.StatusInternalServerError, "internal error")
        }
        return
    }
    slog.Error("unhandled error", "error", err)
    writeError(w, http.StatusInternalServerError, "internal error")
}
```

---

## Middleware

```go
// Middleware signature: func(next http.Handler) http.Handler
type Middleware func(http.Handler) http.Handler

// Logging middleware
func LoggingMiddleware(logger *slog.Logger) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

            next.ServeHTTP(wrapped, r)

            logger.Info("request",
                "method", r.Method,
                "path", r.URL.Path,
                "status", wrapped.statusCode,
                "duration", time.Since(start),
                "remote_addr", r.RemoteAddr,
            )
        })
    }
}

// Recovery middleware (panic -> 500)
func RecoveryMiddleware(logger *slog.Logger) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            defer func() {
                if rec := recover(); rec != nil {
                    logger.Error("panic recovered",
                        "panic", rec,
                        "path", r.URL.Path,
                        "stack", string(debug.Stack()),
                    )
                    writeError(w, http.StatusInternalServerError, "internal server error")
                }
            }()
            next.ServeHTTP(w, r)
        })
    }
}

// Request ID middleware
func RequestIDMiddleware() Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            requestID := r.Header.Get("X-Request-ID")
            if requestID == "" {
                requestID = uuid.NewString()
            }
            ctx := context.WithValue(r.Context(), requestIDKey, requestID)
            w.Header().Set("X-Request-ID", requestID)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// Middleware chain
func Chain(handler http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        handler = middlewares[i](handler)
    }
    return handler
}

// Usage
srv := &http.Server{
    Addr: ":8080",
    Handler: Chain(mux,
        RecoveryMiddleware(logger),
        RequestIDMiddleware(),
        LoggingMiddleware(logger),
    ),
}
```

---

## Response Writer Wrapper

```go
type responseWriter struct {
    http.ResponseWriter
    statusCode int
    written    bool
}

func (w *responseWriter) WriteHeader(code int) {
    if !w.written {
        w.statusCode = code
        w.written = true
    }
    w.ResponseWriter.WriteHeader(code)
}
```

---

## Request Validation

```go
// Using go-playground/validator
import "github.com/go-playground/validator/v10"

var validate = validator.New()

type CreateUserRequest struct {
    Name  string `json:"name" validate:"required,min=2,max=100"`
    Email string `json:"email" validate:"required,email"`
    Age   int    `json:"age" validate:"gte=0,lte=150"`
}

func validateRequest(req any) error {
    if err := validate.Struct(req); err != nil {
        var validationErrors validator.ValidationErrors
        if errors.As(err, &validationErrors) {
            messages := make([]string, 0, len(validationErrors))
            for _, e := range validationErrors {
                messages = append(messages, fmt.Sprintf("%s: %s", e.Field(), e.Tag()))
            }
            return fmt.Errorf("validation failed: %s", strings.Join(messages, ", "))
        }
        return err
    }
    return nil
}
```

---

## Graceful Shutdown

```go
func main() {
    srv := &http.Server{
        Addr:         ":8080",
        Handler:      mux,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Start server in goroutine
    go func() {
        slog.Info("server starting", "addr", srv.Addr)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            slog.Error("server error", "error", err)
            os.Exit(1)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    slog.Info("shutting down server...")

    // Give outstanding requests time to complete
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        slog.Error("server forced shutdown", "error", err)
    }

    slog.Info("server stopped")
}
```

---

## Gin (Popular Framework)

```go
// When to use Gin: projects that need rich middleware,
// automatic binding, and integrated validation

import "github.com/gin-gonic/gin"

func setupRouter(svc UserService) *gin.Engine {
    r := gin.Default() // includes Logger and Recovery middlewares

    api := r.Group("/api/v1")
    {
        api.GET("/users/:id", getUser(svc))
        api.POST("/users", createUser(svc))
        api.GET("/users", listUsers(svc))
    }

    return r
}

func getUser(svc UserService) gin.HandlerFunc {
    return func(c *gin.Context) {
        id, err := strconv.ParseInt(c.Param("id"), 10, 64)
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
            return
        }

        user, err := svc.FindByID(c.Request.Context(), id)
        if err != nil {
            handleGinError(c, err)
            return
        }

        c.JSON(http.StatusOK, user)
    }
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Business logic in handler | Not testable without HTTP | Move to service |
| Global `http.DefaultServeMux` | Global state, unsafe | Create `http.NewServeMux()` |
| No timeout in Server | Hanging connections | Configure Read/Write/IdleTimeout |
| No graceful shutdown | Requests cut during deploy | Use `signal.NotifyContext` + `srv.Shutdown` |
| No recovery middleware | Panic crashes the server | Add recovery middleware |
| No request ID | Impossible to trace requests | Request ID middleware |
| `context.Background()` in handler | Loses timeout and cancellation | Use `r.Context()` |
