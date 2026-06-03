# 💬 Análisis de Reviews y Comentarios Existentes

Cargar cuando el PR ya tiene reviews o comentarios de otros revisores.

---

## 1. Obtención de datos

```bash
# Comentarios generales del PR
gh pr view ${PR_NUMBER} --repo ${OWNER}/${REPO} --json comments \
  --jq '.comments[] | {author: .author.login, body: .body, createdAt: .createdAt}'

# Estado de reviews
gh pr view ${PR_NUMBER} --repo ${OWNER}/${REPO} --json reviews \
  --jq '.reviews[] | {author: .author.login, state: .state, body: .body}'

# Comentarios inline en código (con archivo y línea)
gh api repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments \
  --jq '.[] | {path: .path, line: .line, body: .body, user: .user.login, createdAt: .created_at}'
```

---

## 2. Estados de review

| Estado | Significado |
|--------|-------------|
| `APPROVED` | ✅ Aprobado sin cambios |
| `COMMENTED` | 💬 Solo comentarios, sin veredicto |
| `CHANGES_REQUESTED` | ❌ Requiere cambios antes de merge |
| `PENDING` | ⏳ Review en progreso |
| `DISMISSED` | 🚫 Review descartado por el autor |

---

## 3. Qué analizar

### Comentarios críticos pendientes
Identificar comentarios que:
- Señalan bugs o comportamiento incorrecto
- Cuestionan decisiones de diseño o arquitectura
- Piden cambios de seguridad
- Solicitan tests adicionales
- Están marcados como `CHANGES_REQUESTED`

### Temas recurrentes
- ¿Múltiples revisores señalan lo mismo? → Mayor prioridad
- ¿Hay patrón de mejoras sugeridas en el mismo módulo?

### Hilos sin resolver
- Comentarios sin respuesta del autor
- Discusiones sin conclusión clara
- Sugerencias no implementadas

---

## 4. Formato de reporte

```markdown
## 💬 Reviews Existentes

### Estado
| Reviewer | Estado | Fecha |
|----------|--------|-------|
| @user1 | ✅ Aprobado | 2024-01-15 |
| @user2 | ❌ Cambios requeridos | 2024-01-14 |

### Comentarios críticos pendientes
| Archivo | Reviewer | Comentario resumido | Prioridad |
|---------|----------|---------------------|-----------|
| `api/service.js:45` | @user2 | Falta manejo de error en timeout | Alta |

### Temas recurrentes
- "Falta validación de entrada" — mencionado por 2 revisores
- "Tests insuficientes para casos de error"

### Feedback positivo
- @user1: "Buena implementación del patrón fire-and-forget"
```

---

## 5. Checklist

- [ ] ¿Hay comentarios de `CHANGES_REQUESTED` sin resolver?
- [ ] ¿Los hilos de discusión están todos respondidos?
- [ ] ¿Se implementaron los cambios sugeridos en reviews anteriores?
- [ ] ¿Hay comentarios duplicados (mismos revisores señalando lo mismo)?
- [ ] ¿El autor respondió a todos los comentarios críticos?
