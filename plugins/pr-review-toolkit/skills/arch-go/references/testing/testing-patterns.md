# Testing in Go

---

## Basic Structure

```go
// File: user_service_test.go (same package)
package service

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUserService_FindByID(t *testing.T) {
    // Arrange
    repo := &mockUserRepo{
        users: map[int64]*User{
            1: {ID: 1, Name: "Alice", Email: "alice@test.com"},
        },
    }
    svc := NewUserService(repo)

    // Act
    user, err := svc.FindByID(context.Background(), 1)

    // Assert
    require.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
    assert.Equal(t, "alice@test.com", user.Email)
}
```

---

## Table-Driven Tests (Idiomatic Pattern)

```go
func TestUserService_FindByID(t *testing.T) {
    tests := []struct {
        name    string
        id      int64
        setup   func(*mockUserRepo)  // configures the mock
        want    *User
        wantErr error
    }{
        {
            name: "existing user returns user",
            id:   1,
            setup: func(m *mockUserRepo) {
                m.users[1] = &User{ID: 1, Name: "Alice"}
            },
            want: &User{ID: 1, Name: "Alice"},
        },
        {
            name: "non-existing user returns ErrNotFound",
            id:   99,
            setup: func(m *mockUserRepo) {
                // empty repo
            },
            wantErr: ErrNotFound,
        },
        {
            name: "zero ID returns error",
            id:   0,
            setup: func(m *mockUserRepo) {},
            wantErr: ErrInvalidID,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            repo := newMockUserRepo()
            tt.setup(repo)
            svc := NewUserService(repo)

            got, err := svc.FindByID(context.Background(), tt.id)

            if tt.wantErr != nil {
                require.ErrorIs(t, err, tt.wantErr)
                return
            }
            require.NoError(t, err)
            assert.Equal(t, tt.want.Name, got.Name)
        })
    }
}
```

---

## Testify: assert vs require

```go
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

// require: STOPS the test immediately on failure (FailNow)
// Use for preconditions and errors that invalidate the rest of the test
require.NoError(t, err)           // if err != nil, stops here
require.NotNil(t, result)         // if nil, stops here
require.Len(t, items, 3)          // if len != 3, stops here

// assert: REPORTS failure but continues the test
// Use for value checks where you want to see ALL failures
assert.Equal(t, "Alice", user.Name)
assert.Equal(t, "alice@test.com", user.Email)
assert.True(t, user.Active)
assert.Empty(t, user.DeletedAt)

// Rule: require for errors and preconditions, assert for values

// Useful assertions
assert.Contains(t, "hello world", "hello")
assert.ElementsMatch(t, expected, actual)  // ignores order
assert.ErrorIs(t, err, ErrNotFound)
assert.ErrorAs(t, err, &validErr)
assert.ErrorContains(t, err, "not found")
assert.WithinDuration(t, expected, actual, time.Second)
assert.JSONEq(t, expectedJSON, actualJSON)
assert.Greater(t, count, 0)
assert.InDelta(t, 3.14, result, 0.01)
```

---

## Mocks with Interfaces

```go
// Interface for dependency (defined where it is consumed)
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Save(ctx context.Context, user *User) error
    ExistsByEmail(ctx context.Context, email string) (bool, error)
}

// Manual mock
type mockUserRepo struct {
    users     map[int64]*User
    saveErr   error
    saveCalls []*User
}

func newMockUserRepo() *mockUserRepo {
    return &mockUserRepo{users: make(map[int64]*User)}
}

func (m *mockUserRepo) FindByID(_ context.Context, id int64) (*User, error) {
    user, ok := m.users[id]
    if !ok {
        return nil, ErrNotFound
    }
    return user, nil
}

func (m *mockUserRepo) Save(_ context.Context, user *User) error {
    m.saveCalls = append(m.saveCalls, user)
    if m.saveErr != nil {
        return m.saveErr
    }
    m.users[user.ID] = user
    return nil
}

func (m *mockUserRepo) ExistsByEmail(_ context.Context, email string) (bool, error) {
    for _, u := range m.users {
        if u.Email == email {
            return true, nil
        }
    }
    return false, nil
}
```

---

## Mocks with testify/mock

```go
import "github.com/stretchr/testify/mock"

type MockUserRepo struct {
    mock.Mock
}

func (m *MockUserRepo) FindByID(ctx context.Context, id int64) (*User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

func (m *MockUserRepo) Save(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

// Usage in test
func TestCreateUser(t *testing.T) {
    repo := new(MockUserRepo)
    repo.On("ExistsByEmail", mock.Anything, "alice@test.com").Return(false, nil)
    repo.On("Save", mock.Anything, mock.AnythingOfType("*User")).Return(nil)

    svc := NewUserService(repo)
    user, err := svc.Create(context.Background(), CreateUserRequest{
        Name:  "Alice",
        Email: "alice@test.com",
    })

    require.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
    repo.AssertExpectations(t)
}
```

---

## Generated Mocks with mockery

```bash
# Install mockery
go install github.com/vektra/mockery/v2@latest

# Generate mocks (configure in .mockery.yaml)
mockery

# .mockery.yaml
all: true
dir: "{{.InterfaceDir}}/mocks"
outpkg: "mocks"
mockname: "Mock{{.InterfaceName}}"
```

