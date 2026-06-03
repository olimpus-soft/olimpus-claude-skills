# Guía de contribución

Gracias por contribuir a este proyecto. Por favor lee esta guía antes de abrir un PR.

## Requisitos previos

- Leer el [Código de Conducta](CODE_OF_CONDUCT.md)
- Tener una tarea Jira asociada al trabajo (`OLIMPUSSW-{número}`)
- Tener configurados los pre-commit hooks localmente

## Flujo de trabajo

### 1. Crear rama

```bash
git checkout develop
git pull origin develop
git checkout -b feature/OLIMPUSSW-{número}-{descripcion-kebab}
```

### 2. Desarrollar

- Aplicar TDD: test primero, implementación después
- Actualizar `CHANGELOG.md` con cada cambio significativo
- Commitear usando la convención de commits

### 3. Sincronizar con develop antes del PR

```bash
git fetch origin
git checkout develop && git pull origin develop
git checkout feature/OLIMPUSSW-{número}-{descripcion-kebab}
git merge develop
```

### 4. Abrir Pull Request

- Título: `feat(OLIMPUSSW-{número}): descripción corta`
- Completar el template de PR
- Esperar que todos los checks de CI estén verdes
- Cobertura mínima: **98.5%**

## Convención de commits

```
{type}({scope}): {descripción en imperativo, máx 72 chars}

[cuerpo opcional]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Tipos válidos:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`

## Estándares de calidad

- Tests nombrados por escenario de negocio
- Sin `skip` sin justificación documentada
- Sin `print` ni logs de debug en código de producción
- Sin secretos o credenciales hardcodeadas
- Type hints en todas las funciones públicas (si aplica al stack)

## Preguntas

Abrir un issue con la etiqueta `question` o escribir a miguelmoralescoterio@gmail.com.
