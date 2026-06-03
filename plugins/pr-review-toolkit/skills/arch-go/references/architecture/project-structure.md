# Go Project Structure

---

## Recommended Layout (Services/APIs)

```
myapp/
├── cmd/
│   └── myapp/
│       └── main.go              # Entry point, wiring, startup
├── internal/                     # Private code (not importable externally)
│   ├── handler/                  # HTTP handlers (input layer)
│   │   ├── user_handler.go
│   │   ├── user_handler_test.go
│   │   └── middleware.go
│   ├── service/                  # Business logic (domain)
│   │   ├── user_service.go
│   │   └── user_service_test.go
│   ├── repository/               # Data access
│   │   ├── user_repository.go
│   │   └── user_repository_test.go
│   ├── domain/                   # Domain entities and value objects
│   │   ├── user.go
│   │   └── order.go
│   ├── dto/                      # Request/Response structs
│   │   ├── user_request.go
│   │   └── user_response.go
│   ├── config/                   # Application configuration
│   │   └── config.go
│   └── platform/                 # Shared infrastructure (database, cache, logger)
│       ├── database/
│       │   └── postgres.go
│       ├── cache/
│       │   └── redis.go
│       └── logger/
│           └── logger.go
├── pkg/                          # Reusable code (importable by other projects)
│   └── httputil/
│       └── response.go
├── migrations/                   # SQL migrations
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
├── api/                          # OpenAPI specs, protobuf definitions
│   └── openapi.yaml
├── go.mod
├── go.sum
├── Makefile
├── Dockerfile
└── .golangci.yml
```

---

## Layer Responsibilities

### cmd/ - Entry Point

```go
// cmd/myapp/main.go
package main

import (
    "context"
    "log/slog"
    "net/http"
    "os"
    "os/signal"
    "syscall"

    "myapp/internal/config"
    "myapp/internal/handler"
    "myapp/internal/platform/database"
    "myapp/internal/repository"
    "myapp/internal/service"
)

func main() {
    // 1. Load configuration
    cfg, err := config.Load()
    if err != nil {
        slog.Error("loading config", "error", err)
        os.Exit(1)
    }

    // 2. Infrastructure setup
    db, err := database.Connect(cfg.DatabaseURL)
    if err != nil {
        slog.Error("connecting to database", "error", err)
        os.Exit(1)
    }
    defer db.Close()

    // 3. Dependency wiring (manual, without DI framework)
    userRepo := repository.NewUserRepository(db)
    userSvc := service.NewUserService(userRepo)
    userHandler := handler.NewUserHandler(userSvc)

    // 4. Route setup
    mux := http.NewServeMux()
    userHandler.RegisterRoutes(mux)

    // 5. Graceful shutdown
    srv := &http.Server{Addr: cfg.Port, Handler: mux}

    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
    defer stop()

    go func() {
        slog.Info("server starting", "port", cfg.Port)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            slog.Error("server error", "error", err)
        }
    }()

    <-ctx.Done()
    slog.Info("shutting down gracefully")
    srv.Shutdown(context.Background())
}
```

### internal/handler/ - HTTP Layer

```go
// Responsibilities:
// 1. Deserialize request (JSON, path params, query params)
// 2. Validate input
// 3. Delegate to service
// 4. Serialize response

type UserHandler struct {
    service UserService // interface, not implementation
}

func NewUserHandler(service UserService) *UserHandler {
    return &UserHandler{service: service}
}

func (h *UserHandler) RegisterRoutes(mux *http.ServeMux) {
    mux.HandleFunc("GET /api/v1/users/{id}", h.GetUser)
    mux.HandleFunc("POST /api/v1/users", h.CreateUser)
    mux.HandleFunc("GET /api/v1/users", h.ListUsers)
}

// Handler MUST NOT contain business logic
// Handler MUST NOT access repository directly
```

### internal/service/ - Business Logic

