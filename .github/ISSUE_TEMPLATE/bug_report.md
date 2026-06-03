---
name: Bug Report
about: Reportar un comportamiento inesperado
title: 'fix: '
labels: bug
assignees: ''
---

## Descripción del bug

<!-- Descripción clara y concisa del problema -->

## Pasos para reproducir

1. Llamar a `{METHOD} /v1/{endpoint}` con body `{...}`
2. Respuesta recibida: `...`
3. Error observado: `...`

## Comportamiento esperado

<!-- ¿Qué debería pasar? -->

## Comportamiento actual

<!-- ¿Qué pasa en realidad? -->

## Entorno

- Versión/commit: `git rev-parse --short HEAD`
- `APP_ENV`: development / production
- Docker: `docker --version`

## Logs relevantes

```
# Pegar aquí logs del contenedor (sin datos sensibles)
docker compose logs app --tail=50
```

## Contexto adicional

<!-- Cualquier información extra que ayude a diagnosticar -->
