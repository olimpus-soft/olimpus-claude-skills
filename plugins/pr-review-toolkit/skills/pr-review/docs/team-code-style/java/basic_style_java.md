# Guía de Estilo Java — Fury Services

Lineamientos para el desarrollo de aplicaciones Java en Fury (Mercado Libre). Aplica a servicios REST, workers y microservicios en general.

---

## Índice

1. [Estructura de paquetes](#1-estructura-de-paquetes)
2. [Arquitectura en capas](#2-arquitectura-en-capas)
3. [Nomenclatura](#3-nomenclatura)
4. [Inyección de dependencias](#4-inyección-de-dependencias)
5. [Controladores REST](#5-controladores-rest)
6. [DTOs y modelos](#6-dtos-y-modelos)
7. [Casos de uso](#7-casos-de-uso)
8. [Gateways](#8-gateways)
9. [Manejo de excepciones](#9-manejo-de-excepciones)
10. [Logging](#10-logging)
11. [Métricas vs Logging](#11-métricas-vs-logging)
12. [Configuración](#12-configuración)
13. [Persistencia](#13-persistencia)
14. [Tests](#14-tests)
15. [Patrones de diseño sobre condicionales](#15-patrones-de-diseño-sobre-condicionales)
16. [GraphQL](#16-graphql)
17. [Reglas generales](#17-reglas-generales)

---

## 1. Estructura de paquetes

El paquete raíz sigue la convención:

```
com.mercadolibre.<equipo>.<servicio>
```

La estructura interna se divide en tres capas principales:

```
src/main/java/com/mercadolibre/<equipo>/<servicio>/
├── entrypoint/          # Capa de presentación (HTTP in/out)
│   ├── controller/      # REST controllers (delegan a use cases)
│   ├── converter/       # Mappers Web DTO ↔ Domain DTO
│   └── dto/
│       ├── request/     # DTOs de entrada
│       └── response/    # DTOs de salida
│
├── core/                # Capa de dominio y lógica de negocio
│   ├── usecase/         # Interfaces + implementaciones de casos de uso
│   ├── dto/
│   │   ├── filter/      # Objetos de filtro/query
│   │   └── data/        # Modelos de dominio
│   ├── gateway/         # Interfaces de contratos con externos
│   ├── exceptions/      # Excepciones de dominio
│   └── util/            # Utilidades de dominio
│
└── infra/               # Capa de infraestructura
    ├── config/          # Beans y configuraciones de Spring
    ├── controller/      # Controllers HTTP (Spring MVC)
    │   └── web/         # Organizados por dominio
    ├── gateway/         # Implementaciones de gateways
    │   ├── rest/        # Clientes HTTP y GraphQL
    │   └── <dominio>/   # Gateways por dominio
    ├── exceptions/      # Excepciones de infraestructura
    └── util/            # Utilidades de infraestructura
```

**Reglas:**
- Organizar por dominio funcional primero, luego por capa técnica.
- `core` no debe depender de `infra` ni de `entrypoint`. El flujo de dependencias es: `entrypoint → core ← infra`.
- Cada dominio tiene su propio subpaquete dentro de cada capa (e.g., `usecase/invoice/`, `gateway/invoice/`).

---

## 2. Arquitectura en capas

Se usa una **arquitectura hexagonal (Ports & Adapters)** con tres capas bien definidas:

```
[HTTP Request]
      ↓
[entrypoint] → Valida y transforma la solicitud HTTP
      ↓
[core / use case] → Ejecuta lógica de negocio pura
      ↓
[infra / gateway] → Interactúa con sistemas externos (DB, APIs, colas)
```

### Responsabilidades por capa

| Capa | Responsabilidad |
|---|---|
| `entrypoint` | Recibir HTTP, validar input, transformar Web DTO ↔ Domain DTO, delegar al controller de core |
| `core` | Contener la lógica de negocio. Sin dependencias de frameworks. |
| `infra` | Implementar contratos (gateways). Integrar con Spring, JPA, REST clients. |

### Flujo de una petición

```
RestController (infra)
  → Controller (entrypoint)       ← convierte DTO y delega
    → UseCase (core)              ← ejecuta lógica de negocio
      → GatewayInterface (core)   ← contrato del dominio
        → GatewayImpl (infra)     ← implementación concreta
```

---

## 3. Nomenclatura

### Clases

| Tipo | Sufijo / Convención | Ejemplo |
|---|---|---|
| REST Controller (Spring) | `*RestController` | `InvoiceRestController` |
| Application Controller | `*Controller` | `InvoiceController` |
| Caso de uso (interfaz) | Verbo + Sustantivo | `SearchPaginatedInvoice` |
| Caso de uso (impl) | `*Impl` | `SearchPaginatedInvoiceImpl` |
| Gateway (interfaz) | `*Gateway` | `InvoiceGateway` |
| Gateway (impl) | `*GatewayImpl` | `InvoiceGatewayImpl` |
| DTO web (request/response) | `*Web` | `InvoiceFilterWeb`, `InvoiceResponseWeb` |
| DTO de dominio | sin sufijo | `InvoiceFilter`, `Invoice` |
| Entidad JPA | `*Entity` | `DownloadInfoEntity` |
| Repository JPA | `*Repository` | `DownloadInfoRepository` |
| Converter / Mapper | `*Converter`, `*Mapper` | `InvoiceFilterConverter` |
| Configuración Spring | `*Config` | `InvoiceControllerConfig` |
| Properties | `*Properties` | `LockProperties` |
| Solver / Resolver | `*Solver` | `InvoiceGatewaySolver` |
| Strategy | `*Strategy` | `GraphQueryStrategy` |

### Métodos

- **camelCase** siempre.
- Prefijos descriptivos por intención:
  - `search*` — búsqueda paginada o filtrada
  - `get*` — obtención directa por ID u otro criterio único
  - `find*` — búsqueda que puede no encontrar resultado
  - `create*` / `save*` — creación
  - `update*` — modificación
  - `delete*` / `remove*` — eliminación
  - `handle*` — manejo de eventos o errores
  - `execute*` / `run*` — ejecución de procesos
  - `is*` / `has*` / `can*` — booleanos
  - `build*` / `map*` — construcción de objetos

### Variables y constantes

- Variables y campos: `camelCase`
- Constantes: `UPPER_SNAKE_CASE`
- Evitar abreviaciones ambiguas. Preferir `invoiceFilter` sobre `invFlt`.

### Paquetes

- Todo en minúsculas, sin separadores.
- Organizados por dominio: `invoice`, `downloadprocess`, `fiscalsummary`.

---

## 4. Inyección de dependencias

**Siempre usar inyección por constructor.** Nunca `@Autowired` en campo ni setter.

```java
// CORRECTO
public InvoiceController(
    InvoiceFilterConverter invoiceFilterConverter,
    SearchPaginatedInvoice searchPaginatedInvoice
) {
    this.invoiceFilterConverter = invoiceFilterConverter;
    this.searchPaginatedInvoice = searchPaginatedInvoice;
}
```

```java
// INCORRECTO — No usar
@Autowired
private InvoiceFilterConverter invoiceFilterConverter;
```

**Definición de beans en clases `@Configuration`:**

```java
@Configuration
public class InvoiceControllerConfig {

    @Bean
    public InvoiceController invoiceController(
        InvoiceFilterConverter converter,
        SearchPaginatedInvoice searchUseCase
    ) {
        return new InvoiceController(converter, searchUseCase);
    }
}
```

- Los `@Bean` de infraestructura van en `infra/config/<dominio>/`.
- Los campos inyectados deben ser `final`.
- Para selección condicional de implementaciones, usar `@Qualifier` explícito en la clase `@Configuration`, no en el punto de inyección.

---

## 5. Controladores REST

### Estructura en dos niveles

**Nivel 1 — `infra/controller/web/`:** recibe HTTP, valida, serializa.

```java
@RestController
@RequestMapping("/search/invoice")
public class InvoiceRestController {

    private final InvoiceController invoiceController;

    public InvoiceRestController(InvoiceController invoiceController) {
        this.invoiceController = invoiceController;
    }

    @PostMapping
    public ResponseEntity<PageableResponseWeb<List<InvoiceResponseWeb>>> search(
        @RequestParam("caller.id") Long callerId,
        @Valid @RequestBody InvoiceFilterWeb filterWeb
    ) {
        return ResponseEntity.ok(invoiceController.search(callerId, filterWeb));
    }
}
```

**Nivel 2 — `entrypoint/controller/`:** convierte DTOs y delega al caso de uso.

```java
public class InvoiceController {

    private final InvoiceFilterConverter filterConverter;
    private final SearchPaginatedInvoice searchPaginatedInvoice;
    private final InvoiceResponseConverter responseConverter;

    public PageableResponseWeb<List<InvoiceResponseWeb>> search(Long callerId, InvoiceFilterWeb filterWeb) {
        InvoiceFilter filter = filterConverter.convert(filterWeb);
        filter.setCallerId(callerId);
        PageableResponse<List<Invoice>> result = searchPaginatedInvoice.execute(filter);
        return responseConverter.convert(result);
    }
}
```

### Convenciones de endpoints

- Plural para colecciones: `/invoices`, `/download_processes`.
- snake_case en paths: `/fiscal_summary`, `/download_process`.
- Parámetro de autenticación: `caller.id` como `@RequestParam`.
- Paginación con `offset` y `limit`.
- Respuestas paginadas envueltas en `PageableResponseWeb<T>`.

### Endpoint de salud `/ping`

El endpoint `/ping` **no debe generar logs de ningún tipo**. Su única función es retornar HTTP 200 para health checks de infraestructura.

```java
@GetMapping("/ping")
public ResponseEntity<String> ping() {
    return ResponseEntity.ok("pong");
}
```

---

## 6. DTOs y modelos

### Separación estricta por capa

| Capa | DTO | Características |
|---|---|---|
| Web (entrypoint) | `*Web` | Jackson, validaciones JSR-380, polimorfismo |
| Dominio (core) | sin sufijo | POJO limpio, sin anotaciones de frameworks |
| Persistencia (infra) | `*Entity` | JPA annotations, extiende `AbstractEntity` |

### DTOs Web

```java
// Usar Jackson para control de serialización
@JsonInclude(JsonInclude.Include.NON_NULL)
public class InvoiceFilterWeb extends BaseFilterWeb {

    @NotNull
    @JsonProperty("date_from")
    private LocalDate dateFrom;

    @NotNull
    @JsonProperty("date_to")
    private LocalDate dateTo;
}
```

### Polimorfismo en DTOs

Para tipos que varían según un discriminador (e.g., `site`):

```java
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.EXTERNAL_PROPERTY,
    property = "site",
    visible = true,
    defaultImpl = InvoiceFilterWeb.class
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = InvoiceMLAFilterWeb.class, name = "MLA"),
    @JsonSubTypes.Type(value = InvoiceMLMFilterWeb.class, name = "MLM")
})
public class InvoiceFilterWeb { ... }
```

### Entidades JPA

```java
@Entity
@Table(name = "download_info", indexes = {
    @Index(name = "idx_caller_id", columnList = "caller_id")
})
public class DownloadInfoEntity extends AbstractEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(name = "caller_id", nullable = false)
    private Long callerId;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private ProcessStatus status;
}
```

### Respuesta paginada estándar

```java
public class PageableResponseWeb<T> {
    private T data;
    private Integer total;
    private Integer limit;
    private Long offset;
    private String lastId;
}
```

---

## 7. Casos de uso

- Definir como **interfaz** en `core/usecase/`.
- Implementar en el mismo paquete con sufijo `Impl`.
- Método principal: `execute(...)` o nombre descriptivo del caso de uso.
- Un caso de uso = una responsabilidad.

```java
// Interfaz en core/usecase/invoice/
public interface SearchPaginatedInvoice {
    PageableResponse<List<Invoice>> execute(InvoiceFilter filter);
}

// Implementación
public class SearchPaginatedInvoiceImpl implements SearchPaginatedInvoice {

    private final InvoiceGateway invoiceGateway;

    public SearchPaginatedInvoiceImpl(InvoiceGateway invoiceGateway) {
        this.invoiceGateway = invoiceGateway;
    }

    @Override
    public PageableResponse<List<Invoice>> execute(InvoiceFilter filter) {
        // lógica de negocio aquí
        return invoiceGateway.search(filter);
    }
}
```

**Reglas:**
- Los casos de uso solo dependen de interfaces (gateways), nunca de implementaciones concretas.
- No importar clases de `infra` ni de `entrypoint` en `core`.
- La orquestación de múltiples casos de uso ocurre en el `Controller` (entrypoint), no en los use cases.

---

## 8. Gateways

### Contrato en core, implementación en infra

```java
// core/gateway/InvoiceGateway.java
public interface InvoiceGateway {
    PageableResponse<List<Invoice>> search(InvoiceFilter filter);
}

// infra/gateway/rest/InvoiceGatewayImpl.java
@Component
public class InvoiceGatewayImpl implements InvoiceGateway {

    private final RestTemplate restTemplate;

    public InvoiceGatewayImpl(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @Override
    public PageableResponse<List<Invoice>> search(InvoiceFilter filter) {
        // llamada HTTP real
    }
}
```

### Solver pattern (múltiples implementaciones)

Cuando hay múltiples implementaciones de un gateway (e.g., por site), usar un Solver:

```java
public class InvoiceGatewaySolverImpl implements InvoiceGateway {

    private final List<InvoiceGateway> gateways;

    public InvoiceGatewaySolverImpl(List<InvoiceGateway> gateways) {
        this.gateways = gateways;
    }

    @Override
    public PageableResponse<List<Invoice>> search(InvoiceFilter filter) {
        return gateways.stream()
            .filter(g -> g.isResponsible(filter))
            .findFirst()
            .orElseThrow(() -> new ExternalServiceException("No gateway found for filter"))
            .search(filter);
    }
}
```

Cada implementación expone `isResponsible(filter)` para determinar si aplica.

---

## 9. Manejo de excepciones

### Jerarquía de excepciones

```
Exception
├── ApiException                      ← base infra, con código y HTTP status
│   └── RequestCallException          ← fallos en llamadas a APIs externas
│
└── Excepciones de dominio (core)
    ├── ProcessNotFoundException       → 404
    ├── ForbiddenException             → 403
    ├── ProcessNotRetryableException   → 422
    ├── ExternalServiceException       → 5xx (configurable)
    ├── InvalidFormatException         → 400
    └── InvalidProcessConfigurationException → 500
```

### Handler global

```java
@ControllerAdvice
public class ControllerExceptionHandler {

    private static final Logger LOGGER = LoggerFactory.getLogger(ControllerExceptionHandler.class);

    @ExceptionHandler(ProcessNotFoundException.class)
    protected ResponseEntity<ApiError> handleNotFound(ProcessNotFoundException e) {
        LOGGER.warn("Not found: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ApiError("not_found", e.getMessage(), 404));
    }

    @ExceptionHandler(ForbiddenException.class)
    protected ResponseEntity<ApiError> handleForbidden(ForbiddenException e) {
        LOGGER.warn("Forbidden: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
            .body(new ApiError("forbidden", e.getMessage(), 403));
    }

    @ExceptionHandler(Exception.class)
    protected ResponseEntity<ApiError> handleUnexpected(Exception e) {
        LOGGER.error("Unexpected error: {}", e.getMessage(), e);
        NewRelic.noticeError(e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ApiError("internal_error", "Unexpected error", 500));
    }
}
```

### Respuesta de error estándar

```java
public class ApiError {
    private String code;     // snake_case, e.g. "not_found"
    private String message;
    private Integer status;
}
```

### Reglas

- Errores **4xx** → log `WARN`.
- Errores **5xx** → log `ERROR` + stack trace + New Relic.
- Las excepciones de dominio viven en `core/exceptions/`, las de infraestructura en `infra/exceptions/`.
- No usar excepciones para control de flujo normal.

---

## 10. Logging

### Declaración del logger

```java
private static final Logger LOGGER = LoggerFactory.getLogger(MyClass.class);
```

Usar siempre **SLF4J**. No usar `System.out.println` ni loggers específicos de implementación.

### Niveles de log

| Nivel | Cuándo usarlo |
|---|---|
| `ERROR` | Fallo inesperado, error 5xx, excepción no controlada |
| `WARN` | Error esperado, validación fallida, recurso no encontrado (4xx) |
| `INFO` | Inicio/fin de procesos críticos, estado de operaciones importantes |
| `DEBUG` | Información de diagnóstico, valores intermedios (solo desarrollo) |
| `TRACE` | Flujo detallado de ejecución (solo desarrollo) |

### Reglas de logging

1. **El endpoint `/ping` nunca debe loguear.** No hay log de entrada, proceso ni salida en este endpoint.

2. **Loguear errores, no pasos del flujo.** Los logs no son trazas de ejecución. No agregar logs como "Entrando al método X", "Procesando filtro Y", "Llamando al gateway Z". Esos mensajes generan ruido, consumen storage y no aportan valor en producción. El flujo se entiende leyendo el código; los logs existen para diagnosticar fallos.

   ```java
   // INCORRECTO — log de flujo sin valor
   LOGGER.info("Starting invoice search for callerId: {}", callerId);
   LOGGER.info("Calling invoice gateway...");
   LOGGER.info("Invoice search completed, found {} results", results.size());

   // CORRECTO — solo cuando algo falla o es realmente excepcional
   LOGGER.error("Invoice gateway failed for callerId {}: {}", callerId, e.getMessage(), e);
   ```

3. **Usar placeholders SLF4J**, nunca concatenación de strings:
   ```java
   // CORRECTO
   LOGGER.error("Error processing invoice {}: {}", invoiceId, e.getMessage(), e);

   // INCORRECTO
   LOGGER.error("Error processing invoice " + invoiceId + ": " + e.getMessage());
   ```

4. **Incluir contexto relevante** en el mensaje: identificadores, parámetros clave que permitan reproducir el error.

5. **No loguear datos sensibles**: contraseñas, tokens, datos personales, números de tarjeta.

6. **MDC para request tracing**: agregar `requestId` al MDC en el inicio de cada request para correlacionar logs distribuidos.

7. **Configuración de Logback por perfil:**

```xml
<!-- Producción: formato estructurado con requestId -->
<pattern>%d{yyyy-MM-dd HH:mm:ss} [level:%p] %c{1} - [requestId:%X{requestId}] %m%n</pattern>

<!-- Local: formato legible con color -->
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} %highlight(%p) [%t] %logger{39}: %m%n</pattern>
```

8. En producción y stage, usar **AsyncAppender** con queue de al menos 10000 para no bloquear el hilo de request.

---

## 11. Métricas vs Logging

### Principio fundamental

**Las métricas miden; los logs diagnostican fallos.** No son intercambiables.

Cuando se quiere saber *cuántas veces ocurrió algo*, *con qué frecuencia falla un servicio*, o *cuánto tarda una operación*, la respuesta correcta es una **métrica**, no un log. Los logs que solo registran conteos o estados normales deben eliminarse y reemplazarse por métricas.

| Pregunta | Herramienta correcta |
|---|---|
| ¿Cuántas facturas se procesaron hoy? | Métrica (counter) |
| ¿Cuánto tarda el gateway de facturas? | Métrica (histogram/timer) |
| ¿Qué porcentaje de requests fallan? | Métrica (counter de errores / total) |
| ¿Qué pasó exactamente cuando falló el proceso X? | Log (ERROR con contexto) |
| ¿Qué datos recibió el request que causó el error? | Log (WARN/ERROR con datos del request) |

### Cuándo usar métrica

- Contadores de operaciones exitosas o fallidas.
- Latencia de llamadas a servicios externos.
- Tamaño de queues o backlog.
- Tasa de uso de features (feature flags activados).
- Cualquier dato que se quiera graficar, alertar o monitorear en el tiempo.

```java
// CORRECTO — métrica para medir volumen
metricsClient.incrementCounter("invoice.search.success", tags);
metricsClient.recordTimer("invoice.gateway.latency", duration, tags);

// INCORRECTO — log como sustituto de métrica
LOGGER.info("Invoice search completed successfully for site {}", site); // ← ruido puro
```

### Cuándo usar log

- Cuando **algo falló** y se necesita contexto para diagnosticarlo.
- Cuando ocurre un evento excepcional que no es el camino feliz.
- Cuando se necesita trazar la causa raíz de un error específico.

```java
// CORRECTO — log de error con contexto diagnóstico
LOGGER.error("Invoice gateway timeout for callerId={}, site={}, elapsed={}ms",
    callerId, site, elapsed, e);

// INCORRECTO — log de camino feliz que no aporta información diagnóstica
LOGGER.info("Invoice gateway responded in {}ms", elapsed); // usar métrica de latencia
```

### Regla práctica

> Antes de agregar un `LOGGER.info(...)`, preguntarse: **¿alguien va a leer este log para diagnosticar un problema?** Si la respuesta es no, usar una métrica o no registrar nada.

---

## 12. Configuración

### Archivos de configuración

```
src/main/resources/
├── application.yml                  # Base
├── application-local.yml
├── application-test.yml
├── application-stage.yml
├── application-prod.yml
├── application-integration_test.yml
└── configurations/
    ├── url-template-*.json          # Templates de URLs externas
    └── flags-config.json            # Feature flags locales
```

El perfil activo se controla con la variable de entorno `SCOPE_SUFFIX`.

### Clases de propiedades tipadas

Preferir `@ConfigurationProperties` sobre `@Value` para grupos de propiedades relacionadas:

```java
@ConfigurationProperties(prefix = "lock")
public class LockProperties {
    private int ttl;
    private String prefix;
    // getters / setters
}
```

### Configuraciones importantes de Spring

```yaml
spring:
  jpa:
    open-in-view: false           # Evitar lazy loading fuera de transacción

  mvc:
    throw-exception-if-no-handler-found: true

  web:
    resources:
      add-mappings: false         # Deshabilitar recursos estáticos

server:
  compression:
    enabled: true
    mime-types: application/json,text/plain
```

### ObjectMapper global

Registrar un único `ObjectMapper` configurado como bean:

```java
@Bean
public ObjectMapper objectMapper() {
    return new ObjectMapper()
        .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
        .registerModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .setSerializationInclusion(JsonInclude.Include.NON_NULL);
}
```

---

## 12. Persistencia

### Entidades

- Extender `AbstractEntity` para campos de auditoría (`createdAt`, `updatedAt`).
- UUIDs como PKs: `@GeneratedValue(strategy = GenerationType.UUID)`.
- Nombres de tablas en snake_case.
- Definir índices donde se harán consultas frecuentes.

### Repositorios

Usar Spring Data JPA. Definir queries complejas con `@Query`:

```java
@Repository
public interface DownloadInfoRepository extends JpaRepository<DownloadInfoEntity, String> {

    Optional<DownloadInfoEntity> findByCallerIdAndStatus(Long callerId, ProcessStatus status);

    @Modifying
    @Query("UPDATE DownloadInfoEntity d SET d.status = :status WHERE d.id = :id")
    void updateStatus(@Param("id") String id, @Param("status") ProcessStatus status);
}
```

### Reglas

- Los repositorios viven en `infra/gateway/<dominio>/`.
- No exponer entidades JPA fuera de la capa `infra`. Convertir a DTOs de dominio en el gateway.
- No usar `open-in-view: true`.
- Usar transacciones explícitas (`@Transactional`) en los métodos de escritura.

---

## 13. Tests

### Estructura

Espeja exactamente la estructura de `src/main/java`:

```
src/test/java/com/mercadolibre/<equipo>/<servicio>/
├── entrypoint/
│   └── controller/
├── core/
│   └── usecase/
└── infra/
    ├── controller/web/
    └── gateway/
```

### Nomenclatura

- Tests unitarios: `*Test` o `*UnitTest`
- Tests de integración: `*IntegrationTest`
- Tests de arquitectura: `*ArchTest`

### Frameworks

- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito para mocks
- MockMvc para tests de controllers
- H2 para tests de integración con BD
- ArchUnit para validar reglas de arquitectura

### Ejemplo de test de REST Controller

```java
@ExtendWith(MockitoExtension.class)
class InvoiceRestControllerUnitTest {

    @Mock
    private InvoiceController invoiceController;

    @InjectMocks
    private InvoiceRestController underTest;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders
            .standaloneSetup(underTest)
            .setControllerAdvice(new ControllerExceptionHandler())
            .build();
    }

    @Test
    void shouldReturn200WhenSearchIsSuccessful() throws Exception {
        // given
        when(invoiceController.search(anyLong(), any())).thenReturn(buildResponse());

        // when / then
        mockMvc.perform(post("/search/invoice")
            .param("caller.id", "123")
            .contentType(MediaType.APPLICATION_JSON)
            .content("""
                { "site": "MLA", "date_from": "2024-01-01", "date_to": "2024-12-31" }
            """))
            .andExpect(status().isOk());
    }
}
```

### Cobertura

JaCoCo configurado en CI. Excluir de cobertura:
- DTOs
- Entidades JPA
- Clases `*Config`
- Converters simples
- Excepciones

---

## 15. Patrones de diseño sobre condicionales

### Principio

**Un bloque de `if/else` o `switch` que crece con el tiempo es una señal de que falta un patrón de diseño.** Cada vez que se agrega un nuevo `else if` para manejar un caso nuevo (un site, un tipo, un estado), se está acoplando la lógica y dificultando la extensión. La solución no es más condiciones, es el patrón correcto.

### Strategy — en lugar de if por tipo o site

**Antes (problemático):**
```java
public PageableResponse<List<Invoice>> search(InvoiceFilter filter) {
    if ("MLA".equals(filter.getSite())) {
        return searchMLA(filter);
    } else if ("MLM".equals(filter.getSite())) {
        return searchMLM(filter);
    } else if ("MLC".equals(filter.getSite())) {
        return searchMLC(filter);
    }
    throw new IllegalArgumentException("Unknown site");
}
```

**Después (correcto):**
```java
public interface InvoiceStrategy {
    boolean isResponsible(InvoiceFilter filter);
    PageableResponse<List<Invoice>> execute(InvoiceFilter filter);
}

// Resolver en infra, cada Strategy en su clase
public class InvoiceStrategySolver {
    private final List<InvoiceStrategy> strategies;

    public PageableResponse<List<Invoice>> search(InvoiceFilter filter) {
        return strategies.stream()
            .filter(s -> s.isResponsible(filter))
            .findFirst()
            .orElseThrow(() -> new ExternalServiceException("No strategy for site " + filter.getSite()))
            .execute(filter);
    }
}
```

Agregar un nuevo site = agregar una nueva clase, sin tocar el solver ni las demás estrategias.

### Factory Map — en lugar de switch para instanciar objetos

**Antes (problemático):**
```java
public GraphQueryStrategy getStrategy(String site) {
    switch (site) {
        case "MLA": return new GraphQueryMLA();
        case "MLM": return new GraphQueryMLM();
        default: throw new IllegalArgumentException("Unknown site: " + site);
    }
}
```

**Después (correcto):**
```java
// En @Configuration
@Bean
public Map<String, GraphQueryStrategy> graphQueryStrategies(
    @Qualifier("graphQueryMLA") GraphQueryStrategy mla,
    @Qualifier("graphQueryMLM") GraphQueryStrategy mlm
) {
    return Map.of("MLA", mla, "MLM", mlm);
}

// En el servicio
public GraphQueryStrategy getStrategy(String site) {
    return Optional.ofNullable(strategies.get(site))
        .orElseThrow(() -> new ExternalServiceException("No strategy for site: " + site));
}
```

### Template Method — en lugar de if para variaciones de flujo

Cuando un flujo tiene pasos comunes y pasos que varían por subtipo, usar herencia controlada en lugar de condiciones internas.

```java
// Base con flujo común
public abstract class BaseDownloadProcess {
    public final ProcessResult execute(ProcessFilter filter) {
        validate(filter);
        ProcessResult result = doExecute(filter);  // varía por subtipo
        notify(result);
        return result;
    }
    protected abstract ProcessResult doExecute(ProcessFilter filter);
}

// Cada subtipo implementa solo lo que cambia
public class CsvDownloadProcess extends BaseDownloadProcess {
    @Override
    protected ProcessResult doExecute(ProcessFilter filter) { ... }
}
```

### Adapter (Gateway)

Ver sección [8. Gateways](#8-gateways). El patrón gateway es la forma correcta de encapsular las diferencias entre sistemas externos en lugar de dispersar condicionales por el código de dominio.

### Builder — en lugar de constructores con muchos parámetros

Cuando un objeto tiene más de 3 parámetros opcionales, usar Builder evita el anti-patrón de llamadas como `new Process(null, null, true, false, null, "MLA")`.

```java
@Builder
public class ProcessFilter {
    private final Long callerId;
    private final String site;
    private final LocalDate dateFrom;
    private final LocalDate dateTo;
    private final Integer limit;
    private final Long offset;
}

// Uso claro e ilegible sin ambigüedad
ProcessFilter.builder()
    .callerId(123L)
    .site("MLA")
    .dateFrom(LocalDate.of(2024, 1, 1))
    .build();
```

### Solver (orquestador de strategies)

Ver sección [8. Gateways — Solver pattern](#8-gateways).

### Cuándo sí usar if

Los condicionales simples y estables son correctos. El problema es cuando el `if` es un punto de extensión que crece:

- **Correcto:** `if (result == null) throw new NotFoundException(...)` — condición de guarda, no extensible.
- **Correcto:** `if (filter.getLimit() > MAX_LIMIT) filter.setLimit(MAX_LIMIT)` — validación simple.
- **Señal de alerta:** `if ("A".equals(type)) ... else if ("B".equals(type)) ... else if ("C".equals(type))` — cada caso nuevo rompe el principio Open/Closed.

---

## 16. GraphQL

### Framework

Netflix DGS (`dgs-starter`). Definir el schema en:

```
src/main/resources/schema/schema.graphqls
```

### Estrategias por site

```java
public interface GraphQueryStrategy {
    boolean isResponsible(InvoiceFilter filter);
    String buildQuery(InvoiceFilter filter);
    String buildProjection();
}

@Component("graphQueryMLA")
public class GraphQueryMLA implements GraphQueryStrategy {
    @Override
    public boolean isResponsible(InvoiceFilter filter) {
        return filter instanceof InvoiceMLAFilter;
    }
    // ...
}
```

### Configuración de estrategias

```java
@Configuration
public class InvoiceGraphConfig {

    @Bean
    public Map<String, GraphQueryStrategy> graphQueryStrategies(
        @Qualifier("graphQueryMLA") GraphQueryStrategy mla,
        @Qualifier("graphQueryMLM") GraphQueryStrategy mlm
    ) {
        return Map.of("MLA", mla, "MLM", mlm);
    }
}
```

### ObjectMapper para GraphQL

El cliente GraphQL debe usar un `ObjectMapper` con `MapperFeature.ACCEPT_CASE_INSENSITIVE_PROPERTIES` para tolerancia en respuestas externas.

### Generación de código

Usar el plugin `com.netflix.dgs.codegen` para generar tipos type-safe a partir del schema. El código generado va en un paquete `generated.graph`.

---

## 17. Reglas generales

### Código

- **Java 17+**: usar records, pattern matching, sealed classes donde aplique.
- **Inmutabilidad**: preferir campos `final`. Evitar mutación de estado.
- **Evitar nulos**: usar `Optional<T>` en lugar de retornar `null`. Validar en los límites del sistema.
- **No mezclar capas**: core no puede importar clases de infra o entrypoint.
- **Un archivo = una clase pública**.
- Máximo ~300 líneas por clase. Si es mayor, considerar dividir responsabilidades.

### Asincronismo

- Usar `@Async` con un `ExecutorService` nombrado explícitamente.
- Configurar pool en `application.yml` bajo `async.executor`.
- Nunca bloquear threads del HTTP server con operaciones largas.

### Seguridad

- No loguear datos sensibles (tokens, contraseñas, PII).
- Validar siempre el input en los límites del sistema (`@Valid` en `@RequestBody`).
- Usar secrets via Fury Secrets Service, nunca hardcodear credenciales.
- Aplicar rate limiting donde el endpoint sea público o de alto volumen.

### Métricas y observabilidad

- Registrar métricas de negocio clave (requests procesados, errores, latencia) con el cliente de métricas de Meli.
- Preferir métricas sobre logs para medir volumen, frecuencia y latencia. Ver sección [11. Métricas vs Logging](#11-métricas-vs-logging).
- Integrar New Relic APM: `NewRelic.noticeError(e)` para errores no esperados.
- Propagar `requestId` en MDC para correlación de logs.

### Build

- Gradle como build tool.
- Usar `io.spring.dependency-management` para gestión de versiones.
- JaCoCo para reportes de cobertura.
- Tener perfil `integration_test` separado del perfil `test`.

### Documentación

- Documentar endpoints con SpringDoc/OpenAPI (`springdoc-openapi-starter-webmvc-ui`).
- Los `@Bean` no triviales deben tener un comentario breve sobre su propósito.
- No agregar Javadoc a métodos cuyo nombre ya es autoexplicativo.