```go
// Usage of generated mock
import "myapp/internal/service/mocks"

func TestWithMockery(t *testing.T) {
    repo := mocks.NewMockUserRepository(t) // auto-assert expectations
    repo.EXPECT().FindByID(mock.Anything, int64(1)).Return(&User{ID: 1, Name: "Alice"}, nil)

    svc := NewUserService(repo)
    user, err := svc.FindByID(context.Background(), 1)

    require.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
}
```

---

## Test Helpers

```go
// t.Helper() marks function as helper — error reported at caller
func createTestUser(t *testing.T, name, email string) *User {
    t.Helper()
    user := &User{Name: name, Email: email}
    // ... setup
    return user
}

// t.Cleanup() for automatic teardown
func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()
    db, err := sql.Open("sqlite3", ":memory:")
    require.NoError(t, err)

    t.Cleanup(func() {
        db.Close()
    })

    return db
}

// t.Parallel() for independent tests
func TestConcurrent(t *testing.T) {
    t.Parallel() // runs in parallel with other tests that also call Parallel()

    // ... test code
}

// t.Skip() to skip conditionally
func TestIntegration(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test in short mode")
    }
}
```

---

## HTTP Handler Tests

```go
import (
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"
)

func TestGetUserHandler(t *testing.T) {
    // Arrange
    svc := &mockUserService{
        user: &User{ID: 1, Name: "Alice"},
    }
    handler := NewUserHandler(svc)

    req := httptest.NewRequest(http.MethodGet, "/users/1", nil)
    rec := httptest.NewRecorder()

    // Act
    handler.GetUser(rec, req)

    // Assert
    assert.Equal(t, http.StatusOK, rec.Code)
    assert.Contains(t, rec.Body.String(), "Alice")
}

func TestCreateUserHandler(t *testing.T) {
    body := `{"name":"Alice","email":"alice@test.com"}`
    req := httptest.NewRequest(http.MethodPost, "/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    handler.CreateUser(rec, req)

    assert.Equal(t, http.StatusCreated, rec.Code)
}
```

---

## testing/synctest — Virtual Time for Concurrent Tests (Go 1.24+)

```go
// testing/synctest tests time-dependent concurrent code without real sleep.
// time.Sleep inside synctest.Run advances a virtual clock — tests run in microseconds.
// Stable from Go 1.25+; experimental in Go 1.24 (no GOEXPERIMENT flag needed from 1.25).

import "testing/synctest"

// Example: rate limiter that allows 1 req/second
func TestRateLimiter(t *testing.T) {
    synctest.Run(func() {
        limiter := NewRateLimiter(1, time.Second)

        assert.True(t, limiter.Allow())  // first: allowed
        assert.False(t, limiter.Allow()) // second: blocked (same second)

        time.Sleep(time.Second) // advances virtual clock — no real wait
        synctest.Wait()         // blocks until all goroutines in the group are idle

        assert.True(t, limiter.Allow()) // allowed again after 1s
    })
}

// Example: retry with exponential backoff
func TestRetryWithBackoff(t *testing.T) {
    synctest.Run(func() {
        calls := 0
        op := func() error {
            calls++
            if calls < 3 {
                return errors.New("transient error")
            }
            return nil
        }

        done := make(chan error, 1)
        go func() {
            done <- RetryWithBackoff(context.Background(), op, 5, time.Second)
        }()

        // Advance through backoff windows without real sleep
        time.Sleep(1 * time.Second)
        synctest.Wait()
        time.Sleep(2 * time.Second)
        synctest.Wait()

        require.NoError(t, <-done)
        assert.Equal(t, 3, calls)
    })
}
```

**Key rules:**
- `synctest.Run(func())` — isolated goroutine group with a fake clock
- `time.Sleep` inside the group advances virtual time, not wall time
- `synctest.Wait()` — waits until all goroutines in the group are blocked/idle
- Real I/O (network, disk) still uses real time — only `time.*` is virtualized
- Do NOT mix `synctest.Run` goroutines with external goroutines

**When to use:**
- Code using `time.NewTimer`, `time.After`, `time.NewTicker`
- Retry/backoff logic, TTL caches, debounce/throttle, deadline propagation

**When NOT to use:**
- Tests with real network I/O (use `httptest` instead)
- Tests that don't involve time at all

---

## Benchmarks

```go
func BenchmarkFindByID(b *testing.B) {
    repo := setupBenchRepo(b)
    svc := NewUserService(repo)
    ctx := context.Background()

    b.ResetTimer()
    for range b.N {
        _, _ = svc.FindByID(ctx, 1)
    }
}

// Sub-benchmarks
func BenchmarkCache(b *testing.B) {
    b.Run("hit", func(b *testing.B) {
        // benchmark cache hit
    })
    b.Run("miss", func(b *testing.B) {
        // benchmark cache miss
    })
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Testing implementation, not behavior | Tests break on refactoring | Test via public interface |
| `assert` for errors instead of `require` | Test continues with nil value | Use `require.NoError` for errors |
| Test without `t.Run` | Hard to identify failure | Use subtests with `t.Run` |
| Mock that reimplements the logic | Tests nothing, duplicates code | Mock returns fixed values |
| Tests that depend on order | Flaky in parallel | Each test is independent |
| Ignoring `-race` flag | Data races in production | `go test -race ./...` |
| Hardcoded file paths in tests | Fails in CI/other environments | Use `t.TempDir()` or `testdata/` |
