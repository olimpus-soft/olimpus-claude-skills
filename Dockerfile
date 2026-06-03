# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile genérico — OlimpusSoft template
#
# Reemplazar este archivo con el Dockerfile específico del stack del proyecto.
# Ver ejemplos en docs/guide/deployment.md
# ─────────────────────────────────────────────────────────────────────────────

# TODO: Elegir imagen base según el stack
# Ejemplos:
#   FROM python:3.13-slim AS builder
#   FROM golang:1.22-alpine AS builder
#   FROM node:22-alpine AS builder

FROM alpine:3.20 AS builder

WORKDIR /app

# TODO: Instalar dependencias del proyecto
# RUN ...

# TODO: Copiar y construir la aplicación
# COPY . .
# RUN ...

# ── Runtime ───────────────────────────────────────────────────────────────────
FROM alpine:3.20 AS runtime

WORKDIR /app

# Aplicar parches de seguridad del SO
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Usuario no-root
RUN addgroup -S app && adduser -S -G app app

# TODO: Copiar artefactos del builder
# COPY --from=builder /app/bin /app/bin

# Variables de entorno básicas
ENV APP_ENV=production \
    APP_PORT=8000

# Health check — ajustar path y puerto según el stack
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:${APP_PORT}/health || exit 1

USER app

# TODO: Ajustar puerto según la aplicación
EXPOSE 8000

# TODO: Definir el entrypoint
# ENTRYPOINT ["/app/bin/server"]
# CMD ["--config", "/app/config.yaml"]
