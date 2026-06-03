---
name: pr-comments-resolver
description: Lista comentarios activos (no resueltos, no desactualizados) de un PR de GitHub, clasifica si requieren fix de código o solo respuesta, genera un reporte estructurado con soluciones sugeridas, y opcionalmente aplica los fixes o publica las respuestas con gh CLI. Para PRs de OlimpusSoft en github.com/olimpus-soft.
argument-hint: <pr-number>
allowed-tools: Bash(gh:*), Bash(git:*), Bash(mkdir:*), Read, Write, Edit, Grep, Glob
model: opus
---

## Prerequisitos

Ejecutar todos los checks en orden. Detener ante el primer fallo.

| # | Check | Comando | Condición de stop |
|---|-------|---------|-------------------|
| 1 | Git repo | `git rev-parse --show-toplevel` | exit no-cero |
| 2 | Número de PR | validar `$1` | vacío o inválido |
| 3 | `gh` instalado | `gh --version` | no encontrado |
| 4 | `gh` versión ≥ 2 | parsear major | major < 2 |
| 5 | `gh` autenticado | `gh auth status` | exit no-cero |
| 6 | PR accesible | `gh pr view "${PR_NUMBER}" --json number` | exit no-cero |

### Git repo

```bash
git rev-parse --show-toplevel
```

Si falla, detener: "Este skill debe ejecutarse dentro de un repositorio git."

Capturar como `REPO_ROOT`.

### Número de PR

Si `$1` está vacío, detener: "Falta el número de PR. Uso: `/pr-comments-resolver <número>`"

Validar que sea entero positivo:
```bash
printf '%s' "$1" | grep -qE '^[1-9][0-9]{0,8}$'
```

Si falla, detener: "Número de PR inválido: `$1`. Debe ser un entero positivo."

Desde aquí, `PR_NUMBER = $1`.

### gh CLI

```bash
gh --version
gh --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'
```

Si no está o major < 2, detener con instrucciones: `brew install gh`.

### Autenticación

```bash
gh auth status
```

Si falla, detener: "GitHub CLI no está autenticado. Ejecuta `gh auth login`."

### Acceso al PR

```bash
gh pr view "${PR_NUMBER}" --json number 2>&1
```

Si falla, interpretar error y detener con mensaje apropiado.

---

## Variables de estado

| Variable | Descripción |
|----------|-------------|
| `REPO_ROOT` | Path absoluto del repo |
| `PR_NUMBER` | Número de PR validado |
| `REPO_OWNER` | Owner del repositorio (siempre `olimpus-soft`) |
| `REPO_NAME` | Nombre del repositorio |
| `PR_TITLE` | Título del PR |
| `ACTIVE_THREADS` | Threads activos (no resueltos, no desactualizados) |
| `ANALYSIS` | Clasificación por thread |
| `REPORT_PATH` | Path al reporte generado |

### Patrón de confirmación

Aceptar como "sí": `yes`, `y`, `ok`, `sí`, `si`, `dale`, `listo`, `claro`, `va`.
Cualquier otra respuesta → detener: "Acción cancelada por el usuario."

---

## Paso 1 — Contexto del repo y PR

```bash
gh repo view --json owner,name
gh pr view "${PR_NUMBER}" --json title
```

Extraer `owner.login` → `REPO_OWNER`, `name` → `REPO_NAME`, `title` → `PR_TITLE`.

---

