# Modern Java (17–25 LTS) Patterns

Mandatory patterns for Java 17–25 LTS. Java 25 is the current LTS (September 2025); Spring Boot 3.5+ targets Java 25 as the recommended baseline.

---

## Records

Use records for immutable DTOs and value objects. They eliminate boilerplate getters, equals, hashCode, and toString.

```java
// ✅ Record as a request DTO
public record CreateUserRequest(
    @NotBlank String name,
    @Email String email,
    @NotNull Role role
) {}

// ✅ Record as a response DTO
public record UserResponse(
    Long id,
    String name,
    String email,
    Role role,
    Instant createdAt
) {
    // Static factory method from entity
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(),
            user.getName(),
            user.getEmail(),
            user.getRole(),
            user.getCreatedAt()
        );
    }
}

// ❌ Do not use: mutable class with getters/setters for DTO
public class UserResponseOld {
    private Long id;
    private String name;
    // getters, setters, equals, hashCode, toString... unnecessary boilerplate
}
```

**When to use records:**
- Request/response DTOs in REST APIs
- Domain value objects (Money, Address, Coordinates)
- Query results (projections)
- Return values that group multiple values

**When NOT to use records:**
- JPA Entities (must be mutable and have a no-arg constructor)
- Classes that require inheritance
- When complex construction logic is needed

---

## Sealed Classes

For closed type hierarchies — when the set of subtypes is known and fixed.

```java
// ✅ Operation result with explicit types
public sealed interface PaymentResult
    permits PaymentResult.Success, PaymentResult.Failure, PaymentResult.Pending {

    record Success(String transactionId, Instant processedAt) implements PaymentResult {}
    record Failure(String reason, ErrorCode code) implements PaymentResult {}
    record Pending(String trackingId) implements PaymentResult {}
}

// ✅ Exhaustive pattern matching (compiler ensures all cases are covered)
String message = switch (result) {
    case PaymentResult.Success s -> "Payment approved: " + s.transactionId();
    case PaymentResult.Failure f -> "Failed: " + f.reason();
    case PaymentResult.Pending p -> "Pending: " + p.trackingId();
};
```

---

## Flexible Constructor Bodies (Java 25+)

The restriction that `super()` or `this()` must be the **first** statement in a constructor
has been lifted. Code before the delegation call (the "prologue") cannot reference `this`,
but can validate arguments and initialize `final` fields.

```java
// ✅ Validate BEFORE super() — previously impossible without a static factory
class Employee extends Person {
    final String department;

    Employee(int age, String department) {
        if (age < 18) throw new IllegalArgumentException("Must be 18+: " + age);
        Objects.requireNonNull(department, "department must not be null");
        super(age);                     // super() no longer forced to be first
        this.department = department;
    }
}

// ✅ Initialize subclass final field before super()
class AuditedRepository<T> extends SimpleJpaRepository<T, Long> {
    private final AuditLogger auditLogger;

    AuditedRepository(JpaEntityInformation<T, ?> info, EntityManager em, AuditLogger logger) {
        this.auditLogger = Objects.requireNonNull(logger);  // field init before super()
        super(info, em);
    }
}

// ❌ Old workaround: static factory just to pre-validate before delegating
class EmployeeOld extends Person {
    static EmployeeOld of(int age, String dept) {
        if (age < 18) throw new IllegalArgumentException(...);
        return new EmployeeOld(age, dept);
    }
    private EmployeeOld(int age, String dept) { super(age); ... }
}
```

**Key constraint:** The prologue cannot read or write `this` (other than assigning `final` fields).

**When to use:**
- Validate constructor arguments before the superclass processes them
- Initialize `final` fields the superclass constructor depends on indirectly
- Avoid static factory methods created solely to pre-validate

---

## Pattern Matching

### instanceof (Java 16+)

```java
// ✅ Pattern matching — eliminates explicit cast
if (obj instanceof String s && !s.isEmpty()) {
    return s.toUpperCase();
}

// ❌ Old style
if (obj instanceof String) {
    String s = (String) obj;
    return s.toUpperCase();
}
```

### switch expressions (Java 14+)

```java
// ✅ Switch expression with pattern matching (Java 21)
String label = switch (shape) {
    case Circle c    -> "Circle r=" + c.radius();
    case Rectangle r -> "Rect " + r.width() + "x" + r.height();
    case Triangle t  -> "Triangle";
};

// ✅ Switch as an expression (no fall-through)
int days = switch (month) {
    case JANUARY, MARCH, MAY, JULY, AUGUST, OCTOBER, DECEMBER -> 31;
    case APRIL, JUNE, SEPTEMBER, NOVEMBER -> 30;
    case FEBRUARY -> year % 4 == 0 ? 29 : 28;
};
```

---

## Optional

Use to indicate the absence of a value in public method return types.

```java
// ✅ Search by ID return — may not exist
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ✅ Consuming Optional correctly
userRepository.findById(id)
    .map(UserResponse::from)
    .orElseThrow(() -> new UserNotFoundException(id));

// ✅ orElse / orElseGet
String display = user.getNickname()
    .orElse(user.getName());

// ✅ Conditionally execute an action
user.getEmail().ifPresent(email -> notificationService.send(email));

// ❌ Never return Optional<Optional<T>>
// ❌ Never use Optional as a method parameter
// ❌ Never use Optional in entity fields
// ❌ Never call .get() without checking .isPresent() first
```

---

## Streams

For transforming and aggregating collections without imperative loops.

