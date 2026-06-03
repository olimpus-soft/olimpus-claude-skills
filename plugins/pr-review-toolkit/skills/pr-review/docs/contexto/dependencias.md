# 📦 Análisis de Dependencias

Cargar cuando el PR modifica `package.json`, `pom.xml`, `requirements.txt`, `go.mod` u otros archivos de dependencias.

---

## 1. Clasificar el tipo de cambio

```diff
# Patch (1.2.3 → 1.2.4): bug fix, bajo riesgo
- "lodash": "4.17.20"
+ "lodash": "4.17.21"

# Minor (1.2.x → 1.3.0): features nuevas, backward compatible
- "express": "4.17.1"
+ "express": "4.18.0"

# Major (1.x.x → 2.0.0): puede tener BREAKING CHANGES
- "frontend-i18n": "5.8.1"
+ "frontend-i18n": "6.0.2"   # ← requiere verificar changelog
```

### Checklist por tipo
- [ ] **Patch**: bajo riesgo — verificar que el PR documenta el motivo si no es obvio
- [ ] **Minor**: revisar changelog brevemente — puede haber deprecations
- [ ] **Major**: **revisar changelog completo** — buscar migration guide, breaking changes

---

## 2. Major version upgrades — señales de riesgo

Buscar en el diff consecuencias del upgrade:

```diff
# ❌ Señal de riesgo: import path cambió
- import I18n from 'frontend-i18n/lib/I18n';
+ import I18n from 'frontend-i18n';

# ❌ Señal de riesgo: API cambió
- i18n.translate('key')
+ i18n.gettext('key')
```

Preguntas clave para major upgrades:
- [ ] ¿El PR actualiza todos los lugares afectados por el cambio de API?
- [ ] ¿Hay tests que validan el comportamiento post-upgrade?
- [ ] ¿El upgrade fue testeado en un ambiente no productivo?
- [ ] ¿Hay rollback plan si el upgrade genera problemas en prod?

---

## 3. Dependencias nuevas

```json
// Nueva dependencia productiva — mayor impacto
"dependencies": {
    "some-new-lib": "^1.0.0"
}

// Nueva dependencia de desarrollo — menor impacto
"devDependencies": {
    "@types/new-lib": "^1.0.0"
}
```

Para cada dependencia nueva evaluar:
- [ ] ¿El paquete es ampliamente usado y mantenido (no abandonado)?
- [ ] ¿Tiene vulnerabilidades conocidas? (`npm audit` / `pip-audit`)
- [ ] ¿La licencia es compatible con el proyecto?
- [ ] ¿Podría implementarse con código propio en < 50 líneas? (evitar micro-deps)
- [ ] ¿Tiene peer dependencies que pueden generar conflictos?
- [ ] ¿Cuánto pesa en el bundle final (para deps de frontend)?

---

## 4. Dependencias removidas

```diff
- "@andes/context": "8.41.6",
- "frontend-lazy": "3.9.0",
```

- [ ] ¿Se removieron los usos de la dependencia en el código?
- [ ] ¿No queda código que la importe (aunque no lo use)?
- [ ] ¿Era una dependencia transitiva que otros módulos esperan?

---

## 5. Vulnerabilidades

```bash
# Node.js
npm audit

# Python
pip-audit

# Java
mvn dependency-check:check

# Go
govulncheck ./...
```

Clasificar por severidad:
- 🔴 **Critical / High**: bloqueante para el merge
- 🟡 **Medium**: documentar y crear ticket de seguimiento
- 🟢 **Low**: informar, no bloquea

---

## 6. Lock files

```diff
# ✅ package-lock.json / yarn.lock siempre debe commitearse junto con package.json
# ❌ Diferencia entre package.json y package-lock.json es señal de problema
```

- [ ] ¿Se commitea el lock file junto con el cambio en el manifest?
- [ ] ¿El lock file fue regenerado (no editado manualmente)?

---

## 7. Formato de reporte de dependencias

```markdown
### 📦 Cambios de dependencias

| Paquete | Cambio | Tipo | Riesgo |
|---------|--------|------|--------|
| `frontend-i18n` | 5.8.1 → 6.0.2 | Major | ⚠️ Revisar changelog |
| `@meli-dev/i18n-tools` | 1.0.0 → 2.1.0 | Major | ⚠️ Revisar changelog |
| `adm-zip` | 0.5.10 → 0.5.16 | Patch | ✅ Bajo riesgo |

**Vulnerabilidades detectadas:** ninguna / {lista si hay}
**Dependencias nuevas:** {lista} | **Dependencias removidas:** {lista}
```
