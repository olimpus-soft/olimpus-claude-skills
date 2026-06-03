# 🐹 Análisis Técnico — Go

Cargar cuando se detecta `go.mod`. Complementa `03-tecnico-core.md`.

---

## 1. Error handling idiomático

```go
// ✅ Manejo explícito con wrapping
func GetUser(id string) (*User, error) {
    user, err := db.FindByID(id)
    if err != nil {
        return nil, fmt.Errorf("get user %s: %w", id, err)
    }
    return user, nil
}

// ❌ Ignorar errores — NUNCA
user, _ := db.FindByID(id)

// ✅ Errores custom y verificación por tipo
var ErrNotFound = errors.New("not found")

if errors.Is(err, ErrNotFound) {
    // handle gracefully
}
```

- [ ] ¿No hay `_` para ignorar errores?
- [ ] ¿Errores wrapped con `%w` para mantener la cadena?
- [ ] ¿Se usa `errors.Is` / `errors.As` para verificar tipo?

---

## 2. Goroutines y context — evitar leaks

```go
// ❌ Goroutine leak: nadie lee el channel si caller ya retornó
go func() {
    ch <- expensiveOperation()
}()

// ✅ Con context y cancelación
func process(ctx context.Context) error {
    ch := make(chan int, 1)
    go func() {
        ch <- expensiveOperation()
    }()

    select {
    case result := <-ch:
        return processResult(result)
    case <-ctx.Done():
        return ctx.Err()
    }
}

// ✅ WaitGroup para múltiples goroutines
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(item Item) {  // pasar como parámetro, no capturar
        defer wg.Done()
        process(item)
    }(item)
}
wg.Wait()
```

- [ ] ¿Todas las goroutines tienen mecanismo de cancelación (ctx / channel)?
- [ ] ¿Se pasan variables de loop como parámetros a goroutines (no capturar)?
- [ ] ¿`defer wg.Done()` inmediatamente después de `wg.Add(1)`?

---

## 3. Context — propagación obligatoria

```go
// ✅ Context pasa por todas las capas
func Handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    user, err := userService.GetUser(ctx, userID)
    // ...
}

func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
    return s.repo.FindByID(ctx, id)
}

// ✅ Timeout para operaciones externas
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
result, err := externalAPI.Call(ctx)
```

- [ ] ¿`context.Context` es el primer parámetro de funciones que hacen I/O?
- [ ] ¿Se aplica timeout para llamadas externas?
- [ ] ¿Se llama `defer cancel()` siempre después de `WithTimeout`/`WithCancel`?

---

## 4. Interfaces — pequeñas y en el consumidor

```go
// ✅ Interfaces pequeñas definidas donde se usan
type UserFinder interface {
    FindByID(ctx context.Context, id string) (*User, error)
}

// ✅ Accept interfaces, return structs
func NewService(finder UserFinder) *Service {
    return &Service{finder: finder}
}

// ❌ Interfaces grandes
type Repository interface {
    FindByID(...) (...)
    FindAll(...) (...)
    Save(...) error
    Update(...) error
    Delete(...) error
    // 10 métodos más...
}
```

---

## 5. Cleanup con defer

```go
// ✅ Siempre cerrar recursos
func ReadFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil { return nil, err }
    defer f.Close()  // se ejecuta aunque haya return temprano
    return io.ReadAll(f)
}

// ✅ Recover en goroutines para evitar crash total
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("recovered from panic: %v", r)
        }
    }()
    riskyOperation()
}()
```

---

## 6. Performance en Go

```go
// ✅ Preallocar slices cuando se conoce el tamaño
result := make([]int, 0, len(items))
for _, item := range items { result = append(result, item.Value) }

// ✅ strings.Builder para concatenación en loops
var sb strings.Builder
for _, item := range items {
    sb.WriteString(item.Name)
}
result := sb.String()
```

---

## 7. Testing table-driven

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 2, 3, 5},
        {"with zero", 0, 5, 5},
        {"negative", -1, -2, -3},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Add(tt.a, tt.b); got != tt.expected {
                t.Errorf("Add(%d,%d) = %d; want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

---

## 8. Checklist Go

- [ ] No `_` para ignorar errores
- [ ] Errores wrapped con `%w`
- [ ] `context.Context` propagado en todas las funciones con I/O
- [ ] Timeout en operaciones externas
- [ ] Goroutines con mecanismo de cancelación
- [ ] Variables de loop pasadas como parámetros a goroutines
- [ ] `defer close/cancel/release` para recursos
- [ ] Interfaces pequeñas definidas en el consumidor
- [ ] Tests table-driven
- [ ] Slices preallocados con `make([]T, 0, n)`
