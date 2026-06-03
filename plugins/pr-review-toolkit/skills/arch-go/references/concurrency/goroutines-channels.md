# Concurrency in Go: Goroutines and Channels

---

## Goroutines

```go
// Basic goroutine
go func() {
    result := heavyComputation()
    resultCh <- result
}()

// ALWAYS ensure goroutines terminate (do not leak)
func (s *Server) Start(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)

    g.Go(func() error {
        return s.httpServer.ListenAndServe()
    })

    g.Go(func() error {
        <-ctx.Done()
        return s.httpServer.Shutdown(context.Background())
    })

    return g.Wait()
}
```

---

## Channels

```go
// Unbuffered channel: synchronization
done := make(chan struct{})

go func() {
    defer close(done)
    processData()
}()

<-done // wait for goroutine to finish

// Buffered channel: decouple producer/consumer
jobs := make(chan Job, 100)

// Producer
go func() {
    defer close(jobs) // ALWAYS close channels on the producer side
    for _, item := range items {
        jobs <- Job{Item: item}
    }
}()

// Consumer
for job := range jobs { // range ends when channel is closed
    process(job)
}

// Direction: restrict access with channel direction
func producer(out chan<- int) { // can only send
    out <- 42
}

func consumer(in <-chan int) { // can only receive
    val := <-in
}
```

---

## Select

```go
// Select to multiplex channels
func (w *Worker) Run(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case job := <-w.jobs:
            if err := w.process(job); err != nil {
                slog.Error("processing job", "error", err)
            }
        case <-time.After(30 * time.Second):
            slog.Info("worker idle for 30s")
        }
    }
}

// Non-blocking send/receive with default
select {
case ch <- value:
    // sent
default:
    // channel full, discard or handle
    slog.Warn("channel full, dropping message")
}
```

---

## errgroup (golang.org/x/sync/errgroup)

```go
// Recommended pattern for fan-out/fan-in with error handling
func (s *Service) FetchAll(ctx context.Context, ids []int64) ([]*User, error) {
    g, ctx := errgroup.WithContext(ctx)
    users := make([]*User, len(ids))

    for i, id := range ids {
        g.Go(func() error {
            user, err := s.repo.FindByID(ctx, id)
            if err != nil {
                return fmt.Errorf("fetching user %d: %w", id, err)
            }
            users[i] = user // safe: each goroutine writes to a unique index
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return users, nil
}

// With concurrency limit
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(10) // maximum 10 simultaneous goroutines

for _, id := range ids {
    g.Go(func() error {
        return processItem(ctx, id)
    })
}
```

---

## sync.WaitGroup

```go
// WaitGroup to wait for N goroutines (without error handling)
var wg sync.WaitGroup

for _, item := range items {
    wg.Add(1)
    go func() {
        defer wg.Done()
        process(item)
    }()
}

wg.Wait()

// Go 1.25+: WaitGroup.Go simplifies the pattern
var wg sync.WaitGroup
for _, item := range items {
    wg.Go(func() {
        process(item)
    })
}
wg.Wait()
```

---

## sync.Mutex and sync.RWMutex

```go
// Mutex to protect shared state
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// RWMutex: multiple readers, one writer
type Cache struct {
    mu    sync.RWMutex
    items map[string]Item
}

func (c *Cache) Get(key string) (Item, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, ok := c.items[key]
    return item, ok
}

func (c *Cache) Set(key string, item Item) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = item
}
```

---

## sync.Once

```go
// Thread-safe lazy initialization
type DBPool struct {
    once sync.Once
    db   *sql.DB
}

func (p *DBPool) Get() *sql.DB {
    p.once.Do(func() {
        var err error
        p.db, err = sql.Open("postgres", dsn)
        if err != nil {
            panic(fmt.Sprintf("opening database: %v", err))
        }
    })
    return p.db
}
```

---

## Common Patterns

### Worker Pool

```go
func WorkerPool(ctx context.Context, jobs <-chan Job, workers int) <-chan Result {
    results := make(chan Result, workers)

    var wg sync.WaitGroup
    for range workers {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                case results <- process(job):
                }
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}
```

### Fan-Out / Fan-In

```go
func FanOut(ctx context.Context, input <-chan int, workers int) []<-chan int {
    channels := make([]<-chan int, workers)
    for i := range workers {
        channels[i] = worker(ctx, input)
    }
    return channels
}

func FanIn(ctx context.Context, channels ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup

    for _, ch := range channels {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for val := range ch {
                select {
                case <-ctx.Done():
                    return
                case out <- val:
                }
            }
        }()
    }

    go func() {
        wg.Wait()
        close(out)
    }()

    return out
}
```

### Pipeline

```go
func Pipeline(ctx context.Context, input <-chan int) <-chan int {
    doubled := stage(ctx, input, func(v int) int { return v * 2 })
    filtered := filter(ctx, doubled, func(v int) bool { return v > 10 })
    return filtered
}

func stage[T, U any](ctx context.Context, in <-chan T, fn func(T) U) <-chan U {
    out := make(chan U)
    go func() {
        defer close(out)
        for v := range in {
            select {
            case <-ctx.Done():
                return
            case out <- fn(v):
            }
        }
    }()
    return out
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Goroutine without lifecycle control | Goroutine leak | Use context, errgroup, or WaitGroup |
| Closing channel on the receiver side | Panic: send on closed channel | Close only on the producer side |
| Copied mutex | Race condition | Pass by pointer, never copy struct with Mutex |
| `time.Sleep` for synchronization | Fragile and slow | Use channels, WaitGroup, or errgroup |
| Unbuffered channel for fire-and-forget | Goroutine blocks forever | Use buffered channel or errgroup |
| Shared state without protection | Data race | Use Mutex, channels, or atomic |
| Inconsistent lock order | Deadlock | Always acquire locks in the same order |
