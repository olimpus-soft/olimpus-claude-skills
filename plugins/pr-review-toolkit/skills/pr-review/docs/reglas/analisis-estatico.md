# 🔬 Análisis Estático — Herramientas y Patrones

---

## 1. Herramientas por tecnología

### Node.js / TypeScript
```bash
npm run lint                          # ESLint
tsc --noEmit                          # Type checking
npm audit                             # Vulnerabilidades en deps
prettier --check .                    # Formateo
```

### Python
```bash
ruff check .                          # Linting rápido
mypy .                                # Type checking
bandit -r .                           # Seguridad
black --check .                       # Formateo
radon cc . -a -s                      # Complejidad ciclomática
```

### Java
```bash
mvn checkstyle:check
mvn spotbugs:check
mvn dependency-check:check            # CVEs
```

### Go
```bash
golangci-lint run
gosec ./...
govulncheck ./...
gofmt -l .
```

---

## 2. Código muerto

```javascript
// ❌ Señales de código muerto
function unusedFunction() { }         // Nunca se llama
import os from 'node:os';             // Nunca se usa
if (false) { doSomething(); }         // Inalcanzable
```

- [ ] ¿Hay funciones definidas pero nunca invocadas?
- [ ] ¿Hay imports no utilizados?
- [ ] ¿Hay bloques `if/else` con condición siempre falsa?
- [ ] ¿Hay constantes definidas pero nunca referenciadas?

---

## 3. Código duplicado

Bloques similares en múltiples lugares → candidatos a extracción.

**Herramientas:**
- JS/TS: `jscpd`
- Multiplataforma: PMD CPD

---

## 4. Complejidad ciclomática

| Valor | Estado | Acción |
|-------|--------|--------|
| 1–10 | ✅ | — |
| 11–20 | ⚠️ | Considerar refactor |
| 21+ | ❌ | Refactorizar |

```bash
# Node.js via ESLint
eslint . --rule 'complexity: ["error", 10]'

# Python
radon cc . --min C
```

---

## 5. Métricas de cobertura de tests

```bash
npm test -- --coverage                # Jest
pytest --cov=src --cov-report=term    # Python
```

**Umbrales sugeridos:**
- Código nuevo: > 80%
- Código crítico (pagos, seguridad): > 90%
- Total proyecto: > 70%

---

## 6. Checklist pre-aprobación

- [ ] ¿Linting pasa sin errores nuevos?
- [ ] ¿Type checking pasa (si aplica)?
- [ ] ¿Sin vulnerabilidades nuevas en dependencias?
- [ ] ¿Complejidad ciclomática aceptable?
- [ ] ¿Sin código duplicado significativo?
- [ ] ¿Sin código muerto (dead code)?
- [ ] ¿Cobertura de tests no bajó respecto a la rama base?
- [ ] ¿CI/CD pasa? (`gh pr checks {N} --repo {O}/{R}`)
