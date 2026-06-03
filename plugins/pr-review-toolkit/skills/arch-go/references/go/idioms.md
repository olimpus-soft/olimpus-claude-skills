# Go Idioms (Go 1.22+ / current: Go 1.26)

Mandatory idiomatic patterns for modern Go. Applies to Go 1.22 and later versions.

---

## Naming Conventions

Go has strong naming conventions. Follow them strictly.

```go
// Exported names: PascalCase
type UserService struct {}
func NewUserService() *UserService {}
func (s *UserService) FindByID(id int64) (*User, error) {}

// Unexported names: camelCase
type userRepository struct {}
func (r *userRepository) findByEmail(email string) (*User, error) {}

// Acronyms: all uppercase or all lowercase
var userID int64      // OK
var userId int64      // WRONG: mixes case in acronym
var httpClient *http.Client  // OK
var HTTPClient *http.Client  // OK (exported)

// Interfaces: names with -er suffix for single-method interfaces
type Reader interface { Read(p []byte) (n int, err error) }
type Stringer interface { String() string }
type UserFinder interface { FindUser(id int64) (*User, error) }

// WRONG: do not use I-prefix as in C#/Java
type IUserService interface {}  // WRONG
type UserService interface {}   // CORRECT
```

---

## Structs and Constructors

```go
// Constructor function: New + type name
func NewUserService(repo UserRepository, logger *slog.Logger) *UserService {
    return &UserService{
        repo:   repo,
        logger: logger,
    }
}

// Validate required dependencies
func NewOrderService(repo OrderRepository, paymentGW PaymentGateway) (*OrderService, error) {
    if repo == nil {
        return nil, errors.New("order repository is required")
    }
    if paymentGW == nil {
        return nil, errors.New("payment gateway is required")
    }
    return &OrderService{repo: repo, paymentGW: paymentGW}, nil
}

// Functional options pattern for complex configuration
type Option func(*Server)

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func NewServer(opts ...Option) *Server {
    s := &Server{port: 8080, timeout: 30 * time.Second} // defaults
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage:
srv := NewServer(WithPort(9090), WithTimeout(60*time.Second))
```

---

## Interfaces

```go
// Small, focused interfaces (1-3 methods)
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Save(ctx context.Context, user *User) error
}

// Define interfaces where they are CONSUMED, not where they are implemented
// (accept interfaces, return structs)

// package service
type OrderRepository interface {   // defined in the package that consumes it
    FindByID(ctx context.Context, id int64) (*Order, error)
}

type OrderService struct {
    repo OrderRepository   // depends on the interface
}

// package repository
type PostgresOrderRepo struct {    // implements implicitly
    db *sql.DB
}

func (r *PostgresOrderRepo) FindByID(ctx context.Context, id int64) (*Order, error) {
    // implementation
}

// WRONG: interface in the implementation package
// package repository
// type OrderRepository interface { ... }  // DO NOT define here
```

---

## Zero Values

```go
// Go initializes with zero values - use them to your advantage
var count int        // 0
var name string      // ""
var enabled bool     // false
var users []User     // nil (functional as empty slice for append)
var cache map[string]int // nil (CAREFUL: panic when writing)

// Always initialize maps before use
cache := make(map[string]int)

// Structs with useful zero value
type Config struct {
    Port    int    // 0 = use default
    Debug   bool   // false = production
    Timeout time.Duration // 0 = no timeout
}

func (c Config) PortOrDefault() int {
    if c.Port == 0 {
        return 8080
    }
    return c.Port
}
```

---

## Slices and Maps

