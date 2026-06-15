# Changelog

Todos los cambios notables en este proyecto se documentan aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
Versionado siguiendo [Semantic Versioning](https://semver.org/lang/es/).

## [1.2.0](https://github.com/olimpus-soft/olimpus-claude-skills/compare/v1.1.2...v1.2.0) (2026-06-10)


### Features

* **OLIMPUSSW-438:** propagar 8 workflows canónicos del template a olimpus-claude-skills ([0e8136f](https://github.com/olimpus-soft/olimpus-claude-skills/commit/0e8136fd1b6d62b6e6c7b6f6bc7172a7b2699931))

## [Unreleased]

### Security
- **[OLIMPUSSW-495] Workflows: token permissions least-privilege + pin third-party actions a SHA-40.** Mitiga `TokenPermissionsID` y `PinnedDependenciesID` (code-scanning errors detectados en audit cross-repo `agents/shared/decisions/2026-06-15_security-alerts-cross-repo-piccolo.md`). Cambios:
  - Agregado bloque `permissions: { contents: read }` top-level en `cd.yml`, `ci.yml`, `mutation-tests.yml`, `security.yml`, `stale.yml`, `claude.yml`, `codex-review-gate.yml`.
  - Bajado `permissions:` top-level a `contents: read` y movido `write` necesario a per-job en `backport.yml`, `release.yml`, `docker-publish.yml` (least-privilege default).
  - Pinneadas 11 third-party actions a SHA commit completo (40 chars) con comentario semver: `codecov/codecov-action`, `appleboy/ssh-action`, `anthropics/claude-code-action`, `docker/login-action`, `docker/metadata-action`, `docker/setup-buildx-action`, `docker/build-push-action`, `peter-evans/create-pull-request`, `googleapis/release-please-action`, `ossf/scorecard-action`, `aquasecurity/trivy-action`.
  - Actions oficiales GitHub (`actions/*`, `github/codeql-action/*`) **NO se pinean** por decisión milk — namespace de confianza.
  - Fuera de scope (ticket separado): `claude.yml` `actions/untrusted-checkout/high` + `DangerousWorkflowID` (patrón `workflow_run` con checkout de PR head_sha — requiere refactor estructural). Dockerfile container image pinning. Meta-checks scorecard sin archivo asociado.

### Fixed
- **[OLIMPUSSW-427] `pr-checks.yml` — excepcionar ramas de bots en el validador de convenciones:** los 3 steps de validación (nombre de rama, título Conventional Commits, CHANGELOG.md) ahora hacen early-exit con `exit 0` cuando `$HEAD_REF` matchea `^(dependabot/|release-please--)`. Antes del fix, todo PR de Dependabot fallaba en el primer step porque la rama `dependabot/github_actions/...` no cumple el patrón `^(feature|fix|chore|...)/OLIMPUSSW-[0-9]+`. Caso real: Dependabot PR#8 (bump `github-actions` group con 11 updates) bloqueado en CI. El fix permite que los PRs automáticos avancen sin diluir la validación para ramas humanas.

### Changed
- **[OLIMPUSSW-445] `backport.yml` — App token `olimpus-hermes-bot` para commits Verified:** sustituye `secrets.BACKPORT_TOKEN` (PAT) por installation token vía `actions/create-github-app-token@v3` con `BOT_APP_ID` + `BOT_APP_PRIVATE_KEY` en ambos jobs (`develop_to_main` y `main_to_develop`). Los commits del backport ahora salen como `olimpus-hermes-bot[bot]` con badge **Verified** — cumple `required_signatures` del ruleset `main`. Copia literal del template `olimpus-soft/olimpuss-template@HEAD` (batch-4 cross-repo).

### Added
- **[OLIMPUSSW-438] Propagar 8 workflows canónicos del template:** añade `backport.yml`, `claude.yml`, `codex-review-gate.yml`, `docker-publish.yml`, `gitflow.yml`, `pr-checks.yml`, `runner-control.yml` y `scorecard.yml` copiados literalmente desde `olimpuss-template@HEAD` (PR#33). Habilita CI gates (Codex review, PR conventions, GitFlow Guard), runner-control ephemeral y OpenSSF Scorecard en el repo marketplace. No incluye `codeql.yml` ni `dependency-review.yml` (decisión NO-GHAS 2026-06-02).
- **[OLIMPUSSW-442] `pr-review` SKILL — Paso 2.6: cargar identidad bot `olimpus-hermes-bot[bot]` antes de publicar:** nueva sección obligatoria que ejecuta `unset GH_TOKEN GITHUB_TOKEN && BOT_TOKEN=$(bash ~/olimpussoft/manager/agents/bin/bot-token.sh --raw)` y pasa `BOT_TOKEN` INLINE a cada `gh pr review|comment|api` de los Pasos 3, 4, 5 y 6. Necesario porque el keyring de `gh` (CLI local con `gh auth login`) pisa `export GH_TOKEN` del shell — sólo `GH_TOKEN=... gh ...` inline garantiza override. Si `bot-token.sh` falla, fallback a identidad humana con WARNING visible (nunca aborta). Resuelve que la review pueda salir firmada como humano en CLI local pero como bot en CI/agentes remotos — ahora es uniforme en todos los entornos.

## [1.1.2] - 2026-06-04

### Fixed

- **[OLIMPUSSW-404 hotfix v1.1.2] `plugin.json` — quitar campo `skills` con formato inválido (array de strings):** el formato `"skills": ["pr-review", "quality-test", ...]` (array de strings) **NO es válido** per [docs oficiales Claude Code Plugins reference](https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema). El schema espera que `skills` sea un **string path** (ej: `"./custom/skills/"`) cuando se quiere customizar la ubicación, o **omitido** para que Claude Code auto-descubra desde el path default `skills/` del plugin. El loader del `claude-code-action@v1` rechaza el manifest con `"invalid manifest plugin.json: skills: Invalid input"` (detectado por levi en validación Plan B C2 round-3). **Fix:** se elimina el campo del manifest — las 13 skills (`pr-review`, `quality-test`, `pr-comments-resolver`, `pr-generate`, `commitmsg`, `review-py`, `review-frontend`, `review-go`, `review-java`, `arch-py`, `arch-frontend`, `arch-go`, `arch-java`) viven en `plugins/pr-review-toolkit/skills/<name>/SKILL.md` y son auto-descubiertas correctamente. Bump patch `1.1.1` → `1.1.2` en `marketplace.json` + `plugin.json` + `.release-please-manifest.json` (los tres alineados ahora). Bloqueante crítico Plan B → rollout 3.0.

## [1.1.1] - 2026-06-04

### Fixed

- **[OLIMPUSSW-404 hotfix v1.1.1] `marketplace.json` — corregir schema del campo `plugins` a array de objetos:** el formato `"plugins": ["plugins/pr-review-toolkit"]` (array de strings con paths) es inválido per [docs oficiales Claude Code Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces#create-the-marketplace-file). El loader rechaza el marketplace con error `"pr-review-toolkit not found in marketplace"` (detectado en run `26931012520` durante validación Plan B). Schema correcto: `"plugins": [{ name, source, description, version }]`. Bloqueante crítico Plan B → rollout 3.0 → 12 repos OlimpusSoft. Bump patch `1.1.0` → `1.1.1` (manifest del marketplace; plugin `pr-review-toolkit` mantiene `1.1.0` — su contenido no cambió).

## [1.1.0] - 2026-06-03

### Fixed

- **[OLIMPUSSW-404 sync] `.release-please-manifest.json` — sincronizar con versión publicada manualmente (1.1.0):** el manifest estaba en `0.1.0` mientras `marketplace.json` y `plugin.json` ya estaban en `1.0.0` (drift previo a este PR). Al subir manualmente a `1.1.0`, se sincroniza el manifest para evitar que release-please genere PRs con bump partiendo de `0.1.0` y desalineados con el versionado real del marketplace. Detectado por codex[bot] en review del PR#2.

- **[OLIMPUSSW-404 hotfix] `marketplace.json` — agregar campo `owner` requerido por Claude Code Action:** el action `claude-code-action@v1` (input `plugin_marketplaces`) rechaza el marketplace con error `Failed to parse marketplace.json: owner: Invalid input: expected object, received undefined`. Schema oficial de [Claude Code plugins](https://docs.claude.com/en/docs/claude-code/plugins#marketplace-json) requiere `owner` como objeto con `name`, `email` y `url`. Sin este campo, el plugin `pr-review-toolkit` NO se instala en CI cross-repo (12 repos OlimpusSoft impactados). Detectado empíricamente por levi en validación Plan B del PR `olimpus-streamvault#179`. Bloqueante criterio-1 del rollout 3.0.

### Changed

- **[OLIMPUSSW-404] skill `pr-generate` — quitar triggers `@claude review` y `@codex review`:** se elimina del Paso 6 la publicación de comentarios que disparan los reviews de Claude y Codex. Razón: ahora los workflows del repo (`claude.yml` y `codex-review-gate.yml`) disparan ambos reviews **automáticamente post-CI verde**, lo que evita revisiones sobre código que aún no compila/pasa tests y elimina redundancia. La skill ahora solo asigna `copilot` como reviewer humano-equivalente. Actualizado descripción del frontmatter, Paso 6 (renombrado a "Asignar reviewer (copilot)"), Paso 7 (resumen final), y tabla de estándares de calidad.

- **[OLIMPUSSW-405] skill `pr-generate` — alinear formato título a `amannn/action-semantic-pull-request@v6`:** se actualiza el Paso 1 (mapeo prefijo→tipo) y Paso 3 (construcción de título) al patrón exacto del validator CI configurado en `pr-checks.yml` de los repos OlimpusSoft. Reglas explícitas: solo los 9 tipos válidos (`feat | fix | chore | docs | refactor | test | ci | build | perf`), scope opcional `OLIMPUSSW-N`, separador `: ` (dos puntos + espacio), description en minúscula sin punto final, máximo 120 chars. Se documentan ejemplos válidos e inválidos con la regla rota en cada caso. Mapeos críticos: `hotfix/` → `fix` (NO `hotfix`), `release/` → `chore` (NO `release`), `bugfix/` → `fix`. Razón: PRs con título mal formateado (ej. `[OLIMPUSSW-XXX] Implementar X`) venían fallando el check de semantic PR de forma silenciosa cross-repo.

## [1.0.0] - 2026-06-02

### Added
- Plugin `pr-review-toolkit` con 13 skills: `pr-review`, `quality-test`, `pr-comments-resolver`, `pr-generate`, `commitmsg`, `review-py`, `review-frontend`, `review-go`, `review-java`, `arch-py`, `arch-frontend`, `arch-go`, `arch-java`
- Estructura de plugin marketplace estándar de Claude Code
- README con catálogo de skills y ejemplo de integración en `claude.yml`
