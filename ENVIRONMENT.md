# Variables de entorno

Todas las variables requeridas deben estar definidas en `.env` (copiado de `.env.example`).
**Nunca commitear `.env` con valores reales.**

## Generales

| Variable | Descripción | Requerida | Ejemplo |
|---|---|---|---|
| `APP_ENV` | Entorno de ejecución | ✅ | `development` / `production` |
| `APP_DEBUG` | Modo debug | ✅ | `true` / `false` |
| `LOG_LEVEL` | Nivel de log | ✅ | `INFO` / `DEBUG` |
| `APP_PORT` | Puerto de la aplicación | ✅ | `8000` |

## Base de datos

| Variable | Descripción | Requerida | Ejemplo |
|---|---|---|---|
| `DATABASE_URL` | URL de conexión completa | ✅ | `postgresql+asyncpg://user:pass@localhost:5432/db` |

## Cache (si aplica)

| Variable | Descripción | Requerida | Ejemplo |
|---|---|---|---|
| `REDIS_URL` | URL de conexión Redis | ⚪ | `redis://localhost:6379/0` |

## Seguridad

| Variable | Descripción | Requerida | Ejemplo |
|---|---|---|---|
| `INTERNAL_SECRET` | Secret para llamadas internas | ✅ | `cadena-aleatoria-larga` |

---

> **Completar esta tabla al inicializar el proyecto con las variables específicas del stack y dominio.**

## Variables de desarrollo local

Para desarrollo local, usar `docker-compose.dev.yml` que inyecta valores de prueba automáticamente.

## Generación de secretos

```bash
# Generar secret aleatorio seguro
openssl rand -hex 32
```
