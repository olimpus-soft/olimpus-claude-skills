# Tests with JUnit 5 + Mockito

---

## Basic Structure

```java
// ✅ Unit test — no Spring context, fast
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;  // Mockito injects the @Mock fields above

    // Shared data across tests
    private User testUser;
    private CreateUserRequest createRequest;

    @BeforeEach
    void setUp() {
        testUser = User.create("sample_user", "no-reply@test.invalid", Role.USER);
        ReflectionTestUtils.setField(testUser, "id", 1L);
        createRequest = new CreateUserRequest("sample_user", "no-reply@test.invalid", Role.USER, 30);
    }

    @Test
    void findById_existingUser_returnsUserResponse() {
        // Arrange
        given(userRepository.findById(1L)).willReturn(Optional.of(testUser));

        // Act
        UserResponse response = userService.findById(1L);

        // Assert
        assertThat(response.id()).isEqualTo(1L);
        assertThat(response.name()).isEqualTo("sample_user");
        assertThat(response.email()).isEqualTo("no-reply@test.invalid");
    }

    @Test
    void findById_nonExistingUser_throwsNotFoundException() {
        // Arrange
        given(userRepository.findById(99L)).willReturn(Optional.empty());

        // Act + Assert
        assertThatThrownBy(() -> userService.findById(99L))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("99");
    }

    @Test
    void create_duplicateEmail_throwsConflictException() {
        // Arrange
        given(userRepository.existsByEmail("no-reply@test.invalid")).willReturn(true);

        // Act + Assert
        assertThatThrownBy(() -> userService.create(createRequest))
            .isInstanceOf(ConflictException.class);

        then(userRepository).should(never()).save(any());  // never saved
    }
}
```

---

## Test Naming

```
methodName_scenario_expectedResult()

Good examples:
findById_existingUser_returnsUserResponse
findById_nonExistingUser_throwsNotFoundException
create_validRequest_savesAndReturnsUser
create_duplicateEmail_throwsConflictException
delete_existingUser_deletesAndPublishesEvent
```

---

## Mockito — BDDMockito (Preferred Style)

```java
import static org.mockito.BDDMockito.*;

// ✅ given/when/then instead of when/thenReturn
given(userRepository.findById(1L)).willReturn(Optional.of(testUser));
given(emailService.send(any())).willThrow(new EmailException("SMTP failed"));

// ✅ Interaction verification
then(userRepository).should().save(any(User.class));
then(userRepository).should(times(1)).findById(1L);
then(emailService).should(never()).send(any());
then(userRepository).shouldHaveNoInteractions();

// ✅ ArgumentCaptor — captures the argument passed to the mock
ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
then(userRepository).should().save(captor.capture());
User savedUser = captor.getValue();
assertThat(savedUser.getEmail()).isEqualTo("no-reply@test.invalid");

// ✅ Flexible matchers
given(repo.findByRole(eq(Role.ADMIN), any(Pageable.class))).willReturn(page);
then(emailService).should().send(argThat(email -> email.to().equals("admin@test.invalid")));
```

---

## @ParameterizedTest

```java
// ✅ Multiple simple values
@ParameterizedTest
@ValueSource(strings = {"", " ", "  \t  "})
void create_blankName_throwsValidationException(String blankName) {
    var request = new CreateUserRequest(blankName, "valid@test.invalid", Role.USER, 25);
    assertThatThrownBy(() -> userService.create(request))
        .isInstanceOf(ConstraintViolationException.class);
}

// ✅ Enum values
@ParameterizedTest
@EnumSource(Role.class)
void create_anyRole_succeeds(Role role) {
    var request = new CreateUserRequest("sample_user", "no-reply@test.invalid", role, 30);
    given(userRepository.existsByEmail(any())).willReturn(false);
    given(userRepository.save(any())).willAnswer(inv -> inv.getArgument(0));

    assertThatNoException().isThrownBy(() -> userService.create(request));
}

// ✅ CSV cases
@ParameterizedTest
@CsvSource({
    "no-reply@test.invalid, true",
    "NO-REPLY@TEST.INVALID, true",
    "user@, false",
    "not-an-email, false"
})
void isValidEmail(String email, boolean expected) {
    assertThat(EmailUtils.isValid(email)).isEqualTo(expected);
}

// ✅ Method as source (for complex objects)
@ParameterizedTest
@MethodSource("invalidRequests")
void create_invalidRequest_throwsException(CreateUserRequest request, String expectedMessage) {
    assertThatThrownBy(() -> userService.create(request))
        .hasMessageContaining(expectedMessage);
}

static Stream<Arguments> invalidRequests() {
    return Stream.of(
        Arguments.of(new CreateUserRequest("", "valid@test.invalid", Role.USER, 25), "name"),
        Arguments.of(new CreateUserRequest("sample_user", "invalid", Role.USER, 25), "email"),
        Arguments.of(new CreateUserRequest("sample_user", "valid@test.invalid", null, 25), "role")
    );
}
```

---

## AssertJ (Fluent Assertions)

```java
// Use AssertJ (included in spring-boot-starter-test)
import static org.assertj.core.api.Assertions.*;

// ✅ Basic assertions
assertThat(response.name()).isEqualTo("sample_user");
assertThat(list).hasSize(3).contains("sample_user").doesNotContain("other_user");
assertThat(optional).isPresent().hasValueSatisfying(u -> assertThat(u.getId()).isPositive());

// ✅ Exceptions
assertThatThrownBy(() -> service.findById(0L))
    .isInstanceOf(ResourceNotFoundException.class)
    .hasMessage("User not found with id: 0");

assertThatNoException().isThrownBy(() -> service.findById(1L));
assertThatCode(() -> service.validate(request)).doesNotThrowAnyException();
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `assertTrue(list.size() == 3)` | Generic failure message | `assertThat(list).hasSize(3)` |
| Mocking the class under test | Does not test the real implementation | Only mock dependencies |
| One huge test with multiple asserts | Hard to tell what failed | Split into focused tests |
| `@Mock` of repository without `@Transactional` | Expected inconsistency | Use `@DataJpaTest` for repos |
| Tests coupled to each other | Cascading failures | Each test must be independent |