```go
// Preallocate when size is known
users := make([]User, 0, len(ids))
for _, id := range ids {
    user, err := repo.FindByID(ctx, id)
    if err != nil {
        return nil, err
    }
    users = append(users, *user)
}

// WRONG: append without preallocate in large loop
var users []User  // reallocates multiple times

// maps.Collect (Go 1.23+) to build maps from iterators  — see Iterators section below
// slices.Collect (Go 1.23+) to build slices from iterators — see Iterators section below

// Check existence in map
val, ok := myMap[key]
if !ok {
    // key does not exist
}

// Range with index and value (Go 1.22+: no variable capture needed)
for i, user := range users {
    // 'user' is a new copy on each iteration (Go 1.22+)
    go processUser(user)  // safe without user := user
}
```

---

## Iterators (Go 1.23+)

```go
// Go 1.23: range-over-func — iterate any function matching iter.Seq / iter.Seq2.
// Used throughout the stdlib: slices.All, maps.All, bufio.Lines, etc.

import "iter"

// iter.Seq[V]    — push-based, yields single values
// iter.Seq2[K,V] — push-based, yields key+value pairs

// Writing an iterator
func (t *Tree[V]) All() iter.Seq[V] {
    return func(yield func(V) bool) {
        t.inorder(func(v V) bool {
            return yield(v) // stop early if yield returns false
        })
    }
}

// Consuming with for range — identical to slice/map iteration
for v := range tree.All() {
    fmt.Println(v)
}

// Real-world: paginated API without allocating all pages upfront
func PaginatedUsers(ctx context.Context, client *APIClient) iter.Seq2[int, *User] {
    return func(yield func(int, *User) bool) {
        for page := 0; ; page++ {
            users, err := client.ListUsers(ctx, page)
            if err != nil || len(users) == 0 {
                return
            }
            for i, u := range users {
                if !yield(page*100+i, u) {
                    return // caller used break
                }
            }
        }
    }
}

// stdlib iterator helpers (slices / maps packages)
for i, v := range slices.All(mySlice) { fmt.Println(i, v) } // iter.Seq2[int, V]
for k, v := range maps.All(myMap)     { fmt.Println(k, v) } // iter.Seq2[K, V]

// Materialize an iterator into a slice or map
all := slices.Collect(tree.All())                         // []V
m   := maps.Collect(maps.All(otherMap))                   // map[K]V
```

**Key rules:**
- `yield func(V) bool` — return `false` to signal early stop (break/return from caller)
- Iterators are **lazy** and **single-use** — do not store or reuse them
- Use `iter.Seq[V]` for value-only; `iter.Seq2[K,V]` for indexed/keyed sequences
- Use `defer` inside the iterator body to release resources when the caller stops early

**When to use:**
- Lazy sequences: paginated results, tree/graph traversal, infinite streams
- Avoiding large intermediate slices in pipelines
- Implementing collection types that plug into stdlib helpers (`slices.Collect`, etc.)

**When NOT to use:**
- Simple slice iteration — plain `for range slice` is cleaner
- Random access — use a slice
- Re-iterable sequences — create a new iterator function each time

---

## Defer

```go
// Use defer for cleanup - executes LIFO
func ReadFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, fmt.Errorf("opening file: %w", err)
    }
    defer f.Close()

    return io.ReadAll(f)
}

// Defer with named return to capture error
func WriteJSON(path string, v any) (err error) {
    f, err := os.Create(path)
    if err != nil {
        return fmt.Errorf("creating file: %w", err)
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = fmt.Errorf("closing file: %w", cerr)
        }
    }()

    return json.NewEncoder(f).Encode(v)
}

// WRONG: defer inside loop (accumulates, does not execute until return)
for _, path := range paths {
    f, _ := os.Open(path)
    defer f.Close()  // WRONG: only closes when function exits
}

// CORRECT: extract to function
for _, path := range paths {
    if err := processFile(path); err != nil {
        return err
    }
}
```

---

## Context

