# Layered Architecture — Java/Spring Boot

---

## Recommended Package Structure

```
src/main/java/com/company/app/
├── controller/          # Web Layer
│   ├── UserController.java
│   └── dto/
│       ├── CreateUserRequest.java
│       └── UserResponse.java
├── service/             # Domain / Business Layer
│   ├── UserService.java
│   └── impl/
│       └── UserServiceImpl.java   (if there is an interface)
├── repository/          # Data Layer
│   └── UserRepository.java
├── domain/              # Domain entities
│   ├── User.java
│   └── enums/
│       └── Role.java
├── config/              # Spring configurations
│   ├── SecurityConfig.java
│   └── AsyncConfig.java
├── exception/           # Exception hierarchy
│   ├── AppException.java
│   └── handler/
│       └── GlobalExceptionHandler.java
└── client/              # External HTTP clients (Feign, RestClient)
    └── PaymentClient.java
```

---

## Package Organization Strategies

### Package-by-Layer (current standard)

Groups classes by technical role. Suitable for small projects with few domains.

```
src/main/java/com/company/app/
├── controller/   # all controllers together
├── service/      # all services together
├── repository/   # all repositories together
└── domain/
```

Advantage: simple to understand, widely known convention.
Disadvantage: low cohesion among files in the same domain; the `service/` package grows indefinitely.

---

### Package-by-Feature (recommended for systems with 3+ domains)

Groups classes by business feature. Each package is self-contained.

```
src/main/java/com/company/app/
├── user/
│   ├── UserController.java
│   ├── UserService.java
│   ├── UserRepository.java
│   ├── User.java                  // entity
│   └── dto/
│       ├── CreateUserRequest.java
│       └── UserResponse.java
├── payment/
│   ├── PaymentController.java
│   ├── PaymentService.java
│   └── dto/
│       └── PaymentResponse.java
├── config/
└── exception/
```

Advantage: high cohesion, easy to navigate, aligned with Spring Modulith modules.
Disadvantage: requires discipline to avoid cross-package coupling.

Example of cross-feature access (right vs wrong):

```java
// ✅ Communication between features via domain event (no direct coupling)
// In UserService:
publisher.publishEvent(new UserCreatedEvent(user.getId()));

// In PaymentService (listens to the event, does not depend on UserService):
@EventListener
public void onUserCreated(UserCreatedEvent event) {
    walletService.createWallet(event.userId());
}

// ❌ Direct coupling between features — avoid
@Service
public class PaymentService {
    private final UserService userService;  // ❌ payment feature depends on user feature
    // ...
}
```

---

### Decision Guide: Package-by-Layer vs Package-by-Feature

| Criterion             | Package-by-Layer | Package-by-Feature |
|-----------------------|------------------|--------------------|
| Number of domains     | 1–2              | 3+                 |
| Team size             | Small            | Medium/Large       |
| Plans to modularize   | No               | Yes (Spring Modulith) |
| Simple CRUD           | Ideal            | Excessive          |
| Complex domain        | Grows too large  | Ideal              |

Package-by-feature is recommended by Tom Hombergs (reflectoring.io) and widely adopted
in enterprise Spring Boot projects. It aligns with the Spring Modulith mental model, which
treats each top-level package as a module. It facilitates future extraction into microservices,
since the boundary is already explicit in the package structure.

---

## Responsibilities per Layer

### Controller (Web Layer)

```java
// ✅ Controller responsibilities:
// 1. Receive the HTTP request
// 2. Deserialize and validate the body (@Valid)
// 3. Delegate to the Service
// 4. Serialize and return the response

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @PostMapping
    public ResponseEntity<UserResponse> createUser(@Valid @RequestBody CreateUserRequest request) {
        UserResponse response = userService.create(request);  // fully delegates
        return ResponseEntity.created(locationOf(response.id())).body(response);
    }
}

// ❌ NOT in the Controller:
// - Business logic
// - Repository access
// - Transaction management
// - JPA entity manipulation
```

### Service (Domain Layer)

```java
// ✅ Service responsibilities:
// 1. Implement business rules
// 2. Coordinate repositories
// 3. Manage transactions (@Transactional)
// 4. Convert entity → DTO (or vice versa)
// 5. Publish domain events

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        // Business rule: unique email
        if (userRepository.existsByEmail(request.email())) {
            throw new ConflictException("Email already registered");
        }

        User user = User.create(request.name(), request.email(), request.role());
        user = userRepository.save(user);

        // Domain event
        eventPublisher.publishEvent(new UserCreatedEvent(user.getId()));

        return UserResponse.from(user);  // converts here, does not expose entity
    }
}
```

