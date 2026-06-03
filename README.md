# {PROJECT_NAME}

> {Descripción corta del proyecto — qué hace y para qué existe}

[![CI](https://github.com/olimpus-soft/{PROJECT_NAME}/actions/workflows/ci.yml/badge.svg)](https://github.com/olimpus-soft/{PROJECT_NAME}/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/olimpus-soft/{PROJECT_NAME}/branch/main/graph/badge.svg)](https://codecov.io/gh/olimpus-soft/{PROJECT_NAME})
[![License](https://img.shields.io/badge/license-Propietario-red.svg)](LICENSE.txt)
[![Confidential](https://img.shields.io/badge/acceso-privado%20y%20confidencial-critical.svg)](LEGAL.md)

## Descripción

<!-- Explicar el problema que resuelve, el contexto de negocio y los usuarios objetivo -->

## Documentación

- [Guía completa](docs/guide/) — arquitectura, flujos, diagramas
- [API Reference](docs/swagger/) — Swagger / OpenAPI
- [Changelog](CHANGELOG.md)
- [Contribuir](CONTRIBUTING.md)
- [Deployment](DEPLOYMENT.md)
- [Seguridad](SECURITY.md)

## Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/olimpus-soft/{PROJECT_NAME}.git
cd {PROJECT_NAME}

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con los valores correspondientes

# 3. Levantar infraestructura y correr la app
make setup
make dev
```

## Comandos principales

| Comando | Descripción |
|---|---|
| `make dev` | Levantar servidor en modo desarrollo |
| `make test` | Ejecutar tests con cobertura |
| `make lint` | Verificar estilo de código |
| `make format` | Formatear código |
| `make build` | Construir imagen Docker |

Ver todos los comandos disponibles: `make help`

## Stack

<!-- Completar al inicializar el proyecto -->
- **Lenguaje:** `TODO`
- **Framework:** `TODO`
- **Base de datos:** `TODO`
- **Cache:** `TODO`

## Requisitos

- Docker >= 24
- Docker Compose >= 2.20
- `<!-- TODO: agregar requisitos específicos del stack -->`

## Licencia y Propiedad Intelectual

**Software privado y confidencial. Todos los derechos reservados.**
Copyright © 2026 Olimpus Soft SAS — Miguel Ángel Morales Coterio.

El uso de este software requiere contrato escrito con Olimpus Soft SAS.
Ver [LICENSE.txt](LICENSE.txt) y [LEGAL.md](LEGAL.md) para los términos completos.