## Paso 2 — Obtener threads activos

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isOutdated
          isResolved
          comments(first: 20) {
            nodes {
              databaseId
              body
              path
              line
              originalLine
              diffHunk
              author { login }
              url
              createdAt
            }
          }
        }
      }
    }
  }
}' -F owner="${REPO_OWNER}" -F repo="${REPO_NAME}" -F pr="${PR_NUMBER}"
```

Filtrar: conservar solo threads donde `isOutdated == false` AND `isResolved == false`.

Si `ACTIVE_THREADS` está vacío:
> "No hay comentarios activos en el PR #PR_NUMBER. Todos están resueltos o desactualizados. Nada por hacer."

---

## Paso 3 — Analizar cada thread

Para cada thread, leer el archivo afectado (±20 líneas alrededor de `line`) con la herramienta Read si `path` y `line` están disponibles.

### Categoría A — `needs_fix`
Cambio de código necesario:
- Bug, error de lógica, comportamiento incorrecto
- Validación o manejo de error faltante
- Vulnerabilidad de seguridad
- Violación de convención obligatoria (reglas OlimpusSoft)
- Test faltante o refactor requerido

### Categoría B — `needs_reply`
Sin cambio de código:
- Pregunta ya resuelta por el código
- Sugerencia subjetiva fuera del scope
- Mejora que pertenece a otra tarea
- Nitpick sin impacto funcional

Por cada thread producir:
```
thread_id, url, author, file:line, comment_body,
category: needs_fix | needs_reply,
reasoning,
suggested_action (descripción + archivo + línea + sugerencia de código) o draft_reply
```

---

## Paso 4 — Generar reporte

### 4.0 — Re-validar PR_NUMBER

Verificar que `PR_NUMBER` siga cumpliendo `^[1-9][0-9]{0,8}$`.

### 4.1 — Crear directorio

```bash
mkdir -p "${REPO_ROOT}/.claude/report/pr-comments-resolver/${PR_NUMBER}"
```

### 4.2 — Asegurar `.claude/report/` en `.gitignore`

Si no existe la entrada `\.claude/report/` en `.gitignore`, agregarla con Edit (o crear el archivo con Write).

### 4.3 — Escribir reporte

`REPORT_PATH = ${REPO_ROOT}/.claude/report/pr-comments-resolver/${PR_NUMBER}/report.md`

```markdown
# PR Comments Analysis — #<PR_NUMBER>

**PR**: <PR_TITLE>
**Fecha**: <YYYY-MM-DD>
**Threads activos analizados**: <count>

---

## Resumen

| Categoría | Cantidad |
|-----------|----------|
| Requiere fix de código | <count_fix> |
| Requiere solo respuesta | <count_reply> |

---

## Comentarios que requieren fix de código

### Thread N — `<file>:<line>`

**Comentario de @<author>** ([ver](<url>))

> <comment_body>

**Razonamiento**: <reasoning>

**Fix sugerido**:
- **Archivo**: `<path>`
- **Qué cambiar**: <description>
- **Sugerencia**:
  ```
  <code suggestion>
  ```

---

## Comentarios que solo requieren respuesta

### Thread N — `<file>:<line>`

**Comentario de @<author>** ([ver](<url>))

> <comment_body>

**Razonamiento**: <reasoning>

**Borrador de respuesta**:
> <draft_reply>
```

Informar al usuario: "Reporte guardado en `.claude/report/pr-comments-resolver/${PR_NUMBER}/report.md`"

Presentar el reporte completo.

---

## Paso 5 — Ofrecer aplicar fixes de código

Si no hay threads `needs_fix`, saltar.

Preguntar:
> "Encontré **<count>** comentario(s) que requieren cambios en el código. ¿Quieres que aplique los fixes ahora?"
> "(Mostraré cada cambio antes de aplicarlo y pediré confirmación.)"

Si confirma:
1. Mostrar thread URL, archivo y descripción del cambio
2. Leer el archivo con Read
3. Aplicar con Edit
4. Confirmar aplicación o reportar error y preguntar si continuar

Al finalizar:
> "Fixes aplicados. Revisa los cambios con `git diff` antes de commitear."

---

## Paso 6 — Ofrecer publicar respuestas

Si no hay threads `needs_reply`, saltar.

Preguntar:
> "Encontré **<count>** comentario(s) que solo requieren respuesta. ¿Quieres que publique los borradores en GitHub ahora?"

Si confirma, para cada thread:
1. Mostrar URL y borrador
2. Preguntar: "¿Publicar esta respuesta? (sí/no/editar)"
   - `sí` / aliases → publicar tal cual
   - `editar` → pedir texto al usuario
   - Cualquier otro → saltar al siguiente
3. Publicar:
   ```bash
   gh api repos/${REPO_OWNER}/${REPO_NAME}/pulls/${PR_NUMBER}/comments \
     --method POST \
     --field body="<reply_text>" \
     --field in_reply_to=<databaseId>
   ```
4. Confirmar publicación o reportar error y continuar

Al finalizar:
> "Listo. Respuestas publicadas. Ver PR en: <PR URL>"

---

## Paso 7 — Resumen final

> **PR #PR_NUMBER — Comentarios gestionados**
>
> | Acción | Cantidad |
> |--------|----------|
> | Fixes de código aplicados | <n> |
> | Respuestas publicadas | <n> |
> | Saltados por el usuario | <n> |
>
> Reporte en: `.claude/report/pr-comments-resolver/${PR_NUMBER}/report.md`
