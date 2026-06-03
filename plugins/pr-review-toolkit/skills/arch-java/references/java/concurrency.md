# Concurrency in Java/Spring Boot

---

## CompletableFuture

For asynchronous operations without blocking the current thread.

```java
// ✅ Execute an asynchronous operation
CompletableFuture<UserResponse> future = CompletableFuture
    .supplyAsync(() -> userService.findById(id), executor)
    .thenApply(UserResponse::from);

// ✅ Combine multiple parallel operations
CompletableFuture<UserProfile> profile = CompletableFuture
    .allOf(userFuture, ordersFuture, addressFuture)
    .thenApply(v -> UserProfile.of(
        userFuture.join(),
        ordersFuture.join(),
        addressFuture.join()
    ));

// ✅ Error handling
CompletableFuture<String> safe = future
    .exceptionally(ex -> {
        log.error("Failed", ex);
        return "default-value";
    });

// ✅ Chaining
CompletableFuture<Void> pipeline = CompletableFuture
    .supplyAsync(this::fetchData)
    .thenApplyAsync(this::transform)
    .thenAcceptAsync(this::persist);
```

---

## @Async (Spring)

For delegating method execution to a thread pool managed by Spring.

```java
// ✅ Enable in main class or @Configuration
@SpringBootApplication
@EnableAsync
public class Application {}

// ✅ Asynchronous method — returns CompletableFuture
@Service
public class NotificationService {

    @Async
    public CompletableFuture<Void> sendEmailAsync(String to, String subject, String body) {
        emailClient.send(to, subject, body);  // blocking operation (I/O)
        return CompletableFuture.completedFuture(null);
    }

    @Async
    public CompletableFuture<Report> generateReportAsync(ReportRequest request) {
        var report = heavyReportGeneration(request);  // CPU-bound or I/O-bound
        return CompletableFuture.completedFuture(report);
    }
}

// ✅ Configure a dedicated thread pool
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(16);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}

// ⚠️ @Async only works on Spring beans (not on private methods or internal calls)
// ⚠️ Internal call (this.sendEmailAsync()) is NOT asynchronous — Spring does not intercept it
```

---

## Virtual Threads (Java 21+, enhanced in Java 24)

For applications with high I/O-bound concurrency. Replaces large thread pools.

```java
// ✅ Configure Spring Boot to use Virtual Threads (application.properties)
// spring.threads.virtual.enabled=true

// ✅ Or manually
@Bean
public TomcatProtocolHandlerCustomizer<?> protocolHandlerVirtualThreadExecutorCustomizer() {
    return protocolHandler -> protocolHandler
        .setExecutor(Executors.newVirtualThreadPerTaskExecutor());
}

// ✅ Create a virtual thread manually
Thread.ofVirtual().start(() -> {
    // I/O operation — does not block the carrier thread
    result = httpClient.send(request, BodyHandlers.ofString());
});

// Virtual threads are cheap: millions can run simultaneously without issue
// ✅ Ideal for: HTTP clients, JDBC, Redis, file I/O
// ❌ Do not use for: CPU-intensive work (prefer ForkJoinPool)
```

### synchronized and Virtual Threads (Java 24+, JEP 491)

**Java 21–23:** Virtual threads were "pinned" to their carrier platform thread when blocking
inside a `synchronized` block. This prevented other VTs from using that carrier, causing
scalability regression in legacy code with synchronized I/O.

**Java 24+ (JEP 491):** Virtual threads can now **unmount from the carrier while holding a
monitor lock**. `synchronized` is now fully scalable with Virtual Threads.

```java
// ✅ Java 24+: scalable — VT unmounts from carrier while waiting inside synchronized
class ConnectionPool {
    private final Queue<Connection> available = new LinkedList<>();

    synchronized Connection acquire() throws InterruptedException {
        while (available.isEmpty()) wait();  // VT unmounts here — carrier is free
        return available.poll();
    }

    synchronized void release(Connection c) {
        available.add(c);
        notifyAll();
    }
}
```

**Migration guidance:**

| Scenario | Java 21–23 | Java 24+ |
|---|---|---|
| `synchronized` with blocking I/O | Replace with `ReentrantLock` | Keep `synchronized` — now scalable |
| `synchronized` with CPU-bound work | Prefer `ReentrantLock` (fairness) | Still prefer `ReentrantLock` for tryLock/timed-lock/fairness |
| Existing library code (JDBC drivers, etc.) | May pin VTs — upgrade JDK | No longer pins on Java 24+ runtime |

**Monitoring pinning (Java 24+):** The `-Djdk.tracePinnedThreads` diagnostic property was
removed. Use JFR events instead:

```bash
# Check for remaining pinning (native frames, @Contended) via JFR
jfr print --events jdk.VirtualThreadPinned recording.jfr
```

