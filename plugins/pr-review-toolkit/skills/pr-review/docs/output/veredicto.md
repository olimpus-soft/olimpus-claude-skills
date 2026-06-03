# ⚖️ Template de Veredicto Final

---

## Matriz de decisión

| Criterio | ✅ APROBADO | ✅ CON RECOMENDACIONES | ⚠️ CAMBIOS REQUERIDOS | ❌ RECHAZADO |
|----------|------------|----------------------|----------------------|-------------|
| Seguridad crítica | OK | OK | Problemas | Graves |
| Tests | Adecuados | Mejorables | Insuficientes | Ausentes |
| Code quality | Buena | Aceptable | Problemas | Inaceptable |
| Breaking changes | Ninguno | Documentados | Sin documentar | Inaceptables |
| Arquitectura | Correcta | OK | Cuestionable | Violación grave |

---

## ✅ APROBADO

```markdown
## ✅ APROBADO

El PR está listo para merge.

### Resumen
- Seguridad: ✅ Sin hallazgos críticos
- Tests: ✅ Cobertura adecuada
- Código: ✅ Sigue estándares del proyecto

### Riesgos
- 🟢 Bajo: {riesgo menor si existe}

**Justificación:** {párrafo explicando el veredicto}
```

---

## ✅ APROBADO CON RECOMENDACIONES

```markdown
## ✅ APROBADO CON RECOMENDACIONES

Puede mergearse. Las siguientes mejoras son opcionales pero recomendadas.

### Recomendaciones (no bloqueantes)
- [ ] {Mejora 1} — Prioridad: Media
- [ ] {Mejora 2} — Prioridad: Baja

### Follow-up tasks sugeridos
- Crear issue para {mejora futura}

### Riesgos
- 🟡 Medio: {riesgo aceptable}
- 🟢 Bajo: {riesgo menor}

**Justificación:** {párrafo}
```

---

## ⚠️ CAMBIOS REQUERIDOS

```markdown
## ⚠️ CAMBIOS REQUERIDOS

El PR necesita modificaciones antes de poder mergearse.

### Cambios obligatorios
1. **[Seguridad]** {descripción}
   - Archivo: `path/to/file.ext:línea`
   - Razón: {por qué es necesario}

2. **[Tests]** {descripción}
3. **[Código]** {descripción}

### Bloqueadores actuales
- [ ] {Bloqueador 1}
- [ ] {Bloqueador 2}

### Riesgos actuales
- 🔴 Alto: {riesgo que debe mitigarse}
- 🟡 Medio: {riesgo a considerar}

**Justificación:** {párrafo}
```

---

## ❌ RECHAZADO

```markdown
## ❌ RECHAZADO

El PR tiene problemas fundamentales que impiden su merge.

### Razones del rechazo
1. **{Razón principal}**
   - Descripción detallada
   - Impacto: {qué puede pasar si se mergea}

2. **{Razón secundaria}**

### Problemas críticos
- 🔴 {Problema crítico 1}
- 🔴 {Problema crítico 2}

### Alternativas sugeridas
- {Alternativa 1}: {descripción}

### Recomendación
{Qué debería hacer el autor — ej: cerrar este PR y abrir uno nuevo con approach diferente}
```
