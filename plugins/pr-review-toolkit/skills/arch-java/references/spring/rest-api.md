# REST API with Spring Boot

---

## Controllers

```java
// ✅ Clean controller — only receive, delegate, respond
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    @GetMapping
    public ResponseEntity<List<UserResponse>> listUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(userService.listUsers(page, size));
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        UserResponse created = userService.create(request);
        URI location = URI.create("/api/v1/users/" + created.id());
        return ResponseEntity.created(location).body(created);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UpdateUserRequest request) {
        return ResponseEntity.ok(userService.update(id, request));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}

// ❌ Do not put business logic in the controller
// ❌ Do not access repositories directly from the controller
// ❌ Do not map JPA entities directly to the response
```

---

## DTOs with Records

```java
// ✅ Request DTO with Bean Validation
public record CreateUserRequest(
    @NotBlank(message = "Name is required")
    @Size(max = 100)
    String name,

    @NotBlank @Email(message = "Invalid email")
    String email,

    @NotNull
    Role role,

    @Min(0) @Max(150)
    Integer age
) {}

// ✅ Response DTO — projects only what is necessary
public record UserResponse(
    Long id,
    String name,
    String email,
    Role role,
    Instant createdAt
) {
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(), user.getName(), user.getEmail(),
            user.getRole(), user.getCreatedAt()
        );
    }
}

// ✅ Paginated DTO
public record PageResponse<T>(
    List<T> content,
    int page,
    int size,
    long totalElements,
    int totalPages
) {
    public static <T> PageResponse<T> from(Page<T> page) {
        return new PageResponse<>(
            page.getContent(), page.getNumber(), page.getSize(),
            page.getTotalElements(), page.getTotalPages()
        );
    }
}
```

---

## Bean Validation (Jakarta)

```java
// Most commonly used annotations
@NotNull     // cannot be null
@NotBlank    // cannot be null, empty, or whitespace-only (String)
@NotEmpty    // cannot be null or empty
@Size(min=, max=)  // size of String or Collection
@Email       // email format
@Min / @Max  // minimum/maximum numeric value
@Positive    // number > 0
@Pattern(regexp=)  // regex

// ✅ Validation in controller with @Valid
@PostMapping
public ResponseEntity<X> create(@Valid @RequestBody Request request) { ... }

// ✅ Custom validation
@Target({FIELD, PARAMETER})
@Retention(RUNTIME)
@Constraint(validatedBy = CpfValidator.class)
public @interface ValidCpf {
    String message() default "Invalid CPF";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class CpfValidator implements ConstraintValidator<ValidCpf, String> {
    @Override
    public boolean isValid(String cpf, ConstraintValidatorContext ctx) {
        return CpfUtils.isValid(cpf);
    }
}
```

---

## Dependency Injection — Constructor Injection

```java
// ✅ Constructor injection with Lombok — the correct approach
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    private final UserMapper mapper;
}

// ✅ Without Lombok — same idea
@Service
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}

// ❌ Field injection — makes testing harder, hides dependencies
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // do not use
}

// ❌ Setter injection — dependency can be null
@Service
public class UserService {
    private UserRepository userRepository;

    @Autowired
    public void setRepository(UserRepository repo) { ... }  // do not use
}
```

---

## ResponseEntity

```java
// Correct status codes per operation:
// GET         → 200 OK          + body
// POST        → 201 Created     + body + Location header
// PUT/PATCH   → 200 OK          + updated body
// DELETE      → 204 No Content  + no body
// Error 400   → 400 Bad Request  (validation, format)
// Error 404   → 404 Not Found    (resource not found)
// Error 409   → 409 Conflict     (duplicate, invalid state)
// Error 422   → 422 Unprocessable (business rule)
// Error 500   → 500 Internal     (unexpected errors)

// ✅ Examples
return ResponseEntity.ok(body);                          // 200
return ResponseEntity.created(uri).body(body);           // 201
return ResponseEntity.noContent().build();               // 204
return ResponseEntity.notFound().build();                // 404
return ResponseEntity.badRequest().body(errorResponse);  // 400
```

---

## API Best Practices

```
// Endpoint naming
/api/v1/users              GET   - list
/api/v1/users/{id}         GET   - by ID
/api/v1/users              POST  - create
/api/v1/users/{id}         PUT   - update
/api/v1/users/{id}         DELETE - delete
/api/v1/users/{id}/orders  GET   - sub-resource

// Conventions
- Nouns (not verbs): /users, not /getUsers
- Plural: /users, not /user
- Kebab-case: /user-profiles, not /userProfiles
- Versioning in path: /api/v1/...
- Pagination: ?page=0&size=20&sort=name,asc
- Filters: ?status=ACTIVE&role=ADMIN
```
