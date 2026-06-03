# Java/Spring Boot Code Review Checklist

Use during the review of each modified file. 25 checks divided into 6 categories.

---

## 🔒 Security (5 checks)

- [ ] **S1 — SQL Injection**: Are there queries with string concatenation instead of parameters? Use `@Query` with `:param` or Criteria API
- [ ] **S2 — Deserialization**: Deserializing external input without validation? Use `@Valid` + Bean Validation on all endpoints
- [ ] **S3 — Exposed Secrets**: Are there hardcoded passwords, tokens, API keys? Use `@Value` + `application.properties` + secrets manager
- [ ] **S4 — Missing Authorization**: Sensitive endpoint without `@PreAuthorize` or permission check?
- [ ] **S5 — PII in Logs**: Personal data (email, SSN, password) being logged? Mask before logging

---

## ⚡ Performance (4 checks)

- [ ] **P1 — N+1 Query**: Is there lazy collection access inside a loop? Use `JOIN FETCH` or `@EntityGraph`
- [ ] **P2 — FetchType.EAGER**: Relationships with `EAGER`? Change to `LAZY` and load explicitly when needed
- [ ] **P3 — Query without index**: Query on non-indexed field in a large table? Check `@Index` on entity or migration
- [ ] **P4 — Expensive operation in loop**: Database call, external HTTP, or heavy I/O inside for/while? Extract to batch or stream

---

## 🧪 Testing (3 checks)

- [ ] **T1 — Coverage**: Is there new business logic without a corresponding test? Happy path + error cases
- [ ] **T2 — Correct Mock**: Are they mocking the class under test (not just dependencies)? `@MockBean` used outside of `@WebMvcTest`?
- [ ] **T3 — Edge Cases**: Do tests cover null, empty list, boundary values, exceptions? Use `@ParameterizedTest` for multiple scenarios

---

## ⚙️ Code Quality (7 checks)

- [ ] **Q1 — Null without Optional**: Public method returns `null` for missing value? Replace with `Optional<T>`
- [ ] **Q2 — Exception Swallowed**: Empty `catch` or just `e.printStackTrace()`? Log and rethrow or handle appropriately
- [ ] **Q3 — Raw Types**: Use of raw types (`List`, `Map` without generics)? Always type them (`List<String>`, `Map<Long, User>`)
- [ ] **Q4 — Record for DTO**: Classes with only getters/equals/hashCode for DTO? Replace with `record`
- [ ] **Q5 — Confusing Naming**: Variables named `x`, `temp`, `data`, `obj`? Use names that express intent
- [ ] **Q6 — SRP Violated**: Method does more than one thing? Extract into smaller methods with single responsibility
- [ ] **Q7 — Adequate Logging**: Is there `System.out.println` or `e.printStackTrace()`? Use SLF4J (`log.info/warn/error`)

---

## 🌿 Spring Patterns (4 checks)

- [ ] **SP1 — Field Injection**: `@Autowired` on fields (not constructor)? Change to constructor injection with `@RequiredArgsConstructor`
- [ ] **SP2 — Missing @Transactional**: Service method performing multiple database operations without `@Transactional`? Risk of inconsistent data
- [ ] **SP3 — @Transactional in Controller**: Controller with `@Transactional`? Move to the Service
- [ ] **SP4 — Missing Bean Validation**: Request body in controller without `@Valid`? Input data without validation

---

## 💾 JPA/Data (2 checks)

- [ ] **JPA1 — Entity Exposed in API**: Controller returning `@Entity` directly? Convert to DTO in the Service
- [ ] **JPA2 — Cascade without consideration**: `cascade = CascadeType.ALL` on a critical relationship without thinking about the delete impact?

---

## 🏗️ Architecture (2 checks)

- [ ] **A1 — Repository in Controller**: Direct repository access in the controller (bypassing the service)?
- [ ] **A2 — Logic in Controller**: Business conditions, rule validations, calculations in the controller?

---

## How to Use

1. For each `.java` file in the diff, go through the 25 checks above
2. For each failing check, create a comment using `assets/comment.md`
3. Classify severity as described in `SKILL.md`
4. Include reference to the `arch-java` skill when applicable
5. At the end of the file, compile a summary with count by severity
