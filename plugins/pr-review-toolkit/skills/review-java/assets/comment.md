# Java Code Review Comment Template

Use this template for EACH issue found during the review.
Fill in all `{...}` placeholders with specific information from the diff.

---

## Base Template

```markdown
---

**File:** `{filepath}`
**Lines:** {start_line}-{end_line}
**Category:** {emoji} {category}
**Severity:** {emoji} {severity}

**Issue:**
{clear and objective description of the problem in 1-2 sentences}

**Current Code:**
```java
{problematic code extracted from the diff — exactly as it appears}
```

**Suggested Code:**
```java
{corrected code — must compile and follow arch-java standards}
```

**Rationale:**
{technical explanation of why this is a problem}
{impact if not fixed: performance, security, maintainability}

**Reference:**
- Arch-Java Skill: [{file name}](../arch-java/{path})
{other references if applicable}
```

---

## Examples of Filled-in Comments

### Example 1 — N+1 Query (🟠 High)

```markdown
---

**File:** `src/main/java/com/app/service/OrderService.java`
**Lines:** 45-52
**Category:** ⚡ Performance
**Severity:** 🟠 High

**Issue:**
N+1 query: the loop iterates over users and accesses `user.getOrders()` on each iteration,
firing an additional database query per user.

**Current Code:**
```java
List<User> users = userRepository.findAll();
for (User user : users) {
    int total = user.getOrders().size();  // N+1 here
    log.info("User {} has {} orders", user.getName(), total);
}
```

**Suggested Code:**
```java
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.orders")
List<User> findAllWithOrders();

// In the service:
List<User> users = userRepository.findAllWithOrders();  // 1 query with JOIN
for (User user : users) {
    int total = user.getOrders().size();  // does not fire a new query
    log.info("User {} has {} orders", user.getName(), total);
}
```

**Rationale:**
With 1000 users, this generates 1001 database queries (1 to list + 1 per user).
Use `LEFT JOIN FETCH` in JPQL or `@EntityGraph` to load in a single query.

**Reference:**
- Arch-Java Skill: [Spring Data JPA — N+1](../arch-java/references/spring/data-jpa.md)
```

---

### Example 2 — Field Injection (🟡 Medium)

```markdown
---

**File:** `src/main/java/com/app/service/UserService.java`
**Lines:** 12-16
**Category:** 🌿 Spring Patterns
**Severity:** 🟡 Medium

**Issue:**
Field injection via `@Autowired` makes unit testing harder and hides mandatory dependencies.

**Current Code:**
```java
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    @Autowired
    private EmailService emailService;
}
```

**Suggested Code:**
```java
@Service
@RequiredArgsConstructor  // Lombok generates constructor with all final fields
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}
```

**Rationale:**
Constructor injection ensures dependencies are mandatory (never null), allows
use with `@InjectMocks` in Mockito without Spring, and respects the immutability principle.

**Reference:**
- Arch-Java Skill: [REST API — Dependency Injection](../arch-java/references/spring/rest-api.md)
```

---

### Example 3 — Entity Exposed in API (🟠 High)

```markdown
---

**File:** `src/main/java/com/app/controller/UserController.java`
**Lines:** 28-31
**Category:** 🏗️ Architecture
**Severity:** 🟠 High

**Issue:**
The JPA entity `User` is returned directly as a response, exposing internal structure
and causing serialization issues with lazy relationships.

**Current Code:**
```java
@GetMapping("/{id}")
public User getUser(@PathVariable Long id) {
    return userRepository.findById(id).orElseThrow();
}
```

**Suggested Code:**
```java
// Controller delegates to Service and returns DTO
@GetMapping("/{id}")
public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
    return ResponseEntity.ok(userService.findById(id));
}

// Service converts entity -> DTO
@Transactional(readOnly = true)
public UserResponse findById(Long id) {
    return userRepository.findById(id)
        .map(UserResponse::from)
        .orElseThrow(() -> new ResourceNotFoundException("User", id));
}

// Immutable DTO as record
public record UserResponse(Long id, String name, String email) {
    public static UserResponse from(User user) {
        return new UserResponse(user.getId(), user.getName(), user.getEmail());
    }
}
```

**Rationale:**
Exposing JPA entities in the API creates coupling with the internal data model, may serialize
lazy relationships causing LazyInitializationException, and leaks internal fields.

**Reference:**
- Arch-Java Skill: [Architecture — DTOs vs Entities](../arch-java/references/architecture/layers.md)
```

---

## Positive Points Section (Always Include)

At the end of the review for each file:

```markdown
### ✅ Positive Points

1. ✨ {well-implemented aspect — be specific}
2. ✨ {good practice followed}
3. ✨ {quality worth highlighting}
```