---

## Scoped Values (Java 25+)

Safe, efficient alternative to `ThreadLocal` for sharing immutable data within a bounded
scope. Preferred for any code using Virtual Threads.

```java
// ✅ Declare as a static constant
static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

// ✅ Bind for the duration of a request — cleanup is automatic
ScopedValue.where(CURRENT_USER, authenticatedUser)
           .run(() -> handleRequest(request));

// ✅ Read anywhere in the call tree — no parameter passing needed
void auditAction(String action) {
    User user = CURRENT_USER.get();  // always available within the active scope
    auditLog.record(user.id(), action, Instant.now());
}

// ✅ Check before reading when scope is optional
if (CURRENT_USER.isBound()) {
    log.info("Request from user: {}", CURRENT_USER.get().id());
}

// ✅ Child tasks in StructuredTaskScope inherit parent bindings automatically
ScopedValue.where(CURRENT_USER, authenticatedUser)
           .run(() -> {
               try (var scope = StructuredTaskScope.open()) {
                   scope.fork(() -> auditService.log("read"));     // sees CURRENT_USER
                   scope.fork(() -> metricsService.increment());   // sees CURRENT_USER
                   scope.join();
               }
           });

// ✅ Rebinding creates an inner scope — outer is restored after inner run() completes
ScopedValue.where(CURRENT_USER, adminUser)
           .run(() -> {
               ScopedValue.where(CURRENT_USER, targetUser)
                          .run(() -> performActionAsUser());
               // CURRENT_USER is back to adminUser here
           });
```

### ThreadLocal vs ScopedValue

| Aspect | ThreadLocal | ScopedValue |
|--------|-------------|-------------|
| Mutability | Mutable (`set()` anywhere) | Immutable within scope |
| Lifetime | Until `remove()` or thread dies | Bounded to `run()` block — auto cleanup |
| Memory with VTs | One entry per VT — millions leak | Shared structure, no per-VT copy |
| Child threads | Manual `InheritableThreadLocal` | Automatic in `StructuredTaskScope` |
| Risk | Forgotten `remove()` → memory leak | No cleanup needed |

### Migration: ThreadLocal → ScopedValue

```java
// ❌ Old: ThreadLocal with manual cleanup — easy to forget remove()
private static final ThreadLocal<RequestContext> CTX = new ThreadLocal<>();

void handleRequest(Request req) {
    CTX.set(new RequestContext(req.userId()));
    try {
        process();
    } finally {
        CTX.remove();  // memory leak if omitted
    }
}

// ✅ New: ScopedValue — cleanup is guaranteed by run() contract
private static final ScopedValue<RequestContext> CTX = ScopedValue.newInstance();

void handleRequest(Request req) {
    ScopedValue.where(CTX, new RequestContext(req.userId()))
               .run(this::process);
}
```

---

## Thread Safety

```java
// ✅ Immutability — thread safe by nature
public record Money(BigDecimal amount, Currency currency) {
    public Money add(Money other) {
        // returns a new instance, does not mutate state
        return new Money(this.amount.add(other.amount), this.currency);
    }
}

// ✅ ConcurrentHashMap for shared cache
private final Map<String, CachedValue> cache = new ConcurrentHashMap<>();

// ✅ AtomicLong for counters
private final AtomicLong requestCount = new AtomicLong(0);

// ✅ Synchronized when necessary (minimum scope)
private synchronized void updateSharedState() {
    // minimum block — only the critical section
}

// ❌ @Service with mutable state — dangerous (Singleton in Spring)
@Service
public class BadService {
    private List<String> results = new ArrayList<>();  // mutable and shared!
    // multiple threads can corrupt the list
}

// ✅ @Service stateless — correct
@Service
public class GoodService {
    // only injected deps (final, immutable)
    private final UserRepository repo;
    // methods do not store state between calls
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `Thread.sleep()` in production code | Blocks the thread, fragile | Use `ScheduledExecutorService` or `@Scheduled` |
| Mutable state in `@Service` | Race condition in Singletons | Make services stateless |
| `synchronized` on an entire method | Lock is too coarse-grained | Lock on the minimum required scope |
| Standalone `new Thread(...)` | No lifecycle control | Use `@Async` or `ExecutorService` |
| `.get()` on `CompletableFuture` without timeout | Can block forever | `.get(timeout, unit)` or `.orTimeout()` |
| Replacing `synchronized` with `ReentrantLock` just for VT compatibility (Java 24+) | Unnecessary complexity — pinning was fixed in JEP 491 | Keep `synchronized`; use `ReentrantLock` only for tryLock/timed-lock/fairness |
| `ThreadLocal` for request context with Virtual Threads | Memory grows per VT (millions); no bounded lifetime | Use `ScopedValue` (Java 25+) |
