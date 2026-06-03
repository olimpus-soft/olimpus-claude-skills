# Diagramas de Arquitectura

> Todos los diagramas se renderizan con **Kroki** (kroki.io), que procesa los diagramas server-side.
> Esto evita el bug de Mermaid cuando hay múltiples diagramas en una misma página.
>
> Tipos soportados: `kroki-mermaid`, `kroki-plantuml`, `kroki-graphviz`, `kroki-c4plantuml`, `kroki-erd`

---

## Diagrama de componentes

```kroki-mermaid
graph TB
  subgraph Cliente
    FE[Frontend]
  end

  subgraph Infraestructura
    GW[API Gateway / Nginx]
  end

  subgraph Aplicación
    APP[{PROJECT_NAME}]
    WORKER[Worker / Background Jobs]
  end

  subgraph Persistencia
    DB[(PostgreSQL)]
    CACHE[(Redis)]
  end

  FE --> GW
  GW --> APP
  APP --> DB
  APP --> CACHE
  APP --> WORKER
  WORKER --> DB
```

---

## Diagrama de capas (Hexagonal)

```kroki-mermaid
graph TB
  subgraph Domain["Dominio (core)"]
    E[Entities]
    VP[Value Objects]
    P[Ports / Interfaces]
  end

  subgraph Application["Aplicación"]
    UC[Use Cases]
    S[Services]
  end

  subgraph Infrastructure["Infraestructura (adaptadores)"]
    API[REST API]
    REPO[Repositories]
    EXT[External Services]
  end

  API --> UC
  UC --> E
  UC --> P
  REPO --> P
  EXT --> P
```

---

## Diagrama de secuencia — Request típico

```kroki-mermaid
sequenceDiagram
  actor Client
  participant API as REST API
  participant UC as Use Case
  participant Repo as Repository
  participant DB as PostgreSQL

  Client->>API: HTTP Request
  API->>UC: execute(command)
  UC->>Repo: find / save
  Repo->>DB: SQL Query
  DB-->>Repo: Result
  Repo-->>UC: Entity
  UC-->>API: Response DTO
  API-->>Client: HTTP Response
```

---

## Modelo de datos (ERD)

```kroki-plantuml
@startuml
hide circle
skinparam linetype ortho

entity "Tabla1" as t1 {
  * id : uuid <<PK>>
  --
  campo1 : varchar(255)
  created_at : timestamp
  updated_at : timestamp
}

entity "Tabla2" as t2 {
  * id : uuid <<PK>>
  --
  * tabla1_id : uuid <<FK>>
  valor : text
}

t1 ||--o{ t2 : "tiene"
@enduml
```

---

## Flujo de CI/CD

```kroki-mermaid
graph LR
  DEV[Developer] -->|push| GH[GitHub]
  GH -->|PR trigger| CI[CI — Tests + Lint]
  CI -->|green| REV[Code Review]
  REV -->|approved| MERGE[Merge to develop]
  MERGE -->|merge to main| CD[CD — Deploy VPS]
  CD --> HEALTH[Health Check]
  HEALTH -->|ok| DONE[✓ Deploy exitoso]
  HEALTH -->|fail| ROLL[Rollback + Alerta]
```
