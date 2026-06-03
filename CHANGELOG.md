# Changelog

Todos los cambios notables en este proyecto se documentan aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
Versionado siguiendo [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [1.1.0] - 2026-06-03

### Changed

- **[OLIMPUSSW-404] skill `pr-generate` — quitar triggers `@claude review` y `@codex review`:** se elimina del Paso 6 la publicación de comentarios que disparan los reviews de Claude y Codex. Razón: ahora los workflows del repo (`claude.yml` y `codex-review-gate.yml`) disparan ambos reviews **automáticamente post-CI verde**, lo que evita revisiones sobre código que aún no compila/pasa tests y elimina redundancia. La skill ahora solo asigna `copilot` como reviewer humano-equivalente. Actualizado descripción del frontmatter, Paso 6 (renombrado a "Asignar reviewer (copilot)"), Paso 7 (resumen final), y tabla de estándares de calidad.

- **[OLIMPUSSW-405] skill `pr-generate` — alinear formato título a `amannn/action-semantic-pull-request@v6`:** se actualiza el Paso 1 (mapeo prefijo→tipo) y Paso 3 (construcción de título) al patrón exacto del validator CI configurado en `pr-checks.yml` de los repos OlimpusSoft. Reglas explícitas: solo los 9 tipos válidos (`feat | fix | chore | docs | refactor | test | ci | build | perf`), scope opcional `OLIMPUSSW-N`, separador `: ` (dos puntos + espacio), description en minúscula sin punto final, máximo 120 chars. Se documentan ejemplos válidos e inválidos con la regla rota en cada caso. Mapeos críticos: `hotfix/` → `fix` (NO `hotfix`), `release/` → `chore` (NO `release`), `bugfix/` → `fix`. Razón: PRs con título mal formateado (ej. `[OLIMPUSSW-XXX] Implementar X`) venían fallando el check de semantic PR de forma silenciosa cross-repo.

## [1.0.0] - 2026-06-02

### Added
- Plugin `pr-review-toolkit` con 13 skills: `pr-review`, `quality-test`, `pr-comments-resolver`, `pr-generate`, `commitmsg`, `review-py`, `review-frontend`, `review-go`, `review-java`, `arch-py`, `arch-frontend`, `arch-go`, `arch-java`
- Estructura de plugin marketplace estándar de Claude Code
- README con catálogo de skills y ejemplo de integración en `claude.yml`
