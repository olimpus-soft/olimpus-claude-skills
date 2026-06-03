---
name: pr-review
description: Análisis exhaustivo y AUTÓNOMO de Pull Requests de olimpus-soft. Publica automáticamente — sin pedir confirmación — una revisión formal en GitHub (request changes / approve / comment) con TODOS los issues encontrados como comentarios inline, luego aplica los fixes en el código y responde cada thread con la solución aplicada. Funciona sin necesidad de tener el repo clonado localmente.
allowlist:
  - gh
  - git
  - awk
  - base64
  - grep
  - Read(//tmp/*)
  - Write(//tmp/*)
  - Edit(//tmp/*)
  - Read(//tmp/agents/**)
  - Read(./.git/*)
  - Read(./*)
  - Write(./*)
  - Edit(./*)
  - Write(./.git/*)
  - Write(**/.claude/**)
  - Read(**/.claude/**)
  - Edit(**/.claude/**)
---

# 🔍 Análisis de Pull Request

> **SKILL**: Analiza un PR exhaustivamente y permite publicar una **revisión formal de GitHub** (con estado `REQUEST_CHANGES`, `APPROVE` o `COMMENT`) usando `gh`. Todos los repositorios pertenecen a la organización `olimpus-soft`. Funciona desde cualquier directorio sin necesidad de clonar el proyecto.

---

## ⚠️ REGLA DE AISLAMIENTO — leer antes de cualquier paso

**Esta skill opera en modo de análisis ciego.** Ignorá completamente cualquier información previa que tengas sobre:

- El repositorio, su arquitectura o su historia de cambios
- El autor del PR o cualquier colaborador mencionado
- Reviews anteriores al mismo PR o a PRs relacionados
- Decisiones de diseño, patrones o convenciones del proyecto que no sean visibles en el diff actual
- Cualquier memoria o contexto de sesiones previas

**Fuente de verdad única:** los datos obtenidos mediante los comandos `gh` ejecutados en esta sesión (diff, metadata, comentarios existentes). Si no está en el diff o en la respuesta de la API, no existe para este análisis.

**Por qué:** la memoria de sesiones anteriores puede introducir sesgos involuntarios — favorecer o penalizar código por razones que no son observables en el PR actual, recordar incorrectamente el estado anterior del código, o asumir contexto que ya no aplica.

**Consecuencia práctica:** cada ejecución de esta skill produce un análisis fresco, independiente de cualquier análisis previo del mismo PR o repositorio.

---

## Paso 0 — Identificar el contexto del PR

Antes de cualquier comando, necesitás resolver dos variables que se usarán en todos los pasos:

- **`REPO`**: el nombre del repositorio en olimpus-soft (ej: `fury_my-service`)
- **`NUMERO_PR`**: el número del pull request (ej: `42`)

> **Organización fija:** todos los repositorios pertenecen a `olimpus-soft`. Siempre usar `--repo olimpus-soft/{REPO}` en todos los comandos `gh`.

### Cómo obtenerlos

**Opción A — El usuario pasa una URL:**
Si el usuario pasa `https://github.com/olimpus-soft/REPO/pull/42`, extraé `REPO` y `42` de ahí.

**Opción B — El usuario pasa solo el nombre del repo y número:**
Formato esperado: `fury_my-service 145` o `fury_my-service#145`.
Usar directamente como `REPO` y `NUMERO_PR`.

**Opción C — Hay un repo git en el directorio actual:**
```bash
git remote get-url origin
```
Si el resultado contiene `olimpus-soft`, extraé `REPO` de la URL.

**Opción D — No hay suficiente información:**
Preguntarle al usuario: `¿Cuál es el nombre del repo y el número de PR? (ej: fury_my-service 145)`

### Dónde guardar el archivo de análisis

#### Detección de iteración

Antes de definir el nombre del archivo, verificar si ya existe un análisis previo del mismo PR:

```bash
ls {directorio_actual}/.claude/pr-reviews/{NUMERO_PR}/PR-{REPO}-{NUMERO_PR}-ANALISIS*.md 2>/dev/null
```

- Si **no existe ninguno**: el archivo base es `PR-{REPO}-{NUMERO_PR}-ANALISIS.md` (sin sufijo de iteración).
- Si **existe el archivo base** (sin iteración) pero no iteraciones: la nueva ejecución es la iteración 02, archivo → `PR-{REPO}-{NUMERO_PR}-ANALISIS-iter-02.md`.
- Si **ya existen iteraciones**: tomar el número más alto encontrado, incrementar en 1 (siempre dos dígitos con cero a la izquierda) y usar ese como nuevo sufijo. Ejemplo: si existe `iter-02` y `iter-03`, el nuevo archivo es `PR-{REPO}-{NUMERO_PR}-ANALISIS-iter-04.md`.

> **Nota:** la primera iteración no lleva sufijo. La numeración de iteraciones arranca en `02` para mantener coherencia con el archivo base.

#### Variable `ITER_SUFFIX`

Determinar `ITER_SUFFIX` según la lógica anterior:

| Situación | `ITER_SUFFIX` | Nombre de archivo resultante |
|-----------|--------------|------------------------------|
| Primera ejecución | *(vacío)* | `PR-{REPO}-{N}-ANALISIS.md` |
| Segunda ejecución | `-iter-02` | `PR-{REPO}-{N}-ANALISIS-iter-02.md` |
| Tercera ejecución | `-iter-03` | `PR-{REPO}-{N}-ANALISIS-iter-03.md` |

Usar `{NOMBRE_ARCHIVO}` = `PR-{REPO}-{NUMERO_PR}-ANALISIS{ITER_SUFFIX}.md` en todos los pasos siguientes.

#### Encabezado de iteración en el contenido del archivo

Si `ITER_SUFFIX` no está vacío, agregar al inicio del archivo (antes de la Sección 1) el siguiente bloque:

```markdown
---
## 🔄 Iteración {## número} — {fecha ISO}

**Análisis previo:** `PR-{REPO}-{N}-ANALISIS{ITER_SUFFIX_ANTERIOR}.md`
**Cambios desde iteración anterior:** *se debe volver a ejecutar `gh pr diff` para capturar el estado actual del diff; comparar con el diff anterior si está disponible.*

---
```

Guardar `PR-{REPO}-{NUMERO_PR}-ANALISIS{ITER_SUFFIX}.md` en el **directorio de trabajo actual** (donde el usuario está ejecutando la skill). **No preguntar** — usar siempre el cwd.

---

## Paso 1 — Recopilar información del PR vía `gh`

Todos los comandos usan `--repo OWNER/REPO` para no depender del contexto local:

```bash
# Metadata completa del PR
gh pr view {NUMERO_PR} --repo olimpus-soft/{REPO} \
  --json number,title,body,baseRefName,headRefName,author,\
additions,deletions,changedFiles,commits,createdAt,updatedAt,state,labels,reviewDecision

# Diff completo del PR (equivalente a git diff, sin clonar)
gh pr diff {NUMERO_PR} --repo olimpus-soft/{REPO} > pr-{NUMERO_PR}.diff

# Estadísticas de archivos cambiados
gh pr diff {NUMERO_PR} --repo olimpus-soft/{REPO} --name-only

# Comentarios y reviews existentes (para no repetir)
gh pr view {NUMERO_PR} --repo olimpus-soft/{REPO} --comments
gh api repos/olimpus-soft/{REPO}/pulls/{NUMERO_PR}/reviews
```

---

## Paso 1.5 — Auditoría de alertas de seguridad del repositorio

Ejecutar **todos** los comandos siguientes independientemente de si el PR toca código de seguridad. Las alertas activas del repo son contexto obligatorio para el veredicto final.

### CodeQL / Code Scanning alerts

```bash
# Alertas abiertas de code scanning (incluye CodeQL, IA findings, terceros)
gh api repos/olimpus-soft/{REPO}/code-scanning/alerts \
  --jq '.[] | select(.state=="open") | {number: .number, rule: .rule.id, severity: .rule.severity, description: .rule.description, file: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, tool: .tool.name}'
```

Si retorna `403` o `404`, registrar: `"Code scanning no habilitado o sin permisos"` y continuar.

### Dependabot alerts

```bash
# Alertas de dependencias vulnerables
gh api repos/olimpus-soft/{REPO}/dependabot/alerts \
  --jq '.[] | select(.state=="open") | {number: .number, package: .dependency.package.name, ecosystem: .dependency.package.ecosystem, severity: .security_advisory.severity, cvss: .security_advisory.cvss.score, cve: .security_advisory.cve_id, summary: .security_advisory.summary, manifest: .dependency.manifest_path}'
```

Si retorna `403` o `404`, registrar: `"Dependabot no habilitado o sin permisos"` y continuar.

### Secret scanning alerts

```bash
# Secretos detectados (tokens, claves, credenciales expuestas)
gh api repos/olimpus-soft/{REPO}/secret-scanning/alerts \
  --jq '.[] | select(.state=="open") | {number: .number, type: .secret_type_display_name, secret: (.secret // "***redacted***"), file: .locations_url, created: .created_at}'
```

Si retorna `403` o `404`, registrar: `"Secret scanning no habilitado o sin permisos"` y continuar.

### Correlación con el diff del PR

Una vez obtenidas las alertas, cruzar con los archivos modificados en el PR (`--name-only`):

- Si un archivo del diff **tiene alertas activas** → marcar como `⚠️ ALERTA ACTIVA` y elevar prioridad en el análisis
- Si el PR **agrega dependencias** con Dependabot alerts abiertas → marcarlo como crítico
- Si hay **secrets detectados** → siempre `🔥 CRÍTICO`, bloquea merge

### Formato de reporte de alertas (incluir en Sección 4 — Puntos críticos)

Para cada alerta activa correlacionada con el diff:

```
🔥 ALERTA-SEC-{N}: {tipo} — {descripción}
   Herramienta: {CodeQL | Dependabot | Secret Scanning | IA Finding}
   Severidad: {critical | high | medium | low}
   Archivo: {path}:{línea}
   CVE/Rule: {id}
   Estado: ABIERTA en /security del repo
   Acción requerida: {descripción de la mitigación}
```

Para alertas **no correlacionadas** con el diff (alertas generales del repo), incluirlas en la **Sección 5** como tabla de contexto:

| # | Herramienta | Severidad | Descripción | Archivo |
|---|---|---|---|---|
| {N} | {tool} | {sev} | {desc} | {path} |

> **Regla de veredicto:** si existen alertas `critical` o `high` abiertas en el repo (correlacionadas o no), el veredicto **nunca puede ser APROBADO** — mínimo `APROBADO CON RECOMENDACIONES` con nota explícita de las alertas pendientes.

---

## Paso 2 — Detectar tecnología y cargar skills de revisión

### 2.1 — Detectar stack a partir de los archivos cambiados

Analizar la lista de archivos del diff (`--name-only`) y determinar la tecnología principal:

| Señales en los archivos | Tecnología detectada | Skills a cargar |
|---|---|---|
| `*.py`, `pyproject.toml`, `requirements*.txt`, `*.pyi` | **Python** | `review-py` + `arch-py` |
| `*.ts`, `*.tsx`, `*.jsx`, `*.js`, `package.json`, `*.scss`, `*.css` | **Frontend** | `review-frontend` + `arch-frontend` |
| `*.go`, `go.mod`, `go.sum` | **Go** | `review-go` + `arch-go` |
| `*.java`, `*.kt`, `pom.xml`, `build.gradle*` | **Java** | `review-java` + `arch-java` |
| Mezcla de lenguajes | Cargar **todas** las skills relevantes |
| Sin match claro | Continuar sin skill de tecnología |

### 2.2 — Cargar skills de tecnología

Para cada skill detectada, leerla desde `~/.claude/skills/{nombre}/SKILL.md` y usarla como **base de conocimiento activa** durante el análisis del diff. Estas skills son conocimiento local puro — no hacen llamadas externas.

**Skills de tecnología a integrar en el análisis:**

- **`review-{tech}`** — aporta: checklist de verificación, plantillas de comentarios, criterios de severidad (Critical/High/Medium/Low), criterios de decisión final (aprobar/bloquear)
- **`arch-{tech}`** — aporta: patrones de arquitectura, antipatrones a detectar, buenas prácticas del stack, referencias técnicas para justificar observaciones

**Uso durante el análisis:**
- Aplicar el checklist de `review-{tech}` sobre cada archivo del diff
- Usar las categorías y severidades de `review-{tech}` para clasificar cada hallazgo
- Referenciar los patrones de `arch-{tech}` para justificar las observaciones (ej: "Ver arch-py: error-handling.md")
- Usar los criterios de decisión final de `review-{tech}` para determinar el veredicto de la Sección 7

### 2.3 — Generar el análisis exhaustivo

Analizar el diff con todos los módulos cargados. El análisis debe reflejar el checklist de la skill de tecnología detectada.

Al finalizar, escribir el resultado en `{NOMBRE_ARCHIVO}` en la ubicación confirmada en el Paso 0.

---

### Sección 1 — De qué trata el pull request

- Resumen ejecutivo (2-3 párrafos)
- Contexto y motivación de los cambios
- Objetivos principales
- Estadísticas generales (archivos modificados, líneas agregadas/eliminadas, commits)
- Timeline de commits con sus mensajes
- Módulos/componentes afectados

---

### Sección 2 — Puntos fuertes ⭐

Para cada punto fuerte identificado:
- Título descriptivo con calificación (⭐⭐⭐⭐⭐)
- Explicación detallada
- Archivos específicos involucrados
- Ejemplos de código (antes/después) cuando sea relevante
- Impacto positivo en el proyecto

Categorías a evaluar: arquitectura, calidad de código, manejo de errores, testing, performance, documentación, seguridad, mantenibilidad.

---

### Sección 3 — Puntos para mejorar ⚠️

Para cada mejora identificada:
- Título descriptivo con `⚠️`
- Descripción del problema
- **Archivo(s) afectado(s) con número de línea**
- Fragmento de código problemático
- Sugerencia concreta de refactorización
- Prioridad: `baja` / `media` / `alta`
- **ID único**: `MEJORA-{N}` (ej: `MEJORA-1`, `MEJORA-2`...)

Áreas: code smells, duplicación, complejidad, excepciones, validaciones, documentación, tests insuficientes, deuda técnica.

---

### Sección 4 — Puntos críticos 🔥

Para cada punto crítico:
- Título con `🔥`
- Descripción detallada del riesgo
- **Archivo(s) específico(s) y líneas**
- Breaking changes identificados
- Impacto en producción
- Riesgos de regresión
- Plan de mitigación sugerido
- **ID único**: `CRITICO-{N}` (ej: `CRITICO-1`, `CRITICO-2`...)

Aspectos: breaking changes, APIs públicas, esquema de BD, configuración, lógica de negocio core, seguridad, compliance.

---

### Sección 5 — Métricas y resumen

- Tabla de cambios por módulo/directorio
- Top 10 archivos más modificados
- Balance de líneas (agregadas vs eliminadas)
- Análisis de commits por categoría (feature/fix/refactor/docs/test)

---

### Sección 6 — Recomendaciones finales

- Checklist pre-merge
- Plan de deployment sugerido
- Pruebas adicionales recomendadas
- Follow-up tasks / issues a crear
- Rollback plan si es necesario

---

### Sección 7 — Veredicto final

Una de las siguientes opciones con justificación detallada:

- ✅ **APROBADO** — Listo para merge
- ✅ **APROBADO CON RECOMENDACIONES** — Merge con observaciones menores
- ⚠️ **CAMBIOS REQUERIDOS** — Necesita modificaciones antes de merge
- ❌ **RECHAZADO** — Problemas críticos que impiden el merge

---

## Paso 2.4 — Auditoría de calidad de tests con quality-test

Una vez identificados los archivos modificados en el diff, ejecutar la skill `quality-test` **acotada a los archivos cambiados por el PR**.

### Alcance

Solo analizar los archivos de test que correspondan directamente a los módulos modificados en el diff:

```bash
# Obtener archivos de test del diff
gh pr diff {NUMERO_PR} --repo olimpus-soft/{REPO} --name-only | grep -E "(test_|_test\.|\.test\.|\.spec\.)"
```

Si no hay archivos de test en el diff, verificar si los módulos modificados tienen tests asociados en el repositorio:

```bash
gh api "repos/olimpus-soft/{REPO}/git/trees/HEAD?recursive=1" \
  --jq '.tree[].path' | grep -E "(test_|_test\.|\.test\.|\.spec\.)"
```

### Qué evaluar (basado en quality-test)

Aplicar el análisis de quality-test sobre los archivos de test identificados, enfocado en:

1. **Caminos críticos no cubiertos** — funciones o ramas del diff que no tienen test correspondiente
2. **Test smells en los tests del PR** — según la lista prohibida en `testing_rules_improved.md`:
   - Assertion Roulette, Conditional Test Logic, Eager Test, Empty Test, Magic Number Test, Sleepy Test, Unknown Test, etc.
3. **Mutación readiness** — si los tests detectarían mutaciones simples (cambiar `>` por `>=`, invertir condicionales, eliminar llamadas)
4. **Cobertura de edge cases** — valores límite, errores esperados, paths de fallo
5. **Mocks vs integraciones** — si usan mocks cuando deberían ser integración o viceversa

### Formato de hallazgos de tests (incluir en Sección 3 o Sección 4)

Para cada hallazgo de calidad de tests:

```
⚗️ TEST-{N}: {descripción del problema}
   Archivo: {ruta/test_archivo.py}:{línea}
   Smell: {nombre del test smell si aplica}
   Impacto: {qué escenario de negocio queda sin cobertura}
   Sugerencia: {qué agregar o cambiar}
   Prioridad: {alta | media | baja}
```

**Regla de severidad:**
- Sin tests para código nuevo → siempre `alta` (Sección 4 — Críticos)
- Test smell bloqueante (Empty Test, Unknown Test) → `alta`
- Cobertura de edge cases faltante → `media`
- Mejoras de calidad de tests existentes → `baja`

### Condición de skip

Si el diff no contiene ni modifica archivos de test **y** el PR tiene menos de 10 líneas de código nuevo, omitir este paso y registrar: `"Sin archivos de test en el diff — análisis de quality-test omitido"`.

---

## Paso 2.5 — Registrar al revisor en el PR

### Obtener el usuario autenticado actual

```bash
gh api user --jq '.login'
# Guarda el resultado como REVIEWER_LOGIN
```

## Paso 3 — Publicación automática de TODOS los issues (sin confirmación)

> **AUTÓNOMO:** la skill **NO pide confirmación**. Publica todos los issues encontrados (`MEJORA-*` y `CRITICO-*`) en una única revisión formal e inmediatamente después aplica los fixes y responde cada thread con la solución.

Mostrar al usuario un resumen informativo (no es una pregunta — solo trazabilidad) antes de publicar:

```
📋 ISSUES ENCONTRADOS — publicando automáticamente
══════════════════════════════════════════════════

CRÍTICOS:  N  (todos serán comentados inline)
MEJORAS:   M  (todas serán comentadas inline)

Tipo de revisión derivado del veredicto:
  • CAMBIOS REQUERIDOS / RECHAZADO  → gh pr review --request-changes
  • APROBADO CON RECOMENDACIONES    → gh pr review --comment
  • APROBADO                        → gh pr review --approve
```

**Reglas obligatorias:**
- Incluir TODOS los issues en la revisión (críticos + mejoras), sin filtrar.
- No pausar, no esperar respuesta del usuario.
- Si no hay ningún issue (PR limpio) y el veredicto es APROBADO sin recomendaciones, publicar `--approve` con `body` indicando "Sin observaciones".
- Continuar inmediatamente con Paso 4 (publicación) y Paso 5 (fixes + respuestas).

---

## Paso 4 — Publicar la revisión con comentarios inline usando la GitHub API

Según la selección del usuario, publica **una única revisión formal con comentarios inline** usando `gh api`. Los comentarios inline aparecen pegados a líneas específicas del código en el diff, con botón **Reply** para que el autor responda en thread por cada issue.

### Por qué usar `gh api` en lugar de `gh pr review`

`gh pr review --body "..."` crea un único bloque de texto a nivel de PR. En cambio, la GitHub API permite adjuntar cada issue a la **línea exacta del código** que lo origina — igual al botón "Start a review" en la interfaz web.

### Paso 4.1 — Obtener el commit SHA del HEAD del PR

```bash
gh pr view {NUMERO_PR} --repo olimpus-soft/{REPO} --json headRefOid --jq '.headRefOid'
# Guarda el resultado como HEAD_SHA
```

### Paso 4.2 — Encontrar los números de línea reales en los archivos

Para cada issue que tenga archivo + línea identificados, obtener la línea exacta en el archivo actual (no en el diff):

```bash
# Obtener el contenido del archivo en el HEAD del PR y buscar el patrón
gh api "repos/olimpus-soft/{REPO}/contents/{ruta/archivo.py}?ref={HEAD_SHA}" \
  --jq '.content' | base64 -d | grep -n "{patrón_del_código_problemático}"
```

### Paso 4.3 — Construir el payload JSON de la revisión

Crear el archivo `/tmp/inline_review.json` con este formato:

```json
{
  "commit_id": "{HEAD_SHA}",
  "body": "{VEREDICTO} — Ver análisis completo en `{NOMBRE_ARCHIVO}`.\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_",
  "event": "{REVIEW_EVENT}",
  "comments": [
    {
      "path": "ruta/al/archivo.py",
      "line": 123,
      "side": "RIGHT",
      "body": "### {EMOJI} {TIPO}-{N}: {TÍTULO}\n\n**Prioridad:** {prioridad}\n\n{descripción del problema}\n\n**Sugerencia:**\n```python\n{código sugerido}\n```"
    }
  ]
}
```

**Valores para `event`** según el veredicto:

| Veredicto | `event` | Efecto |
|-----------|---------|--------|
| CAMBIOS REQUERIDOS / RECHAZADO | `"REQUEST_CHANGES"` | Bloquea merge |
| APROBADO CON RECOMENDACIONES   | `"COMMENT"`         | No bloquea |
| APROBADO                       | `"APPROVE"`         | Aprueba merge |

**Regla para `side`:** siempre `"RIGHT"` para comentar código nuevo (adiciones del PR).

**Issues sin archivo/línea concretos** — si algún issue no tiene una línea identificable en el diff, incluirlo en el `body` de la revisión a nivel general (no como inline comment).

### Paso 4.4 — Publicar la revisión

```bash
gh api repos/olimpus-soft/{REPO}/pulls/{NUMERO_PR}/reviews \
  --method POST \
  --input /tmp/inline_review.json \
  --jq '{id: .id, state: .state, url: .html_url}'
```

### Verificar que la revisión fue publicada

```bash
gh pr view {NUMERO_PR} --repo olimpus-soft/{REPO} --json reviews \
  --jq '.reviews[] | {author: .author.login, state: .state, submitted: .submittedAt}'
```

### Fallback: cuando una línea no está en el diff

Si la línea está en un archivo no modificado por el PR, GitHub rechazará el inline comment con error `422`. En ese caso, incluir ese issue en el `body` general de la revisión en lugar de como inline comment.

---

## Referencia rápida de comandos `gh`

Todos los comandos aceptan `--repo OWNER/REPO` para operar sin estar dentro del proyecto.

### Obtención de información

| Acción | Comando |
|--------|---------|
| Ver PR con metadata completa | `gh pr view {N} --repo {O}/{R} --json number,title,body,author,createdAt,updatedAt,baseRefName,headRefName,state,mergeable,additions,deletions,changedFiles` |
| Ver comentarios existentes | `gh pr view {N} --repo {O}/{R} --comments` |
| Ver reviews existentes (con estado) | `gh pr view {N} --repo {O}/{R} --json reviews --jq '.reviews[] \| {author: .author.login, state: .state, body: .body}'` |
| Ver comentarios inline en código | `gh api repos/{O}/{R}/pulls/{N}/comments --jq '.[] \| {path: .path, line: .line, body: .body, user: .user.login}'` |
| Ver estado de CI/CD | `gh pr checks {N} --repo {O}/{R}` |
| Obtener diff completo | `gh pr diff {N} --repo {O}/{R}` |
| Solo nombres de archivos cambiados | `gh pr diff {N} --repo {O}/{R} --name-only` |
| Lista de archivos con paths | `gh pr view {N} --repo {O}/{R} --json files --jq '.files[].path'` |
| Lista de commits formateada | `gh pr view {N} --repo {O}/{R} --json commits --jq '.commits[] \| {sha: .oid[0:7], message: .messageHeadline, author: .authors[0].login}'` |
| Labels del PR | `gh pr view {N} --repo {O}/{R} --json labels --jq '.labels[].name'` |
| Estado de merge | `gh pr view {N} --repo {O}/{R} --json mergeable --jq '.mergeable'` |
| Listar PRs abiertos | `gh pr list --repo {O}/{R}` |

### Alertas de seguridad

| Acción | Comando |
|--------|---------|
| Code scanning / CodeQL / IA findings | `gh api repos/{O}/{R}/code-scanning/alerts --jq '.[] \| select(.state=="open") \| {number,rule:.rule.id,severity:.rule.severity,tool:.tool.name,file:.most_recent_instance.location.path}'` |
| Dependabot alerts | `gh api repos/{O}/{R}/dependabot/alerts --jq '.[] \| select(.state=="open") \| {number,package:.dependency.package.name,severity:.security_advisory.severity,cve:.security_advisory.cve_id}'` |
| Secret scanning | `gh api repos/{O}/{R}/secret-scanning/alerts --jq '.[] \| select(.state=="open") \| {number,type:.secret_type_display_name,created:.created_at}'` |
| Resumen `/security` del repo | `gh api repos/{O}/{R} --jq '{security_policy: .security_policy_enabled, has_issues: .has_issues}'` |

### Publicar en el PR

| Acción | Comando | Bloquea merge |
|--------|---------|---------------|
| Solicitar cambios (revisión formal) | `gh pr review {N} --repo {O}/{R} --request-changes --body "texto"` | ✅ Sí |
| Aprobar PR | `gh pr review {N} --repo {O}/{R} --approve --body "texto"` | No aplica |
| Revisión informativa (sin bloqueo) | `gh pr review {N} --repo {O}/{R} --comment --body "texto"` | ❌ No |
| Comentario suelto (sin threading formal) | `gh pr comment {N} --repo {O}/{R} --body "texto"` | ❌ No |

---

## Paso 5 — Aplicar fixes y responder cada thread con la solución (AUTOMÁTICO)

Una vez publicada la revisión formal (Paso 4), invocar **automáticamente y sin confirmación** la skill `pr-comments-resolver` sobre el mismo PR. Esta skill resuelve TODOS los comentarios activos del PR — incluyendo los recién publicados por esta revisión, los de reviewers anteriores (Copilot, otros autores) y respuestas pendientes en threads abiertos.

```
/pr-comments-resolver {NUMERO_PR}
```

`pr-comments-resolver` se ejecuta de forma autónoma:
1. Lista todos los threads activos (no resueltos, no desactualizados).
2. Clasifica cada uno: `needs_fix` (cambio de código) vs `needs_reply` (solo respuesta).
3. **Aplica los fixes en el código** (Edit/Write en los archivos afectados, commit + push a la rama del PR).
4. **Responde cada thread con la solución aplicada** (referenciando commit SHA y diff cuando aplique) usando `gh api` para mantener el thread.
5. Genera reporte en `.claude/report/pr-comments-resolver/{NUMERO_PR}/report.md`.

**Reglas:**
- Esta invocación NO requiere confirmación — es parte del flujo autónomo de `pr-review`.
- Si `pr-comments-resolver` detecta un fix que requiere decisión humana (cambio de arquitectura, dependencia nueva, eliminación de feature), publica `needs_reply` con justificación y deja el comentario abierto sin aplicar fix.
- Si no hay comentarios activos tras publicar la revisión (caso muy raro: solo si no se publicó ningún issue), reportar al usuario y terminar.

---

## Paso 6 — Desbloquear el PR para merge (AUTOMÁTICO)

Tras aplicar todos los fixes y responder los threads (Paso 5), si la revisión publicada fue `REQUEST_CHANGES` el PR queda bloqueado. **Desbloquear automáticamente** ejecutando esta secuencia:

### 6.1 Verificar que todo está realmente resuelto

```bash
# Threads activos no resueltos
UNRESOLVED=$(gh api graphql -f query='
{
  repository(owner: "olimpus-soft", name: "{REPO}") {
    pullRequest(number: {NUMERO_PR}) {
      reviewThreads(first: 100) {
        nodes { id isResolved isOutdated }
      }
    }
  }
}' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false and .isOutdated == false)] | length')

# CI checks
CHECKS=$(gh pr checks {NUMERO_PR} --repo olimpus-soft/{REPO} --json bucket --jq '[.[] | select(.bucket == "fail" or .bucket == "pending")] | length')
```

**Condiciones para desbloquear:** `UNRESOLVED == 0` **y** `CHECKS == 0` (sin fallos ni pendientes).

Si alguna condición falla, NO desbloquear. Reportar al usuario el motivo (threads abiertos, CI fallando) y terminar dejando el PR como está.

### 6.2 Resolver threads pendientes que ya fueron atendidos

Cualquier thread cuyo último comentario sea respuesta del bot resolutor debe marcarse como resuelto vía GraphQL:

```bash
gh api graphql -f query='
mutation($id: ID!) {
  resolveReviewThread(input: { threadId: $id }) {
    thread { isResolved }
  }
}' -f id="{THREAD_ID}"
```

### 6.3 Dismiss de la review bloqueante

Identificar la(s) review(s) propias en estado `CHANGES_REQUESTED` y descartarlas:

```bash
# Listar reviews propias bloqueantes
gh api repos/olimpus-soft/{REPO}/pulls/{NUMERO_PR}/reviews \
  --jq '.[] | select(.state == "CHANGES_REQUESTED" and .user.login == "{BOT_O_USER_ACTUAL}") | .id'

# Dismiss de cada una
gh api -X PUT repos/olimpus-soft/{REPO}/pulls/{NUMERO_PR}/reviews/{REVIEW_ID}/dismissals \
  -f message="Fixes aplicados y verificados — ver respuestas en cada thread. Desbloqueo automático por pr-review."
```

### 6.4 Publicar review de aprobación final

```bash
gh pr review {NUMERO_PR} --repo olimpus-soft/{REPO} --approve \
  --body "✅ Todos los issues señalados fueron corregidos. Threads resueltos, CI en verde. PR listo para merge.

🤖 Aprobación automática por pr-review tras aplicación de fixes."
```

### 6.5 Reportar al usuario

Mensaje final al usuario con:
- Total issues encontrados / corregidos / con respuesta humana pendiente.
- SHA del último commit con fixes.
- Estado del PR: `MERGEABLE` confirmado vía `gh pr view {N} --json mergeable,mergeStateStatus`.
- Link al PR.

**Nota:** NO ejecutar el merge. El usuario o el flujo de release decide cuándo mergear.

---

## Notas de comportamiento

1. **Siempre usar `--repo olimpus-soft/{REPO}`** en todos los comandos `gh` — la organización es siempre `olimpus-soft`.
2. **Siempre revisar reviews existentes** antes de publicar para evitar duplicar una review del mismo autor (`gh pr view {N} --repo {O}/{R} --json reviews`).
3. **Agrupar TODOS los issues encontrados en UNA SOLA revisión** — no filtrar, no pedir selección al usuario. Consolidar críticos + mejoras en el cuerpo de un único `gh pr review`.
4. **Publicar automáticamente sin confirmación.** El Paso 3 es informativo, no interactivo.
5. **Tras publicar, invocar `pr-comments-resolver` automáticamente** (Paso 5) para aplicar fixes y responder cada thread con la solución; luego ejecutar el Paso 6 para desbloquear el PR (resolver threads, dismiss de la review bloqueante y aprobación automática) cuando se cumplan las condiciones de seguridad (threads resueltos + CI en verde).
6. **El tipo de revisión (`--request-changes` / `--comment` / `--approve`) debe derivarse del veredicto** del análisis, no elegirse al azar.
7. **Manejo de fallos de `gh`:**
   - Si `gh` no está instalado → detener y mostrar: `"gh CLI requerido. Instalá desde https://cli.github.com"`
   - Si `gh` no está autenticado → detener y sugerir: `gh auth login`
   - Si `gh pr view` falla por permisos (`403`) → detener y explicar: `"Sin acceso al repo olimpus-soft/{REPO}. Verificá que tu token tiene scope repo."`
   - Si `gh pr diff` falla por PR demasiado grande → avisar al usuario y continuar el análisis solo con metadata (sin diff completo)
   - Si cualquier comando `gh` falla por otro motivo → mostrar el error exacto y detener
8. Si no se puede resolver el `REPO` automáticamente (Paso 0), detener con error explícito (`"No se pudo inferir el repositorio. Reinvocar como /pr-review {repo}#{N} o {URL_PR}."`). **No preguntar interactivamente** — la skill es autónoma.
9. **Sin sesgo de memoria** — el análisis se basa exclusivamente en el diff y los datos de la API obtenidos en esta sesión. No usar información de sesiones previas, reviews anteriores al mismo PR, ni conocimiento previo sobre el repositorio o sus autores. Ver la Regla de Aislamiento al inicio del documento.