### Repository (Data Layer)

```java
// ✅ Repository responsibilities:
// 1. CRUD operations
// 2. Custom queries (JPQL, @Query)
// 3. Projections (return only necessary fields)
// NO business logic

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
}
```

---

## DTOs vs Entities

```java
// ✅ DTO at the API boundary — immutable, no JPA annotations
public record UserResponse(Long id, String name, String email) {}
public record CreateUserRequest(@NotBlank String name, @Email String email) {}

// ✅ Entity in the data layer — with JPA annotations, internally mutable
@Entity
public class User { ... }

// Data flow:
// HTTP Request → (deserialize) → DTO → Service → Entity → Repository → DB
//                                      ↑ conversion here
// DB → Repository → Entity → Service → (convert) → DTO → Controller → HTTP Response

// ❌ Never expose the Entity directly as a response
@GetMapping("/{id}")
public User getUser(@PathVariable Long id) {  // ❌ leaks internal structure, JPA serialization cycle
    return userRepository.findById(id).orElseThrow();
}
```

---

## Service Interface — When to Use

```java
// ✅ Use an interface when:
// - There are multiple implementations
// - You want to make mocking easier in tests (though @MockBean already handles this in Spring)
// - Implementing the Strategy pattern or Port (Hexagonal)

public interface PaymentGateway {
    PaymentResult process(PaymentRequest request);
}

@Component("stripe")
public class StripeGateway implements PaymentGateway { ... }

@Component("paypal")
public class PaypalGateway implements PaymentGateway { ... }

// ✅ No interface — for simple Services without multiple implementations
@Service  // directly without interface — ok for most cases
public class UserService { ... }
```

---

## Domain Events

```java
// ✅ Events to decouple side effects from the main flow
public record UserCreatedEvent(Long userId) {}

@Service
@RequiredArgsConstructor
public class UserService {
    private final ApplicationEventPublisher publisher;

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        User user = ...;
        userRepository.save(user);
        publisher.publishEvent(new UserCreatedEvent(user.getId()));  // decoupled
        return UserResponse.from(user);
    }
}

@Component
@Slf4j
public class UserEventListener {
    @EventListener
    @Async  // executes on a separate thread
    public void onUserCreated(UserCreatedEvent event) {
        log.info("User created: {}", event.userId());
        // send email, sync with CRM, etc.
    }
}
```

---

## Modular Monolith with Spring Modulith

Spring Modulith allows structuring monoliths with explicit modules, enforced boundaries,
and inter-module events — without the operational complexity of microservices. It is the
natural evolution of package-by-feature with Spring tooling support.

### When to use Spring Modulith

- System growing beyond 3–4 domains
- Different teams working on distinct parts of the system
- You want explicit boundaries but are not ready for microservices yet
- Preparation for eventual microservice extraction

### Structure with Spring Modulith

Spring Modulith treats each top-level subpackage as a module. Classes at the package level
are public (accessible by other modules); classes in `internal/` are private.

```
src/main/java/com/company/app/
├── user/                          // User Module
│   ├── UserService.java           // public (accessible by other modules)
│   ├── UserCreatedEvent.java      // public (event published to other modules)
│   └── internal/                  // private (not accessible externally)
│       ├── UserEntity.java
│       └── UserRepository.java
├── payment/                       // Payment Module
│   ├── PaymentService.java
│   └── internal/
│       └── PaymentRepository.java
└── Application.java
```

### Communication between modules

```java
// ✅ Modules communicate via events — not via direct calls to internal classes

// UserService publishes an event when creating a user
@Service
@RequiredArgsConstructor
public class UserService {
    private final ApplicationEventPublisher publisher;

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        User user = User.create(request.name(), request.email());
        userRepository.save(user);
        publisher.publishEvent(new UserCreatedEvent(user.getId()));
        return UserResponse.from(user);
    }
}

// PaymentModule listens to the event — without depending on UserModule's internal classes
@Component
public class PaymentModuleListener {

    @ApplicationModuleListener  // Spring Modulith: processes after transaction commit
    public void onUserCreated(UserCreatedEvent event) {
        walletService.initializeWallet(event.userId());
    }
}

// ❌ Avoid — Payment accessing UserModule internals
import com.company.app.user.internal.UserEntity;  // ❌ crosses module boundary
```

### Automatic boundary verification

```java
// ✅ Test that validates no module accesses another module's internals
// Spring Modulith throws an error if any module violates the boundaries
@Test
void verifyModularStructure() {
    ApplicationModules.of(Application.class).verify();
}
```

### Adding to the project

