# {PROJECT_NAME}

> Documentación técnica completa del proyecto.

## ¿Qué es este proyecto?

<!-- Describir el propósito y contexto del servicio -->

## Inicio rápido

```bash
git clone https://github.com/olimpus-soft/{PROJECT_NAME}.git
cd {PROJECT_NAME}
cp .env.example .env
make setup
make dev
```

## Navegación

- **Arquitectura** — diagramas, decisiones técnicas, capas del sistema
- **Desarrollo** — setup local, testing, flujo git
- **API** — referencia Swagger, endpoints, autenticación
- **Deployment** — CI/CD, Docker, rollback

## Diagramas de ejemplo

Los diagramas usan **Kroki** — se renderizan vía API, sin conflictos de JS.

### Flujo general del sistema

```kroki-mermaid
graph LR
  Client([Cliente]) --> API[API Gateway]
  API --> App[{PROJECT_NAME}]
  App --> DB[(Base de datos)]
  App --> Cache[(Cache)]
```

### Secuencia de request típico

```kroki-mermaid
sequenceDiagram
  actor User
  participant API
  participant Service
  participant DB

  User->>API: POST /v1/resource
  API->>Service: handle(request)
  Service->>DB: query()
  DB-->>Service: result
  Service-->>API: response
  API-->>User: 201 Created
```

### Modelo de dominio (PlantUML)

```kroki-plantuml
@startuml
entity Entity1 {
  * id : UUID
  --
  name : String
  created_at : DateTime
}

entity Entity2 {
  * id : UUID
  --
  entity1_id : UUID
  value : String
}

Entity1 ||--o{ Entity2 : "has many"
@enduml
```