```go
// Responsibilities:
// 1. Implement business rules
// 2. Coordinate repositories
// 3. Convert domain -> DTO (or vice versa)
// 4. Publish events

type UserService struct {
    repo   UserRepository // interface
    logger *slog.Logger
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{
        repo:   repo,
        logger: slog.Default(),
    }
}

func (s *UserService) Create(ctx context.Context, req dto.CreateUserRequest) (*dto.UserResponse, error) {
    // Business rule: unique email
    exists, err := s.repo.ExistsByEmail(ctx, req.Email)
    if err != nil {
        return nil, fmt.Errorf("checking email: %w", err)
    }
    if exists {
        return nil, NewConflictError("email already registered")
    }

    user := domain.NewUser(req.Name, req.Email)
    if err := s.repo.Save(ctx, user); err != nil {
        return nil, fmt.Errorf("saving user: %w", err)
    }

    return dto.UserResponseFrom(user), nil
}
```

### internal/repository/ - Data Access

```go
// Responsibilities:
// 1. CRUD operations
// 2. SQL queries
// 3. Mapping DB rows -> domain entities
// NO business logic

type UserRepository struct {
    db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
    return &UserRepository{db: db}
}

func (r *UserRepository) FindByID(ctx context.Context, id int64) (*domain.User, error) {
    var user domain.User
    err := r.db.QueryRowContext(ctx,
        "SELECT id, name, email, created_at FROM users WHERE id = $1", id,
    ).Scan(&user.ID, &user.Name, &user.Email, &user.CreatedAt)

    if errors.Is(err, sql.ErrNoRows) {
        return nil, ErrNotFound
    }
    if err != nil {
        return nil, fmt.Errorf("querying user: %w", err)
    }
    return &user, nil
}
```

### internal/domain/ - Domain Entities

```go
// Pure entities, no infrastructure dependency
type User struct {
    ID        int64
    Name      string
    Email     string
    Active    bool
    CreatedAt time.Time
    UpdatedAt time.Time
}

func NewUser(name, email string) *User {
    now := time.Now()
    return &User{
        Name:      name,
        Email:     email,
        Active:    true,
        CreatedAt: now,
        UpdatedAt: now,
    }
}

func (u *User) Deactivate() {
    u.Active = false
    u.UpdatedAt = time.Now()
}
```

### internal/dto/ - Data Transfer Objects

```go
// Request structs with validation tags
type CreateUserRequest struct {
    Name  string `json:"name" validate:"required,min=2,max=100"`
    Email string `json:"email" validate:"required,email"`
}

// Response structs - projects only what is needed
type UserResponse struct {
    ID        int64  `json:"id"`
    Name      string `json:"name"`
    Email     string `json:"email"`
    CreatedAt string `json:"created_at"`
}

func UserResponseFrom(u *domain.User) *UserResponse {
    return &UserResponse{
        ID:        u.ID,
        Name:      u.Name,
        Email:     u.Email,
        CreatedAt: u.CreatedAt.Format(time.RFC3339),
    }
}
```

---

## internal/ vs pkg/

```
internal/  -> PRIVATE code of the module. Go prevents import by other modules.
             Use for: handlers, services, repositories, domain, config.

pkg/       -> REUSABLE PUBLIC code.
             Use for: generic utilities, HTTP helpers, formatters.
             Rule: only put in pkg/ if another project could use it.
```

---

## Dependency Injection (Manual)

```go
// Idiomatic Go: manual DI via constructors (without framework)
// Wiring is done in main.go

// CORRECT: constructor receives dependencies
func NewOrderService(
    orderRepo OrderRepository,
    userRepo UserRepository,
    paymentGW PaymentGateway,
    logger *slog.Logger,
) *OrderService {
    return &OrderService{
        orderRepo: orderRepo,
        userRepo:  userRepo,
        paymentGW: paymentGW,
        logger:    logger,
    }
}

// WRONG: service creates its own dependencies
func NewOrderService() *OrderService {
    db := database.Connect()           // coupled
    repo := repository.NewOrderRepo(db) // not testable
    return &OrderService{repo: repo}
}

// For large projects: consider Wire (google/wire) for DI code generation
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Everything in one package | Circular imports, low cohesion | Separate by responsibility |
| Repository in handler | Bypasses business logic | Always go through the service |
| Domain entity as JSON response | Leaks internal fields | Use a separate DTO |
| `init()` for wiring | Makes tests harder, unpredictable order | Wire in main.go |
| Packages by technical type (`models/`, `utils/`) | Low cohesion, high coupling | Packages by feature or layer |
| Circular import | Compilation fails | Restructure dependencies, use interface |
| Global singleton | Shared state, makes tests harder | DI via constructor |
