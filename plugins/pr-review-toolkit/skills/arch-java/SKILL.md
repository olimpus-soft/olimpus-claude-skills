---
name: arch-java
description: >
  Java/Spring Boot architecture skill — modern Java 25 LTS patterns, Spring Boot 3.x,
  REST APIs, Spring Data JPA, testing with JUnit 5 and Mockito, and layered architecture.
  Use as quality baseline for development, code review and analysis of Java projects.
triggers:
  - arch-java
  - java architecture
  - java best practices
  - spring boot patterns
  - modern java
---

# Arch-Java Skill

Knowledge base for modern Java/Spring Boot architecture and patterns.
Used as a baseline by the `explorer`, `dev-java` and `review-java` agents.

## Communication Principles

- **Verifiability**: never present inferences as facts. Use `[Inference]` for unverified content
- **Specificity**: always cite the file and line when pointing out problems
- **Actionability**: each problem must have a concrete recommendation
- Code and comments in **English**; discussions in **English**

---

## Core Concepts

### 1. Modern Java (Java 25 LTS)

**Reference**: `references/java/modern-java.md`

Mandatory patterns:
- **Records** for immutable DTOs (replace classes with only getters)
- **Sealed classes** for closed hierarchies (closed domain of types)
- **Pattern matching** in `instanceof` and `switch`
- **Optional** for absent values (never return `null` in public APIs)
- **Text blocks** for multiline strings (SQL, JSON templates)
- **var** for local inference when it improves readability
- **Streams + collectors + Gatherers** for collection transformation (windowFixed, windowSliding, scan, mapConcurrent)
- **Flexible Constructor Bodies** — validate before `super()` without static factory workarounds
- **Module Import Declarations** — `import module java.base;` for less boilerplate

### 2. Null Safety

**Reference**: `references/java/modern-java.md`

- Use `Optional<T>` in return types of search methods
- Use `@NonNull`/`@Nullable` annotations (Lombok or Jakarta)
- Never pass `null` between layers — use `Optional` or throw an exception
- `Objects.requireNonNull()` in constructors of critical objects

### 3. Exception Handling

**Reference**: `references/java/error-handling.md`

- Prefer **unchecked exceptions** (RuntimeException) for domain errors
- Hierarchy: `AppException` → `DomainException`, `InfraException`
- Use `@ControllerAdvice` + `@ExceptionHandler` for standardized error responses
- Never swallow exceptions with empty catch blocks
- `try-with-resources` for all `Closeable` resources

### 4. Concurrency

**Reference**: `references/java/concurrency.md`

- **CompletableFuture** for asynchronous operations without blocking threads
- **@Async** from Spring for container-managed asynchronous methods
- **Virtual Threads** (Java 21+) for I/O-bound with high concurrency; `synchronized` is safe with VTs since Java 24 (JEP 491)
- **Scoped Values** (Java 25) as the preferred replacement for `ThreadLocal` in VT-based code
- Use `ReentrantLock` only for tryLock/timed-lock/fairness — not as a VT workaround
- **Immutability** by default for shared objects

---

## Spring Boot Patterns

### 5. REST API

**Reference**: `references/spring/rest-api.md`

- **Records** as request/response DTOs (immutable, no boilerplate)
- `@Valid` + Bean Validation (Jakarta) on all request bodies
- `ResponseEntity<T>` for explicit HTTP status control
- `@ControllerAdvice` for centralized error handling
- Versioning via path: `/api/v1/resource`
- Endpoint naming: plural, nouns, kebab-case

### 6. Dependency Injection

**Reference**: `references/spring/rest-api.md`

- **Constructor injection** always (never `@Autowired` on fields)
- Use `final` on all injected fields
- `@RequiredArgsConstructor` from Lombok to reduce boilerplate
- Interfaces for services with multiple implementations or that will be mocked

### 7. Spring Data JPA

**Reference**: `references/spring/data-jpa.md`

- Entities with `@Entity`, `@Table`, `@Id`, `@GeneratedValue`
- Use `Long` for PKs (not `int`)
- Fetch type **LAZY** by default on all relationships
- `@Transactional` on service methods (not on the repository)
- Avoid N+1: use `@EntityGraph` or JOIN FETCH in queries
- `@Query` for complex JPQL; Spring Data derived queries for simple cases

