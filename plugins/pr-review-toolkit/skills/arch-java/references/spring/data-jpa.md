# Spring Data JPA

---

## Entity Design

```java
// ✅ Well-structured entity
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_users_email", columnList = "email", unique = true)
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)  // JPA requires a no-arg constructor
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Role role;

    // Relationships ALWAYS LAZY
    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private List<Order> orders = new ArrayList<>();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;

    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @Column(nullable = false)
    private Instant updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
        updatedAt = Instant.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = Instant.now();
    }

    // Factory method — controls valid creation
    public static User create(String name, String email, Role role) {
        var user = new User();
        user.name = Objects.requireNonNull(name);
        user.email = Objects.requireNonNull(email);
        user.role = Objects.requireNonNull(role);
        return user;
    }
}
```

---

## Repositories

```java
// ✅ Extend JpaRepository for CRUD operations + pagination
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    // Spring Data derived queries — for simple cases
    Optional<User> findByEmail(String email);
    List<User> findByRoleAndActive(Role role, boolean active);
    boolean existsByEmail(String email);
    long countByRole(Role role);

    // JPQL — for more complex queries
    @Query("SELECT u FROM User u WHERE u.role = :role AND u.createdAt >= :since")
    List<User> findActiveByRole(@Param("role") Role role, @Param("since") Instant since);

    // JOIN FETCH — avoids N+1 query
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
    Optional<User> findByIdWithOrders(@Param("id") Long id);

    // Projection — returns only the necessary fields
    @Query("SELECT new com.app.dto.UserSummary(u.id, u.name, u.email) FROM User u WHERE u.active = true")
    List<UserSummary> findAllSummaries();

    // Pagination
    Page<User> findByRole(Role role, Pageable pageable);
}
```

---

## N+1 Problem — How to Detect and Resolve

```java
// ❌ Classic N+1 — 1 query for users + N queries for orders
List<User> users = userRepository.findAll();
for (User user : users) {
    log.info("Orders: {}", user.getOrders().size());  // new query for each user!
}

// ✅ Solution 1: JOIN FETCH in JPQL
@Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.orders")
List<User> findAllWithOrders();

// ✅ Solution 2: @EntityGraph
@EntityGraph(attributePaths = {"orders", "orders.items"})
List<User> findAll();  // overrides the default method with eager fetch

// ✅ Solution 3: DTO Projection for reads (does not load the entity)
public interface UserOrderCount {
    Long getId();
    String getName();
    Long getOrderCount();
}

@Query("SELECT u.id as id, u.name as name, COUNT(o) as orderCount FROM User u LEFT JOIN u.orders o GROUP BY u.id, u.name")
List<UserOrderCount> findUserOrderCounts();
```

---

## @Transactional

```java
// ✅ @Transactional in the Service — not in the Repository
@Service
@RequiredArgsConstructor
public class UserService {

    // Read: readOnly=true (optimization — no flush at the end)
    @Transactional(readOnly = true)
    public UserResponse findById(Long id) {
        return userRepository.findById(id)
            .map(UserResponse::from)
            .orElseThrow(() -> new ResourceNotFoundException("User", id));
    }

    // Write: default transaction (REQUIRED, rollback on RuntimeException)
    @Transactional
    public UserResponse create(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new ConflictException("Email already exists: " + request.email());
        }
        User user = User.create(request.name(), request.email(), request.role());
        user = userRepository.save(user);
        eventPublisher.publishEvent(new UserCreatedEvent(user.getId()));
        return UserResponse.from(user);
    }

    // Explicit rollback for checked exceptions
    @Transactional(rollbackFor = ExternalServiceException.class)
    public void processWithExternalCall(Long id) { ... }
}

// ❌ @Transactional in Repository — adds no value, unnecessary
// ❌ @Transactional on private methods — Spring does not intercept
// ❌ this.method() with @Transactional — proxy is not invoked
```

---

## Pagination

```java
// ✅ Pageable in the Controller
@GetMapping
public ResponseEntity<Page<UserResponse>> listUsers(
        @PageableDefault(size = 20, sort = "name") Pageable pageable) {
    return ResponseEntity.ok(userService.findAll(pageable));
}

// ✅ In the Service
@Transactional(readOnly = true)
public Page<UserResponse> findAll(Pageable pageable) {
    return userRepository.findAll(pageable)
        .map(UserResponse::from);
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `FetchType.EAGER` on relationships | Loads unnecessary data, N+1 | Use `LAZY` + `@EntityGraph` when needed |
| Exposing entity directly in the API | Leaks internal data, coupling | Map to DTO in the Service |
| `@Transactional` in the Controller | Transaction spans the entire request | Place in the Service |
| Native queries without necessity | Loses database portability | Use JPQL or Criteria API |
| Updating entity via public setters | Allows invalid state | Use domain methods with rules |
