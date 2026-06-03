# Análisis de la Aplicación

> Documento técnico de referencia: arquitectura, dominio, decisiones y contexto del sistema.
> Mantener actualizado con cada cambio arquitectónico significativo.

## Resumen ejecutivo

| Campo | Valor |
|---|---|
| **Nombre** | `{PROJECT_NAME}` |
| **Tipo** | `<!-- ej. API REST, servicio de workers, BFF, microservicio -->` |
| **Dominio** | `<!-- ej. autenticación, streaming, pagos -->` |
| **Estado** | `<!-- En desarrollo / Producción / Deprecado -->` |
| **Versión actual** | `<!-- ej. 1.0.0 -->` |
| **Responsable** | Miguel Morales |

## Propósito y contexto

<!-- Describir qué problema resuelve este servicio, quién lo usa y por qué existe -->

## Arquitectura

<!-- Describir el patrón arquitectónico elegido y sus capas -->

### Patrón arquitectónico

`<!-- ej. Hexagonal (Ports & Adapters), MVC, Layered, Event-Driven -->`

### Diagrama de alto nivel

```
<!-- Completar con diagrama en formato texto o referencia a docs/guide/ -->

[Cliente] → [API Gateway] → [{PROJECT_NAME}] → [Base de datos]
                                              → [Cache]
                                              → [Servicios externos]
```

### Capas del sistema

| Capa | Responsabilidad | Directorio |
|---|---|---|
| `<!-- Dominio -->` | `<!-- Lógica de negocio pura -->` | `<!-- src/domain/ -->` |
| `<!-- Aplicación -->` | `<!-- Casos de uso / orquestación -->` | `<!-- src/application/ -->` |
| `<!-- Infraestructura -->` | `<!-- Adaptadores externos -->` | `<!-- src/infrastructure/ -->` |

## Módulos principales

<!-- Describir los módulos o bounded contexts del sistema -->

| Módulo | Responsabilidad |
|---|---|
| `<!-- TODO -->` | `<!-- TODO -->` |

## Dependencias externas

| Servicio | Propósito | Criticidad |
|---|---|---|
| `<!-- Base de datos -->` | `<!-- Persistencia -->` | Alta |
| `<!-- Cache -->` | `<!-- Caché de sesiones/datos -->` | Media |

## Decisiones técnicas

<!-- Registrar decisiones de arquitectura con su justificación (ADRs ligeros) -->

| Fecha | Decisión | Justificación |
|---|---|---|
| `YYYY-MM-DD` | `<!-- Qué se decidió -->` | `<!-- Por qué -->` |

## Flujos críticos

<!-- Describir los flujos de negocio más importantes del sistema -->

### Flujo 1: `{nombre}`

```
1. ...
2. ...
3. ...
```

## Métricas y SLAs

| Métrica | Objetivo |
|---|---|
| Disponibilidad | 99.9% |
| Latencia p99 | `<!-- TODO: ej. < 200ms -->` |
| Cobertura de tests | >= 97% |

## Riesgos conocidos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| `<!-- TODO -->` | `<!-- Alto/Medio/Bajo -->` | `<!-- TODO -->` |

## Referencias

- [Documentación completa](docs/guide/)
- [API Reference](docs/swagger/)
- [CHANGELOG](CHANGELOG.md)
