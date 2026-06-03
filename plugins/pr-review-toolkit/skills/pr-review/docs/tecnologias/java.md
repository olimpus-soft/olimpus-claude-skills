# ☕ Análisis Técnico — Java / Spring Boot / Kotlin

Cargar cuando se detecta `pom.xml` o `build.gradle`. Complementa `03-tecnico-core.md`.

---

## 1. Anotaciones Spring

```java
// ❌ Field injection (difícil de testear, acoplado)
@Autowired
private UserService userService;

// ✅ Constructor injection (recomendado)
@RequiredArgsConstructor   // Lombok
public class UserController {
    private final UserService userService;
}
```

- [ ] ¿Se usa `@RestController` para APIs, `@Service` para lógica, `@Repository` para datos?
- [ ] ¿Constructor injection en lugar de field injection?

---

## 2. JPA / Hibernate — N+1 y transacciones

```java
// ❌ N+1 queries
orders.forEach(o -> System.out.println(o.getCustomer().getName()));

// ✅ JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.customer")
List<Order> findAllWithCustomer();

// ✅ O EntityGraph
@EntityGraph(attributePaths = {"customer"})
List<Order> findAll();
```

```java
// ✅ @Transactional en capa de servicio
@Service
public class OrderService {
    @Transactional(readOnly = true)   // lecturas
    public Order findById(Long id) { ... }

    @Transactional                    // escrituras
    public Order createOrder(OrderDTO dto) { ... }

    @Transactional(rollbackFor = BusinessException.class)
    public void processOrder(Long id) { ... }
}
```

- [ ] ¿`@Transactional` está en servicio, no en controller ni repository?
- [ ] ¿`readOnly = true` en queries de lectura?
- [ ] ¿Queries de lista usan JOIN FETCH o EntityGraph?

---

## 3. Validaciones

```java
// ✅ Bean Validation en DTOs
public class UserDTO {
    @NotBlank @Size(min = 2, max = 100)
    private String name;

    @Email @NotNull
    private String email;
}

// ✅ Activar en el controller
@PostMapping("/users")
public ResponseEntity<User> create(@Valid @RequestBody UserDTO dto) { ... }
```

---

## 4. Manejo de excepciones centralizado

```java
// ✅ Un solo handler para todo el proyecto
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(EntityNotFoundException e) {
        return ResponseEntity.status(404)
            .body(new ErrorResponse("NOT_FOUND", e.getMessage()));
    }

    // NO exponer stack trace en producción
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity.status(500)
            .body(new ErrorResponse("INTERNAL_ERROR", "An error occurred"));
    }
}
```

---

## 5. Configuración externalizada

```yaml
# ✅ Variables de entorno para secrets
spring:
  datasource:
    url: ${DB_URL}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```

```java
// ✅ Type-safe configuration
@ConfigurationProperties(prefix = "app.api")
@Validated
public class ApiProperties {
    @NotBlank
    private String baseUrl;
    @Min(1000) @Max(30000)
    private int timeout = 5000;
}
```

---

## 6. Logging

```java
// ✅ SLF4J con placeholders (no concatenación)
@Slf4j
@Service
public class OrderService {
    public void process(Long id) {
        log.info("Processing order: {}", id);
        try {
            // ...
        } catch (Exception e) {
            log.error("Error processing order {}: {}", id, e.getMessage(), e);
        }
    }
}
```

| Nivel | Cuándo usarlo |
|---|---|
| `ERROR` | Fallo inesperado, error 5xx, excepción no controlada |
| `WARN` | Error esperado, validación fallida, recurso no encontrado (4xx) |
| `INFO` | Inicio/fin de procesos críticos únicamente |
| `DEBUG` | Diagnóstico en desarrollo, nunca en producción |

- [ ] ¿Se usan placeholders `{}` en lugar de concatenación de strings?
- [ ] ¿Errores loggean el objeto `e` para el stack trace?
- [ ] ¿No hay logs de flujo normal (`"Entrando al método X"`, `"Llamando al gateway Y"`)?
- [ ] ¿No se loggean datos sensibles (tokens, contraseñas, PII)?

---

