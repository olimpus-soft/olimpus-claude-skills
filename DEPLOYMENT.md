# Guía de Deployment

## Ambientes

| Ambiente | Rama | URL |
|---|---|---|
| Development | `develop` | `http://localhost:{PORT}` |
| Staging | `release/*` | `<!-- TODO: URL de staging -->` |
| Production | `main` | `<!-- TODO: URL de producción -->` |

## Requisitos del servidor

- Docker >= 24
- Docker Compose >= 2.20
- `<!-- TODO: especificar recursos mínimos (CPU/RAM) -->`

## Variables de entorno

Ver [ENVIRONMENT.md](ENVIRONMENT.md) para la lista completa de variables requeridas.

## Deploy manual (VPS)

```bash
# Conectar al servidor
ssh olimpus-vps-claude

# Ir al directorio del proyecto
cd /opt/apps/{PROJECT_NAME}

# Actualizar código
git pull origin main

# Construir y reiniciar
docker compose build
docker compose up -d --no-deps --remove-orphans

# Verificar health
curl -sf http://localhost:{PORT}/health
```

## Deploy automático (CI/CD)

El workflow `cd.yml` se dispara automáticamente al hacer merge en `main`.

**Pasos del workflow:**
1. Conectar al VPS vía SSH
2. `git pull origin main`
3. `docker compose build`
4. Aplicar migraciones (si aplica)
5. `docker compose up -d`
6. Health check con retry (12 intentos, 5s entre cada uno)
7. Limpieza de imágenes antiguas

## Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `VPS_HOST` | IP del servidor |
| `VPS_USER` | Usuario SSH |
| `VPS_SSH_KEY` | Clave privada SSH |
| `VPS_PORT` | Puerto SSH (default 22) |

## Rollback

```bash
# En el servidor — revertir al commit anterior
git log --oneline -5
git checkout {commit-hash}
docker compose build && docker compose up -d
```

## Health check

El servicio expone un endpoint de salud en `{HEALTH_CHECK_PATH}` que retorna `200 OK` cuando está listo.

```bash
curl -sf http://localhost:{PORT}/health
```

## Logs

```bash
# Ver logs del contenedor
docker compose logs -f --tail=100

# Logs de un servicio específico
docker compose logs -f {service-name} --tail=50
```