---

## Testing

### 8. JUnit 5 + Mockito

**Reference**: `references/testing/junit5-mockito.md`

- `@ExtendWith(MockitoExtension.class)` for pure unit tests
- `@Mock` + `@InjectMocks` for dependency isolation
- `@ParameterizedTest` + `@ValueSource`/`@CsvSource`/`@MethodSource` for multiple scenarios
- `assertThrows()` to test exceptions
- Naming: `methodName_scenario_expectedResult()`

### 9. Spring Boot Test

**Reference**: `references/testing/spring-boot-test.md`

- `@WebMvcTest` to test only the web layer (fast)
- `@DataJpaTest` to test repositories with H2
- `@SpringBootTest` + `@AutoConfigureMockMvc` for full integration tests
- `MockMvc` to test endpoints without a real HTTP server
- `@MockBean` to replace Spring context beans

---

## Architecture

### 10. Layers

**Reference**: `references/architecture/layers.md`

Mandatory separation:
```
Controller (web) → Service (domain) → Repository (data)
```

- **Controller**: receives request, validates, delegates to service, returns response. Zero business logic.
- **Service**: business logic, coordinates repositories, manages transactions
- **Repository**: data access, no business logic
- **DTOs** at the web boundary; **Entities** only inside the data layer

### 11. Logging

- Use **SLF4J** with Logback (already included in Spring Boot)
- `private static final Logger log = LoggerFactory.getLogger(ClassName.class)`
- Or `@Slf4j` from Lombok
- Structured logging with MDC for request_id in APIs
- Never `System.out.println()` in production

---

## Essential Tools

| Category | Tool | Purpose | Command |
|----------|------|---------|---------|
| Build | Maven | Build, deps, lifecycle | `./mvnw clean verify` |
| Build | Gradle | Alternative build | `./gradlew build` |
| Test | JUnit 5 | Test framework | `./mvnw test` |
| Mock | Mockito | Mocking in unit tests | (via dependency) |
| Lint | Checkstyle | Style checker | `./mvnw checkstyle:check` |
| Analysis | SpotBugs | Static bug detector | `./mvnw spotbugs:check` |
| Code gen | Lombok | Boilerplate reduction | (via annotation processor) |
| Validation | Bean Validation | Input validation | `@Valid`, `@NotNull`, etc. |
| Docs | Springdoc OpenAPI | Automatic Swagger UI | `/swagger-ui.html` |
| Modularity | Spring Modulith | Modular monolith with explicit boundaries | (via dependency) |
| Performance | AOT Cache | Pre-load classes to reduce startup time 42% | `java -XX:AOTCacheOutput=app.aot -cp app.jar Main` |

---

## Recommended Workflow

```
DESIGN → TYPE (interfaces/records) → TEST → IMPLEMENT → VALIDATE → REVIEW
```

1. **Design**: define contracts (interfaces, request/response records)
2. **Type**: classes, generics, validation annotations
3. **Test**: unit tests with Mockito before implementing
4. **Implement**: code that passes the tests
5. **Validate**: `./mvnw verify` (compiles + tests + checkstyle)
6. **Review**: self-review against this skill

---

## References

### Java Core
- `references/java/modern-java.md` — Records, sealed, pattern matching, Optional, Streams, Gatherers, Flexible Constructors
- `references/java/concurrency.md` — CompletableFuture, Virtual Threads, Scoped Values, @Async
- `references/java/error-handling.md` — Exceptions, @ControllerAdvice, try-with-resources
- `references/java/jvm-performance.md` — AOT class loading, method profiling, startup optimization (Java 24/25)

### Spring Boot
- `references/spring/rest-api.md` — Controllers, DTOs, validation, ResponseEntity, DI
- `references/spring/data-jpa.md` — Entities, repositories, transactions, N+1

### Testing
- `references/testing/junit5-mockito.md` — Unit tests with JUnit 5 + Mockito
- `references/testing/spring-boot-test.md` — Integration tests with Spring

### Architecture
- `references/architecture/layers.md` — Controller-Service-Repository, DI, DTOs vs Entities