```go
// context.Context is ALWAYS the first parameter
func (s *UserService) FindByID(ctx context.Context, id int64) (*User, error) {
    return s.repo.FindByID(ctx, id)
}

// Propagate context throughout the chain
func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    user, err := h.service.FindByID(ctx, id)
    // ...
}

// Timeout/deadline with context
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

result, err := externalClient.Call(ctx, request)

// WRONG: context.Background() in the middle of the chain
func (s *Service) Process(ctx context.Context) error {
    // WRONG: loses timeout/cancellation from caller
    result, err := s.client.Call(context.Background(), req)
}

// Values in context: only request-scoped data (request ID, auth token)
type contextKey string
const requestIDKey contextKey = "request_id"

ctx = context.WithValue(ctx, requestIDKey, "abc-123")
```

---

## Type Assertions and Type Switches

```go
// Type switch - idiomatic Go
func describe(i interface{}) string {
    switch v := i.(type) {
    case string:
        return "string: " + v
    case int:
        return fmt.Sprintf("int: %d", v)
    case error:
        return "error: " + v.Error()
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
}

// Type assertion with ok check
str, ok := val.(string)
if !ok {
    return fmt.Errorf("expected string, got %T", val)
}

// WRONG: type assertion without check (panic on failure)
str := val.(string)  // panic if val is not a string
```

---

## Enums with iota

```go
type OrderStatus int

const (
    OrderStatusPending    OrderStatus = iota // 0
    OrderStatusConfirmed                     // 1
    OrderStatusShipped                       // 2
    OrderStatusDelivered                     // 3
    OrderStatusCancelled                     // 4
)

func (s OrderStatus) String() string {
    switch s {
    case OrderStatusPending:
        return "PENDING"
    case OrderStatusConfirmed:
        return "CONFIRMED"
    case OrderStatusShipped:
        return "SHIPPED"
    case OrderStatusDelivered:
        return "DELIVERED"
    case OrderStatusCancelled:
        return "CANCELLED"
    default:
        return fmt.Sprintf("unknown(%d)", s)
    }
}

// Validation
func (s OrderStatus) IsValid() bool {
    return s >= OrderStatusPending && s <= OrderStatusCancelled
}
```

---

## Randomness (Go 1.22+)

```go
// Use math/rand/v2 — math/rand (v1) is deprecated since Go 1.22.
// v2 is auto-seeded, uses ChaCha8 by default, and has a cleaner API.

import "math/rand/v2"

// Integer in [0, n)
n := rand.IntN(100)        // [0, 100)
i := rand.N[int64](1000)   // generic: any integer type

// Float in [0.0, 1.0)
f := rand.Float64()

// Shuffle a slice
rand.Shuffle(len(items), func(i, j int) {
    items[i], items[j] = items[j], items[i]
})

// Reproducible in tests: local Rand with fixed seed
rng := rand.New(rand.NewPCG(42, 0))
val := rng.IntN(100)

// WRONG: deprecated v1 package
import "math/rand"            // deprecated since Go 1.22
rand.Seed(time.Now().Unix())  // also deprecated — v2 is auto-seeded

// Cryptographic randomness: always use crypto/rand (unchanged)
import crand "crypto/rand"
b := make([]byte, 32)
_, err := crand.Read(b)
```

**Key rules:**
- `math/rand/v2` global is auto-seeded — never call `rand.Seed()`
- For reproducible tests: `rand.New(rand.NewPCG(seed, seq))`
- Security-sensitive (tokens, keys, nonces): always use `crypto/rand`
- Prefer `rand.N[T]` (generic) over type-specific variants

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `interface{}` instead of `any` | Verbose (Go 1.18+) | Use `any` |
| Interface with many methods | Hard to mock, violates ISP | Break into smaller interfaces |
| Interface in the implementation package | Unnecessary coupling | Define where consumed |
| `init()` with side effects | Makes tests harder, unpredictable order | Explicit constructor |
| Panic in libraries | Breaks caller without recovery option | Return error |
| Returning `interface{}` | Loses type safety | Return concrete type |
| Getter with Get prefix | Non-idiomatic in Go | `User()` instead of `GetUser()` |
| `import "math/rand"` (v1) | Deprecated since Go 1.22, weak PRNG | Use `math/rand/v2` |
