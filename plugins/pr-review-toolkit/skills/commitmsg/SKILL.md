---
name: commitmsg
description: "Genera mensajes de commit convencionales y concisos basándose en los archivos en staging area. Úsalo siempre que el usuario pida generar, sugerir o escribir un mensaje de commit, o cuando mencione 'commit', 'staged changes', 'git commit', o pida revisar qué hay en staging. También aplica cuando el usuario diga 'qué pongo en el commit' o similar. Ejecuta el flujo completo automáticamente: revisa staging, detecta branch, construye el mensaje, lo escribe en COMMIT_EDITMSG, hace git commit y git push. Sin pausas, sin preguntas, sin confirmaciones."
allowlist:
  - git
  - Bash(git *)
  - Read(**/.git/*)
  - Write(**/.git/*)
  - Edit(**/.git/*)
  - Read(//tmp/agents/**)
  - Write(//tmp/agents/**)
  - Read(**/.claude/**)
  - Write(**/.claude/**)
  - Edit(**/.claude/**)
alwaysApply: true
autoAccept: true
---

# Generador de Mensajes de Commit

## Principio fundamental

**Flujo completamente autónomo.** El modelo analiza el diff con criterio técnico y de negocio, elige el mejor mensaje posible, hace commit y push. No pausa. No pregunta. No pide confirmación en ningún punto.

---

## Flujo de ejecución

### 1. Verificar staging

```bash
git diff --cached --name-status
```

Si el resultado está vacío → responde: `No hay cambios en staging. Agregá archivos con git add primero.` y detente.

### 2. Revisar el diff completo con criterio técnico

```bash
git diff --cached
```

Analizar con visión crítica:
- ¿Qué cambió realmente en la lógica de negocio? (no nombres de archivos — el impacto real)
- ¿Es un fix, una feature, un refactor, config? Ser preciso — no usar `fix` si es un `feat`
- ¿Hay múltiples tipos de cambio? Priorizar el de mayor impacto (ver tabla abajo)
- ¿El cambio es en tests solamente? Solo entonces usar `test`
- ¿Actualización de deps? Usar `chore` con los nombres de las deps relevantes

### 3. Detectar branch y ticket ID

```bash
git branch --show-current
```

**Tipo de branch:**

| Prefijo | Tipo |
|---|---|
| `feature/` | `[FEATURE]` |
| `release/` | `[RELEASE]` |
| `hotfix/` | `[HOTFIX]` |
| `fix/` | `[FIX]` |
| `bugfix/` | `[BUGFIX]` |
| `develop` | `[DEVELOP]` |
| `main` | `[MAIN]` |
| Otro | `[FIX]` |

**Ticket ID:** buscar `OLIMPUSSW-\d+` en el nombre del branch. Si hay match → incluirlo.

**Prefijo final:**
- Con ticket: `[TIPO][OLIMPUSSW-N]`
- Sin ticket: `[TIPO]` o `[SIN-ID]`

### 4. Construir el mensaje — criterio técnico estricto

**Reglas:**
- Máximo **150 caracteres** totales
- **Una sola línea**, sin saltos
- Verbo en infinitivo: `Agregar`, `Corregir`, `Refactorizar`, `Actualizar`, `Eliminar`, `Implementar`, `Ajustar`, `Migrar`, `Extraer`
- Sin artículos innecesarios (`el`, `la`, `un`, `una`)
- Una sola acción principal — la de mayor impacto
- Nombrar el componente, módulo o capa afectada con precisión técnica

**Prioridad de cambios:**

1. Lógica de negocio / nuevas funcionalidades
2. Corrección de bugs
3. Refactoring con impacto en arquitectura
4. Configuración / dependencias
5. Tests (solo si son los únicos cambios)
6. Documentación

**Auto-crítica antes de escribir:** preguntarse internamente —
- ¿Este mensaje describe el IMPACTO, no el medio? (malo: "Modificar archivo X" / bueno: "Corregir cálculo de impuestos en checkout")
- ¿Es lo suficientemente específico para entenderse en 6 meses sin contexto?
- ¿El tipo de commit es correcto y honesto?

**Ejemplos:**

```
[FEATURE][OLIMPUSSW-42] Implementar validación email en formulario registro usuarios
[BUGFIX][OLIMPUSSW-77] Corregir error timeout en consultas base datos productos
[HOTFIX][OLIMPUSSW-99] Resolver falla crítica autenticación usuarios premium
[DEVELOP] Actualizar dependencias testing y configuración CI/CD pipeline
[SIN-ID] Extraer lógica paginación a hook reutilizable usePagedQuery
```

### 5. Hacer commit

El commit debe incluir el co-autor del modelo activo en la sesión:

| Modelo | Co-autor |
|---|---|
| claude-sonnet-4-6 | `Co-authored-by: Claude Sonnet 4.6 <noreply@anthropic.com>` |
| claude-opus-4-7 | `Co-authored-by: Claude Opus 4.7 <noreply@anthropic.com>` |
| claude-haiku-4-5 | `Co-authored-by: Claude Haiku 4.5 <noreply@anthropic.com>` |

El modelo activo es **claude-sonnet-4-6** por defecto, salvo que el contexto de sesión indique otro.

```bash
git commit -m "[TIPO][TICKET] Descripción del cambio

Co-authored-by: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### 6. Push

```bash
git push
```

Si el push falla por rama sin upstream:

```bash
git push --set-upstream origin $(git branch --show-current)
```

### 7. Mostrar resultado

Mostrar al usuario:
- El mensaje de commit usado
- El conteo de caracteres
- El resultado del push (rama y remoto)
