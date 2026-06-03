# ⚙️ Análisis Técnico — Core

Aplica a **todas las tecnologías**. Siempre cargar este módulo.

---

## 1. Principios SOLID

| Principio | Checklist |
|-----------|-----------|
| **SRP** — Single Responsibility | ¿Cada clase/módulo tiene una sola responsabilidad? ¿Funciones < 20 líneas? |
| **OCP** — Open/Closed | ¿Se puede extender sin modificar código existente? ¿Se usan abstracciones? |
| **LSP** — Liskov Substitution | ¿Las subclases pueden sustituir a sus padres sin romper comportamiento? |
| **ISP** — Interface Segregation | ¿Las interfaces son pequeñas y específicas? |
| **DIP** — Dependency Inversion | ¿Se depende de abstracciones, no implementaciones? ¿Hay inyección de deps? |

---

## 2. Code Smells a detectar

| Smell | Señales |
|-------|---------|
| **Código duplicado** | Bloques similares en múltiples lugares |
| **Función larga** | > 30 líneas, múltiples niveles de indentación |
| **Lista de parámetros larga** | > 4 parámetros en una función |
| **Feature Envy** | Función que usa más datos de otra clase que de la propia |
| **Dead Code** | Código inalcanzable, imports sin usar, funciones nunca llamadas |
| **Speculative Generality** | Abstracciones sin uso real (YAGNI) |
| **Switch Statements** | Múltiples switches sobre el mismo tipo → polimorfismo |
| **Primitive Obsession** | Uso excesivo de primitivos en lugar de objetos de valor |

---

## 3. Complejidad ciclomática

| Valor | Estado | Acción |
|-------|--------|--------|
| 1–10 | ✅ Aceptable | — |
| 11–20 | ⚠️ Revisar | Considerar refactorizar |
| 21–50 | ❌ Alta | Refactorizar obligatorio |
| 50+ | ❌ Crítica | Urgente |

**Señales de alta complejidad:** muchos `if/else` anidados, múltiples `switch/case`, loops anidados, condiciones booleanas largas.

---

## 4. Arquitectura

- [ ] ¿Las dependencias van en una sola dirección (sin circulares)?
- [ ] ¿La capa de presentación no accede directamente a BD?
- [ ] ¿La lógica de negocio está separada de infraestructura?
- [ ] ¿Alta cohesión dentro de módulos?
- [ ] ¿Bajo acoplamiento entre módulos?

---

## 5. Testing

- [ ] ¿Hay tests para la funcionalidad nueva?
- [ ] ¿Se cubren casos edge y escenarios de error?
- [ ] ¿Los tests siguen el patrón AAA (Arrange-Act-Assert)?
- [ ] ¿Los tests son independientes entre sí?
- [ ] ¿Los nombres de tests describen el escenario?
- [ ] ¿Se evitan tests frágiles (dependientes de orden, tiempo, etc.)?

---

## 6. Manejo de errores

- [ ] ¿Se manejan todos los errores posibles?
- [ ] ¿Los errores tienen mensajes útiles para debugging?
- [ ] ¿No se silencian errores (`catch {}` vacío)?
- [ ] ¿Se usa logging apropiado (no solo `console.log`)?
- [ ] ¿Se propagan errores correctamente por capas?

---

## Formatos de reporte

```markdown
### ⭐⭐⭐⭐⭐ {Título del punto fuerte}
**Archivos:** `path/to/file.ext`
**Descripción:** {por qué es un punto fuerte}
**Impacto:** {beneficio para el proyecto}

### ⚠️ {Título} — Prioridad: {Alta|Media|Baja}
**Archivos:** `path/to/file.ext:línea`
**Problema:** {descripción del issue}
**Sugerencia:** {cómo mejorarlo}

### 🔥 {Título}
**Archivos:** `path/to/file.ext:línea`
**Riesgo:** {descripción}
**Impacto:** {qué puede pasar en producción}
**Mitigación:** {qué hacer}
```
