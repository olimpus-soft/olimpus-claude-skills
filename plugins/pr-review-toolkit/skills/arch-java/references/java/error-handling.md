# Error Handling in Java/Spring Boot

---

## Exception Hierarchy

Define a clear exception hierarchy for the application:

```java
// ✅ Base of the hierarchy — unchecked
public abstract class AppException extends RuntimeException {
    private final String errorCode;

    protected AppException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    protected AppException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() { return errorCode; }
}

// ✅ Domain exceptions
public class ResourceNotFoundException extends AppException {
    public ResourceNotFoundException(String resource, Object id) {
        super("RESOURCE_NOT_FOUND", resource + " not found with id: " + id);
    }
}

public class BusinessRuleViolationException extends AppException {
    public BusinessRuleViolationException(String message) {
        super("BUSINESS_RULE_VIOLATION", message);
    }
}

public class ConflictException extends AppException {
    public ConflictException(String message) {
        super("CONFLICT", message);
    }
}

// ✅ Infrastructure exceptions
public class ExternalServiceException extends AppException {
    public ExternalServiceException(String service, String message, Throwable cause) {
        super("EXTERNAL_SERVICE_ERROR", service + ": " + message, cause);
    }
}
```

---

## @ControllerAdvice — Centralized Handler

```java
// ✅ Centralized handler for all API exceptions
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // Domain error: resource not found → 404
    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ResourceNotFoundException ex) {
        log.warn("Resource not found: {}", ex.getMessage());
        return new ErrorResponse(ex.getErrorCode(), ex.getMessage());
    }

    // Business rule violated → 422
    @ExceptionHandler(BusinessRuleViolationException.class)
    @ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
    public ErrorResponse handleBusinessRule(BusinessRuleViolationException ex) {
        log.warn("Business rule violation: {}", ex.getMessage());
        return new ErrorResponse(ex.getErrorCode(), ex.getMessage());
    }

    // Conflict (e.g., duplicate) → 409
    @ExceptionHandler(ConflictException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleConflict(ConflictException ex) {
        log.warn("Conflict: {}", ex.getMessage());
        return new ErrorResponse(ex.getErrorCode(), ex.getMessage());
    }

    // Bean Validation → 400
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
            .toList();
        log.debug("Validation failed: {}", errors);
        return new ErrorResponse("VALIDATION_ERROR", "Invalid request", errors);
    }

    // Generic fallback → 500
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleGeneric(Exception ex) {
        log.error("Unexpected error", ex);
        return new ErrorResponse("INTERNAL_ERROR", "Internal server error");
    }
}

// ✅ Error response DTO
public record ErrorResponse(
    String code,
    String message,
    List<String> details
) {
    public ErrorResponse(String code, String message) {
        this(code, message, List.of());
    }
}
```

---

## Checked vs Unchecked

**Prefer unchecked exceptions (RuntimeException)** for domain and application errors.

```java
// ✅ Unchecked — caller is not forced to handle it
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long id) {
        super("User not found: " + id);
    }
}

// ❌ Checked — forces try/catch everywhere, pollutes the API
public class UserNotFoundException extends Exception { ... }

// ✅ Checked only when recovery is expected and well-defined
// Example: IOException in I/O that MUST be handled by the caller
```

---

## try-with-resources

```java
// ✅ Guarantees resource closure
try (var connection = dataSource.getConnection();
     var statement = connection.prepareStatement(sql)) {
    statement.setLong(1, userId);
    return statement.executeQuery();
}

// ✅ Custom Closeable
try (var tempFile = Files.createTempFile("export", ".csv")) {
    writeData(tempFile);
    uploadToStorage(tempFile);
}
// tempFile.toFile().delete() is called automatically
```

---

## Best Practices

```java
// ✅ Never swallow exceptions
try {
    process();
} catch (Exception e) {
    log.error("Failed to process", e);  // log and re-throw or propagate
    throw new AppProcessingException("Processing failed", e);
}

// ❌ Swallow — completely hides the error
try {
    process();
} catch (Exception e) {
    // nothing here — very bad
}

// ✅ Preserve root cause when re-throwing
catch (SomeCheckedException e) {
    throw new AppException("WRAPPED", "Error in processing", e);  // passes 'e' as cause
}

// ❌ Loses the original stack trace
catch (SomeCheckedException e) {
    throw new AppException("WRAPPED", e.getMessage());  // without cause
}
```

---

## Antipatterns

| Antipattern | Problem | Fix |
|-------------|---------|-----|
| `catch (Exception e) {}` | Silently swallows error | Log and re-throw or propagate |
| `throws Exception` in signature | Too generic | Declare specific exceptions |
| Checked exceptions in the service layer | Pollutes the API, forces try/catch | Use unchecked |
| Returning `null` to indicate error | NullPointerException out of context | Throw a specific exception |
| Error messages without context | "Error occurred" — unusable | Include resource + id + reason |