## 7. Métricas vs Logging

**Las métricas miden; los logs diagnostican fallos.** No son intercambiables.

| Pregunta | Herramienta correcta |
|---|---|
| ¿Cuántas veces ocurrió X? | Métrica (counter) |
| ¿Cuánto tarda la operación Y? | Métrica (histogram/timer) |
| ¿Qué pasó exactamente cuando falló Z? | Log (ERROR con contexto) |

```java
// ✅ Métrica para medir volumen y latencia
metricsClient.incrementCounter("invoice.search.success", tags);
metricsClient.recordTimer("invoice.gateway.latency", duration, tags);

// ❌ Log como sustituto de métrica — ruido puro
LOGGER.info("Invoice search completed successfully for site {}", site);
```

> Antes de agregar un `LOGGER.info(...)`: ¿alguien va a leer este log para diagnosticar un problema? Si la respuesta es no, usar métrica o no registrar nada.

- [ ] ¿Los conteos y latencias usan métricas, no logs?
- [ ] ¿Los logs INFO solo aparecen en eventos excepcionales o de fallo?

---

## 8. Patrones de diseño sobre condicionales

**Un `if/else` que crece con el tiempo es señal de que falta un patrón.** Cada `else if` nuevo para manejar un caso (un tipo, un estado) acopla la lógica y dificulta la extensión.

### Strategy — en lugar de if por tipo

```java
// ❌ Problemático: agregar un caso nuevo = modificar este método
public Result process(Filter filter) {
    if ("A".equals(filter.getType())) return processA(filter);
    else if ("B".equals(filter.getType())) return processB(filter);
    throw new IllegalArgumentException("Unknown type");
}

// ✅ Correcto: agregar un caso nuevo = agregar una clase nueva
public interface ProcessStrategy {
    boolean isResponsible(Filter filter);
    Result execute(Filter filter);
}
// Resolver elige la estrategia; cada tipo tiene su clase
```

### Factory Map — en lugar de switch para instanciar

```java
// ❌ Problemático
switch (type) {
    case "A": return new ProcessorA();
    case "B": return new ProcessorB();
}

// ✅ Correcto
Map<String, Processor> processors = Map.of("A", processorA, "B", processorB);
return Optional.ofNullable(processors.get(type))
    .orElseThrow(() -> new NotFoundException("No processor for: " + type));
```

### Builder — en lugar de constructores con muchos parámetros

```java
// ❌ Ilegible: new Process(null, null, true, false, null, "MLA")

// ✅ Builder
@Builder
public class ProcessFilter {
    private final Long callerId;
    private final String site;
    private final LocalDate dateFrom;
}
ProcessFilter.builder().callerId(123L).site("MLA").build();
```

- [ ] ¿Los `if/else` por tipo o estado son candidatos a Strategy o Factory Map?
- [ ] ¿Los objetos con más de 3 parámetros opcionales usan Builder?

---

## 9. Testing

```java
// ✅ JUnit 5 + Mockito
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock UserRepository userRepository;
    @InjectMocks UserService userService;

    @Test
    void shouldFindUserById() {
        when(userRepository.findById(1L)).thenReturn(Optional.of(new User("John")));

        User result = userService.findById(1L);

        assertThat(result.getName()).isEqualTo("John");
        verify(userRepository).findById(1L);
    }
}
```

---

## 10. Checklist Java/Spring

- [ ] Constructor injection en lugar de field injection
- [ ] `@Transactional` solo en capa de servicio
- [ ] Queries sin N+1 (JOIN FETCH / EntityGraph)
- [ ] Bean Validation en DTOs con `@Valid`
- [ ] Manejo de excepciones centralizado (`@RestControllerAdvice`)
- [ ] Logging con placeholders SLF4J, sin concatenación
- [ ] Sin logs de flujo normal — solo errores y eventos críticos
- [ ] Métricas para conteos y latencia, no logs
- [ ] Configuración externalizada en variables de entorno
- [ ] Tests unitarios con Mockito + JUnit 5
- [ ] `if/else` por tipo reemplazados por Strategy o Factory Map
- [ ] Builder para objetos con más de 3 parámetros opcionales
