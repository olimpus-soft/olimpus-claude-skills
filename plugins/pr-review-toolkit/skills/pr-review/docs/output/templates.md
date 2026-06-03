# 📄 Templates de Output

---

## Cuándo usar cada formato

- **PR pequeño** (<10 archivos, <200 líneas) → Sección A: Output directo (single)
- **PR grande** (>20 archivos o >500 líneas) → Sección B: Output por fases

---

## Sección A — Output directo (single)

Para PRs pequeños. Un solo archivo `PR-{REPO}-{N}-ANALISIS.md`.

```markdown
# 📊 Análisis del PR #{N}

**Fecha:** {YYYY-MM-DD}
**Repositorio:** {REPO}
**Autor:** {AUTHOR}
**Rama base:** {BASE_BRANCH}
**Tecnología:** {TECH}/{FRAMEWORK}

---

## 1. Resumen ejecutivo
{2-3 párrafos sobre qué hace el PR y por qué}

## 2. Estadísticas
| Métrica | Valor |
|---------|-------|
| Archivos modificados | X |
| Líneas agregadas | +X |
| Líneas eliminadas | -X |
| Commits | X |

## 3. Análisis de seguridad 🔒
{Hallazgos o "Sin hallazgos de seguridad"}

## 4. Análisis técnico ⚙️
{Arquitectura, calidad, tests}

## 5. Puntos fuertes ⭐
### ⭐⭐⭐⭐⭐ {Título}
**Archivos:** `path/to/file.ext`
{Descripción e impacto}

## 6. Puntos a mejorar ⚠️
### ⚠️ {Título} — Prioridad: {Alta|Media|Baja}   [MEJORA-N]
**Archivos:** `path/to/file.ext:línea`
{Problema y sugerencia}

## 7. Puntos críticos 🔥
### 🔥 {Título}   [CRITICO-N]
**Archivos:** `path/to/file.ext:línea`
{Riesgo, impacto, mitigación}

## 8. Checklist pre-merge
- [ ] {Acción requerida}

## 9. Veredicto
{Ver 09-veredicto.md}
```

---

## Sección B — Output por fases (phased)

Para PRs grandes. Genera 5 archivos intermedios + 1 consolidado final.

### Archivos generados
```
PR-{N}-fase-1-contexto.md
PR-{N}-fase-2-seguridad.md
PR-{N}-fase-3-tecnico.md
PR-{N}-fase-4-reviews.md
PR-{N}-fase-5-acciones.md
PR-{N}-ANALISIS-COMPLETO.md   ← unificado al final
```

### Fase 1 — Contexto y preparación
- Metadata del proyecto (tech, framework, arquitectura)
- Info del PR (título, autor, rama, fechas)
- Estadísticas generales (tabla)
- Timeline de commits
- Estado de CI/CD
- Módulos afectados

### Fase 2 — Análisis de seguridad
- Resumen de hallazgos por severidad
- Vulnerabilidades SSRF / input validation / secrets / deps
- Recomendaciones de seguridad

### Fase 3 — Análisis técnico
- Principios SOLID (tabla de estado por principio)
- Code smells detectados
- Complejidad por archivo
- Puntos fuertes ⭐
- Puntos a mejorar ⚠️
- Puntos críticos 🔥

### Fase 4 — Reviews y comentarios
- Estado de reviews (tabla)
- Comentarios críticos pendientes
- Temas recurrentes
- Feedback positivo

### Fase 5 — Acciones y veredicto
- Acciones antes del merge (checklist)
- Acciones post-merge
- Plan de deployment
- Rollback plan
- Veredicto final (ver `09-veredicto.md`)

### Indicadores de progreso a mostrar
```
🔄 Fase 1/5: Contexto y preparación...
✅ Fase 1/5 completada

🔄 Fase 2/5: Análisis de seguridad...
✅ Fase 2/5 completada

🔄 Fase 3/5: Análisis técnico...
✅ Fase 3/5 completada

🔄 Fase 4/5: Reviews y comentarios...
✅ Fase 4/5 completada

🔄 Fase 5/5: Acciones y veredicto...
✅ Fase 5/5 completada

🔄 Unificando resultados...
✅ Análisis completo: PR-{N}-ANALISIS-COMPLETO.md
```
