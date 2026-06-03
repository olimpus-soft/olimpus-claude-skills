# Integration Tests with Spring Boot Test

---

## Test Slices (Prefer over @SpringBootTest)

```java
// ✅ @WebMvcTest — tests ONLY the web layer (controller + security)
// Fast: does not load JPA, repositories, etc.
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean  // replaces the real bean in the Spring context
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void getUser_existingId_returnsUserResponse() throws Exception {
        var response = new UserResponse(1L, "sample_user", "no-reply@test.invalid", Role.USER, Instant.now());
        given(userService.findById(1L)).willReturn(response);

        mockMvc.perform(get("/api/v1/users/1")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.name").value("sample_user"))
            .andExpect(jsonPath("$.email").value("no-reply@test.invalid"));
    }

    @Test
    void createUser_invalidRequest_returns400() throws Exception {
        var badRequest = new CreateUserRequest("", "not-an-email", null, -1);

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(badRequest)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"));
    }

    @Test
    void createUser_validRequest_returns201WithLocation() throws Exception {
        var request = new CreateUserRequest("sample_user", "no-reply@test.invalid", Role.USER, 30);
        var response = new UserResponse(1L, "sample_user", "no-reply@test.invalid", Role.USER, Instant.now());
        given(userService.create(any())).willReturn(response);

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", containsString("/api/v1/users/1")));
    }
}
```

---

## @DataJpaTest — Tests Repositories

```java
// ✅ Uses H2 in-memory, automatic rollback per test
@DataJpaTest
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TestEntityManager entityManager;

    @Test
    void findByEmail_existingEmail_returnsUser() {
        // Arrange: persist test entity
        var user = User.create("sample_user", "no-reply@test.invalid", Role.USER);
        entityManager.persistAndFlush(user);

        // Act
        Optional<User> found = userRepository.findByEmail("no-reply@test.invalid");

        // Assert
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("sample_user");
    }

    @Test
    void findByEmail_nonExisting_returnsEmpty() {
        assertThat(userRepository.findByEmail("unknown@test.invalid")).isEmpty();
    }

    @Test
    void existsByEmail_duplicateEmail_returnsTrue() {
        entityManager.persistAndFlush(User.create("other_user", "other@test.invalid", Role.USER));

        assertThat(userRepository.existsByEmail("other@test.invalid")).isTrue();
        assertThat(userRepository.existsByEmail("other@test.invalid")).isFalse();
    }
}
```

---

## @SpringBootTest — Full Integration

```java
// ✅ Full integration test — use sparingly (slow)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.ANY)
@Transactional  // rollback after each test
class UserIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Test
    void createAndRetrieveUser_fullFlow_succeeds() {
        var request = new CreateUserRequest("sample_user", "no-reply@test.invalid", Role.USER, 30);

        // POST → create
        ResponseEntity<UserResponse> createResponse = restTemplate
            .postForEntity("/api/v1/users", request, UserResponse.class);
        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        Long createdId = createResponse.getBody().id();

        // GET → retrieve the created user
        ResponseEntity<UserResponse> getResponse = restTemplate
            .getForEntity("/api/v1/users/" + createdId, UserResponse.class);
        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().email()).isEqualTo("no-reply@test.invalid");
    }
}
```

---

## MockMvc — Useful Helpers

```java
// ✅ Static imports for fluency
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.*;
import static org.hamcrest.Matchers.*;

// Verify JSON response
.andExpect(jsonPath("$.content", hasSize(2)))
.andExpect(jsonPath("$.content[0].name", is("sample_user")))
.andExpect(jsonPath("$.totalElements", is(2)))

// Log request/response for debugging
.andDo(print())

// Authentication header
mockMvc.perform(get("/api/v1/admin/users")
    .header("Authorization", "Bearer " + token))

// Multipart
mockMvc.perform(multipart("/api/v1/files")
    .file("file", content)
    .param("name", "test"))
```

---

## When to Use Each Slice

| Test | When to use | Speed |
|------|-------------|-------|
| `@ExtendWith(MockitoExtension)` | Isolated service logic | Fast |
| `@WebMvcTest` | Controller + validation + error handlers | Fast |
| `@DataJpaTest` | Repositories + JPQL queries | Medium |
| `@SpringBootTest` | End-to-end flow | Slow |

**Recommended test pyramid:**
- 70% unit tests (Mockito)
- 20% slice tests (@WebMvcTest, @DataJpaTest)
- 10% integration tests (@SpringBootTest)