```java
// ✅ Transformation with map + filter + collect
List<String> activeEmails = users.stream()
    .filter(User::isActive)
    .map(User::getEmail)
    .sorted()
    .toList();  // Java 16+: immutable list

// ✅ Grouping
Map<Role, List<User>> byRole = users.stream()
    .collect(Collectors.groupingBy(User::getRole));

// ✅ Aggregation
OptionalDouble avgAge = users.stream()
    .mapToInt(User::getAge)
    .average();

// ✅ flatMap for lists of lists
List<Permission> allPermissions = roles.stream()
    .flatMap(role -> role.getPermissions().stream())
    .distinct()
    .toList();

// ❌ Do not use Streams for operations with side effects or that require an index
// ❌ Do not nest streams without flatMap
```

---

## Stream Gatherers (Java 24+)

`Stream::gather(Gatherer)` is a fully extensible intermediate stream operation — the missing
link between `filter/map` (one-to-one) and `collect` (many-to-one). Analogous to how
`Collector` works for terminal operations, `Gatherer` works for intermediate transformations.

### Built-in Gatherers (`java.util.stream.Gatherers`)

```java
// ✅ Fixed windows — group into non-overlapping batches of n elements
Stream.of(1, 2, 3, 4, 5, 6, 7, 8, 9)
    .gather(Gatherers.windowFixed(3))
    .toList();
// → [[1,2,3], [4,5,6], [7,8,9]]

// ✅ Sliding windows — overlapping windows (useful for moving averages)
Stream.of(1, 2, 3, 4, 5)
    .gather(Gatherers.windowSliding(3))
    .toList();
// → [[1,2,3], [2,3,4], [3,4,5]]

// ✅ Scan — running fold / prefix aggregation (cumulative sums, stats)
Stream.of(1, 2, 3, 4, 5)
    .gather(Gatherers.scan(() -> 0, Integer::sum))
    .toList();
// → [1, 3, 6, 10, 15]

// ✅ Fold — many-to-one as intermediate step, chainable with further operations
Stream.of("a", "b", "c")
    .gather(Gatherers.fold(() -> "", (acc, s) -> acc + s))
    .map(String::toUpperCase)
    .findFirst();
// → Optional["ABC"]

// ✅ mapConcurrent — virtual-thread parallel mapping (preserves order, backpressure built-in)
List<Response> responses = requests.stream()
    .gather(Gatherers.mapConcurrent(16, this::callExternalService))
    .toList();
// Uses up to 16 virtual threads; element order is preserved
```

### Custom Gatherer

```java
// ✅ Stateful gatherer: take elements while they are strictly increasing
Gatherer<Integer, ?, Integer> takeWhileIncreasing = Gatherer.ofSequential(
    () -> new int[]{Integer.MIN_VALUE},          // initializer — mutable local state
    (state, element, downstream) -> {            // integrator
        if (element > state[0]) {
            state[0] = element;
            return downstream.push(element);     // true = continue pipeline
        }
        return false;                            // false = short-circuit
    }
);

Stream.of(1, 3, 5, 4, 6).gather(takeWhileIncreasing).toList();
// → [1, 3, 5]
```

**Gatherer vs Collector:**
- `gather()` is **intermediate** — chains with further `filter`, `map`, `toList()`
- `collect()` is **terminal** — produces the final result
- Use Gatherers for windowing, stateful transformations, batching, parallel I/O within pipelines

**❌ Antipatterns replaced by Gatherers:**

| Old Pattern | Problem | Gatherer replacement |
|---|---|---|
| Imperative index loop for batching | Verbose, error-prone | `Gatherers.windowFixed(n)` |
| `Stream.iterate` for running aggregation | Unintuitive, no early termination | `Gatherers.scan()` |
| `parallelStream()` for I/O-bound work | ForkJoin tasks, not VT-friendly | `Gatherers.mapConcurrent(n, fn)` |

---

## Text Blocks (Java 15+)

```java
// ✅ Multiline SQL
String query = """
    SELECT u.id, u.name, u.email
    FROM users u
    WHERE u.active = true
      AND u.role = :role
    ORDER BY u.name
    """;

// ✅ JSON template
String body = """
    {
        "name": "%s",
        "email": "%s"
    }
    """.formatted(name, email);
```

---

## var (Local Variable Type Inference)

```java
// ✅ When the type is obvious from the initializer
var users = userRepository.findAll();
var response = UserResponse.from(user);

// ❌ When it obscures the type
var x = process(data);  // What does process() return?
```

---

## Module Import Declarations (Java 25+)

`import module M;` imports all public types exported by module `M` in a single declaration.

```java
// ❌ Before: 6 separate imports from java.base
import java.util.Map;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.Collectors;
import java.util.function.Function;
import java.util.Optional;

// ✅ After: single module import
import module java.base;

// Ambiguity resolution: single-type import always wins over module import
import module java.base;   // exports java.util.Date
import module java.sql;    // also exports java.sql.Date
import java.sql.Date;      // explicit import resolves the conflict — unambiguous
```

**When to use:**
- Test classes that use many `java.base` types
- Scripts and compact programs (combined with instance `main()` from JEP 512)

**When NOT to use:**
- Production service classes — explicit imports serve as documentation of dependencies

---

## Antipatterns to Avoid

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Returning `null` from public methods | Silent NullPointerException | Use `Optional<T>` |
| `instanceof` without pattern matching | Unnecessary explicit cast | Use pattern matching |
| Switch with fall-through | Bug-prone, hard to read | Use switch expressions |
| Imperative loops for transformation | Verbose, less declarative | Use Streams |
| Classes with only getters/equals/hashCode for DTOs | Unnecessary boilerplate | Use Records |
| `parallelStream()` for I/O-bound work | ForkJoin pool, not VT-friendly | Use `Gatherers.mapConcurrent(n, fn)` |
| Imperative index loop for batch/window processing | Verbose, error-prone | Use `Gatherers.windowFixed(n)` |