```xml
<!-- pom.xml — import via Spring Boot BOM (no explicit version required) -->
<dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-core</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

References: [Baeldung Spring Modulith](https://www.baeldung.com/spring-modulith),
[JetBrains Blog Feb/2026](https://blog.jetbrains.com/idea/2026/02/migrating-to-modular-monolith-using-spring-modulith-and-intellij-idea/).

---

## Choosing the Right Architecture

### Layered Architecture — documented in this file

**When to use:**
- CRUDs, MVPs, systems with low domain complexity
- Small teams or short-lived projects
- When development speed is the priority

**Structure:** `Controller → Service → Repository`

---

### Hexagonal Architecture (Ports & Adapters)

**When to use:**
- Rich and complex domain logic
- Multiple infrastructure adapters (database swap, multiple brokers, multiple input channels)
- High need for domain testability in isolation
- Long-lived systems (5+ years)

**Core concept:**

```
                  ┌──────────────────────────┐
  REST API ──────►│  Input Port (use case)   │
  Queue    ──────►│                          │──────► DB (Output Port)
  CLI      ──────►│    DOMAIN (hexagon)      │──────► Email (Output Port)
                  └──────────────────────────┘
```

The domain has no knowledge of Spring, JPA, or any infrastructure.
Adapters implement the Ports (interfaces defined by the domain).

**Package structure:**

```
src/main/java/com/company/app/
├── domain/               // Hexagon — zero infra dependencies
│   ├── model/
│   ├── port/
│   │   ├── in/           // Input Ports (use cases — interfaces)
│   │   └── out/          // Output Ports (driven ports — interfaces)
│   └── service/          // Domain Services (implement Input Ports)
├── adapter/
│   ├── in/
│   │   ├── web/          // REST Controllers (input adapter)
│   │   └── messaging/    // Queue consumers (input adapter)
│   └── out/
│       ├── persistence/  // JPA repositories (output adapter)
│       └── email/        // Email sender (output adapter)
└── config/
```

**Port and Adapter example:**

```java
// Input Port — defined in the domain
public interface CreateOrderUseCase {
    OrderId createOrder(CreateOrderCommand command);
}

// Domain Service implements the Input Port
@Service
public class OrderService implements CreateOrderUseCase {
    private final OrderRepository orderRepository;  // Output Port (interface)

    @Override
    public OrderId createOrder(CreateOrderCommand command) {
        Order order = Order.create(command);
        return orderRepository.save(order);  // calls interface, not implementation
    }
}

// Output Port — defined in the domain
public interface OrderRepository {
    OrderId save(Order order);
    Optional<Order> findById(OrderId id);
}

// Output Adapter — JPA implementation (outside the domain)
@Repository
public class JpaOrderRepository implements OrderRepository {
    private final SpringDataOrderRepository jpa;  // Spring Data JPA

    @Override
    public OrderId save(Order order) {
        OrderEntity entity = OrderMapper.toEntity(order);
        jpa.save(entity);
        return order.getId();
    }
}
```

---

### Vertical Slice Architecture

**When to use:**
- Inside large modules (complements modular monolith)
- Teams working on isolated features
- When you want to maximize cohesion within a context

**Concept:** Each feature (slice) contains everything it needs — controller, service, repository,
DTO — in a single vertical package. No shared horizontal layers.

---

### Decision Table

| Criterion                       | Layered    | Hexagonal  | Vertical Slices |
|---------------------------------|------------|------------|-----------------|
| Domain complexity               | Low        | High       | Medium          |
| Development speed               | High       | Medium     | High            |
| Domain testability              | Medium     | High       | Medium          |
| Infrastructure flexibility      | Low        | High       | Medium          |
| Learning curve                  | Low        | High       | Medium          |
| CRUD / MVP                      | Ideal      | Excessive  | Ok              |
| Rich domain + long lifespan     | Fragile    | Ideal      | Partial         |
| Preparation for microservices   | Ok         | Natural    | Natural         |

Layered architecture breaks down when business logic grows and couples to infrastructure (JPA
leaking into the Service, Spring annotations in the domain). Hexagonal isolates the domain
by design, making it testable and replaceable. Vertical slices maximize cohesion per feature
and are complementary to Spring Modulith.

---

## Architecture Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| Repository in the Controller | Bypasses business logic | Always route through the Service |
| Entity exposed in the API | Leaks internal structure, coupling | Convert to DTO in the Service |
| Business logic in the Controller | Not reusable, not testable | Move to the Service |
| `@Transactional` in the Controller | Transaction includes HTTP serialization | Place in the Service |
| Circular imports between packages | Indicates wrong coupling | Restructure or use events |
| Service calling another Service in a cycle | Bidirectional coupling | Extract logic to a third service or event |
