---
name: pr-generate
description: "Genera y crea Pull Requests automáticamente sin pedir confirmación. Analiza el diff, construye título y body, crea el PR en Draft, asigna copilot como reviewer y dispara el review de Claude. Flujo 100% autónomo — nunca pausa ni pregunta al usuario."
allowlist:
  - git
  - gh
  - curl
  - make
  - mkdir
  - date
  - cat
  - ls
  - python3
  - sleep
  - Bash(git *)
  - Bash(gh *)
  - Bash(curl *)
  - Bash(make *)
  - Bash(mkdir *)
  - Bash(date *)
  - Bash(cat *)
  - Bash(ls *)
  - Bash(python3 *)
  - Bash(sleep *)
  - Read(**/.git/*)
  - Read(**/.claude/**)
  - Write(**/.claude/**)
  - Edit(**/.claude/**)
  - Read(//tmp/agents/**)
  - Write(//tmp/agents/**)
  - Read(*)
  - mcp__my-mysql-server__execute_select
  - mcp__my-mysql-server__list_databases
  - mcp__my-mysql-server__list_tables
alwaysApply: true
autoAccept: true
---

# Generate PR

## Principio fundamental

**Flujo 100% autónomo.** El agente analiza el diff, elige título y body con criterio técnico, y crea el PR sin pausar. No pide confirmación de rama target (usa `develop` por defecto), no muestra preview, no espera aprobación. Ejecuta todos los pasos en secuencia.

**Regla de fuente de datos:** todo el análisis (título, body, componentes, casos) se basa estrictamente en el `git diff` entre la rama actual y la rama target. Sin inferencias de contexto del chat.

**Rama target por defecto:** `develop`, salvo que el usuario la especifique explícitamente al invocar la skill.

---

## Paso 1: Recopilar información del repositorio

```bash
CURRENT_BRANCH=$(git branch --show-current)

# Detección automática de rama target según prefijo del branch
case "${CURRENT_BRANCH}" in
  release/*|hotfix/*)
    # Verificar si existe 'main' o 'master'
    if git ls-remote --exit-code --heads origin main > /dev/null 2>&1; then
      TARGET_BRANCH="main"
    else
      TARGET_BRANCH="master"
    fi
    ;;
  *)
    # feature/, fix/, bugfix/, chore/, docs/, refactor/, test/, develop, y cualquier otro
    TARGET_BRANCH="develop"
    ;;
esac

# El usuario puede override la rama target pasándola como argumento al invocar la skill
# Si el usuario especificó una rama explícitamente, usar esa en lugar de la detectada.

git diff --stat ${TARGET_BRANCH}...${CURRENT_BRANCH}
git diff --shortstat ${TARGET_BRANCH}...${CURRENT_BRANCH}
git diff ${TARGET_BRANCH}...${CURRENT_BRANCH}
```

**Regla de rama target:**

| Prefijo del branch | Target automático |
|---|---|
| `feature/*` | `develop` |
| `fix/*` | `develop` |
| `bugfix/*` | `develop` |
| `chore/*` | `develop` |
| `docs/*` | `develop` |
| `refactor/*` | `develop` |
| `test/*` | `develop` |
| `release/*` | `main` o `master` (el que exista en remoto) |
| `hotfix/*` | `main` o `master` (el que exista en remoto) |
| Cualquier otro | `develop` |

Extraer del branch:
- **Tipo CC** según prefijo: `feature/` → `feat`, `fix/` → `fix`, `hotfix/` → `hotfix`, `bugfix/` → `fix`, `chore/` → `chore`, `docs/` → `docs`, `refactor/` → `refactor`, `test/` → `test`, `release/` → `release`, sin prefijo → `feat`
- **Ticket ID** — patrón `OLIMPUSSW-\d+` en el nombre del branch

---

## Paso 2: Validaciones (bloqueantes)

```bash
# Archivos cambiados (máx 20)
FILE_COUNT=$(git diff --name-only ${TARGET_BRANCH}...${CURRENT_BRANCH} | wc -l)
[ "$FILE_COUNT" -gt 20 ] && echo "❌ PR excede 20 archivos ($FILE_COUNT). Dividir en múltiples PRs." && exit 1

# CHANGELOG.md actualizado
CHANGELOG_CHANGED=$(git diff --name-only ${TARGET_BRANCH}...${CURRENT_BRANCH} | grep -c "^CHANGELOG.md$" || true)
[ "$CHANGELOG_CHANGED" -eq 0 ] && echo "❌ CHANGELOG.md no actualizado. Agrega entrada bajo [Unreleased]." && exit 1

# Branch en remoto
git ls-remote --exit-code --heads origin ${CURRENT_BRANCH} > /dev/null 2>&1 || git push -u origin ${CURRENT_BRANCH}
```

Tests: ejecutar `make test` si existe Makefile con target `test`. Si no existe, continuar.

---

## Paso 3: Construir título

**Formato obligatorio:**
```
{type}({scope}): {descripción mínimo 10 chars}
```

- Máximo **120 caracteres** totales
- Una sola línea
- Verbos en infinitivo: Agregar, Corregir, Refactorizar, Actualizar, Eliminar, Implementar, Ajustar, Migrar
- Sin artículos innecesarios
- Una sola acción principal — la de mayor impacto en lógica de negocio

**Auto-crítica interna antes de escribir:**
- ¿Describe el impacto real, no el medio? (malo: "modificar archivo X" / bueno: "corregir cálculo impuestos en checkout")
- ¿El tipo CC es honesto y preciso?
- ¿Tiene suficiente especificidad para entenderse sin contexto adicional?

**Ejemplos:**
```
feat(OLIMPUSSW-42): implementar validación email en formulario registro usuarios
fix(OLIMPUSSW-77): corregir rotación de refresh token con sesión expirada
hotfix(OLIMPUSSW-99): resolver falla crítica autenticación usuarios premium
chore(OLIMPUSSW-12): actualizar dependencias testing y configuración CI/CD
```

---

## Paso 4: Construir body

Usar esta plantilla. Omitir secciones sin contenido real — no llenar con texto genérico.

```markdown
## Summary

{Descripción concisa de qué se implementa/corrige y el enfoque técnico elegido}

🔗 **Jira:** [{TICKET_ID}](https://olimpus-soft.atlassian.net/browse/{TICKET_ID})

## Componentes implementados

- **{Componente1}**: {descripción breve de responsabilidad}
- **{Componente2}**: {descripción breve de responsabilidad}

## Casos soportados

✅ {Caso/escenario 1}
✅ {Caso/escenario 2}

## Test plan

- ☑️ **{Módulo}**: {qué se testea}
- ☑️ Cobertura global: ≥ 98%
- ☑️ `make test-coverage` pasa sin regresiones

## Files changed

- **Nuevos**: `{archivo1}`, `{archivo2}`
- **Modificados**: `{archivo}` ({detalle})
- **Tests**: {N} archivos
- **Total**: {N} archivos (+{añadidas}/-{eliminadas})

---
_Generated by [Claude Code](https://claude.ai/code)_

Co-authored-by: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Prohibido:** textos como "Made with", "Powered by", "Generated by Cursor" o similares.
**Permitido:** `_Generated by [Claude Code](https://claude.ai/code)_` y `Co-authored-by:`.

---

## Paso 5: Crear el PR en Draft

```bash
PR_URL=$(gh pr create \
  --title "${PR_TITLE}" \
  --body "${PR_BODY}" \
  --base ${TARGET_BRANCH} \
  --draft)

echo "PR creado: ${PR_URL}"
PR_NUMBER=$(echo "${PR_URL}" | grep -oE '[0-9]+$')
```

---

## Paso 6: Asignar reviewers y disparar reviews (Claude + Codex)

```bash
for i in 1 2 3 4 5; do
  gh pr edit ${PR_NUMBER} --add-reviewer copilot 2>/dev/null && break
  echo "Intento $i fallido, reintentando en 30s..."
  sleep 30
done

gh pr comment ${PR_NUMBER} --body "@claude review this PR"

# Codex como reviewer — SIEMPRE. El PR se crea en Draft y Codex no revisa drafts
# automáticamente, por eso se dispara explícito con la mención.
gh pr comment ${PR_NUMBER} --body "@codex review"
```

---

## Paso 6.5: Comentario con enlace a Jira (si aplica)

Si se detectó `TICKET_ID` en el branch:

```bash
gh pr comment ${PR_NUMBER} --body "🔗 **Jira:** https://olimpus-soft.atlassian.net/browse/${TICKET_ID}"
```

---

## Paso 7: Confirmar resultado al usuario

```
✅ PR #N creado en Draft: {PR_URL}
✅ Título: {PR_TITLE}
✅ copilot asignado como reviewer
✅ @claude review disparado
✅ @codex review disparado
✅ Jira link publicado (si aplica)
```

---

## Estándares de calidad

| Criterio | Regla |
|---|---|
| Cobertura | ≥ 98% (advertencia si no) |
| Archivos | ≤ 20 por PR (bloqueante) |
| CHANGELOG.md | Actualizado (bloqueante) |
| Título | Conventional Commits, máx 120 chars |
| Estado | Siempre Draft |
| Firmas | Solo `Generated by Claude Code` + `Co-authored-by:` |
