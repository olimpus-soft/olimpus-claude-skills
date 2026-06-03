# 🎯 Orquestador del Análisis

Punto de entrada para análisis de PRs. Define qué módulos de este directorio cargar según el contexto detectado.

---

## Paso 1: Detección del contexto

```bash
# Ubicación y repo
pwd
git rev-parse --show-toplevel 2>/dev/null
git config --get remote.origin.url

# Detectar tecnología (buscar archivos de configuración)
ls -la package.json pom.xml build.gradle requirements.txt pyproject.toml go.mod Cargo.toml composer.json 2>/dev/null
```

## Paso 2: Decisiones de carga

### 2.1 Método de obtención del PR
- **Si `gh` está disponible** → Usar los comandos de SKILL.md (recomendado)
- **Si repo público sin gh** → Usar `git clone --depth=1` + `git diff`

### 2.2 Tecnología detectada — cargar UNO de estos:
- `package.json` → `tecnologias/node.md`
- `pom.xml` o `build.gradle` → `tecnologias/java.md`
- `requirements.txt` o `pyproject.toml` → `tecnologias/python.md`
- `go.mod` → `tecnologias/go.md`
- Archivos `.jsx`/`.tsx`/`next.config` → `tecnologias/frontend.md`

### 2.3 Análisis siempre requeridos
- `analisis/seguridad-core.md` — Seguridad base (SSRF, secrets, deps, input validation)
- `analisis/tecnico-core.md` — Calidad de código (SOLID, smells, complejidad)
- `reglas/logs-comentarios.md` — Reglas de logs y comentarios
- `contexto/proyecto.md` — Convenciones del proyecto (README, AGENTS.md)

### 2.4 Análisis condicionales
- **Si es una API** → `analisis/seguridad-apis.md`
- **Si hay reviews/comentarios existentes** → `analisis/reviews.md`
- **Si usa servicios Fury (MeLi)** → `contexto/fury.md`
- **Si hay cambios en package.json / pom.xml / go.mod / requirements.txt** → `contexto/dependencias.md`
- **Si hay cambios de performance sospechosos (N+1, loops, queries)** → `analisis/performance.md`
- **Si hay cambios en APIs públicas, esquema DB, env vars o configuración** → `analisis/breaking-changes.md`

### 2.5 Team code style (opcional)

Una vez detectada la tecnología, **antes de comenzar el análisis**, preguntar al usuario:

```
📐 Se detectó un repositorio {TECNOLOGIA}.
   ¿Querés aplicar el team code style del equipo?
   Incluye convenciones de arquitectura, nomenclatura y patrones específicos. (s/n)
```

Mapeo de archivos según tecnología detectada:

| Tecnología | Archivo a cargar |
|---|---|
| Java (`pom.xml` / `build.gradle`) | `team-code-style/java/basic_style_java.md` |
| Node (`package.json`) | `team-code-style/node/basic_style_node.md` *(si existe)* |
| Python (`requirements.txt` / `pyproject.toml`) | `team-code-style/python/basic_style_python.md` *(si existe)* |
| Go (`go.mod`) | `team-code-style/go/basic_style_go.md` *(si existe)* |
| Frontend (`.jsx`/`.tsx`) | `team-code-style/frontend/basic_style_frontend.md` *(si existe)* |

- Si el usuario responde **s** → cargar el archivo correspondiente y usarlo como criterio adicional en el análisis
- Si el usuario responde **n** → continuar sin team code style
- Si el archivo no existe para esa tecnología → informar: `"No hay team code style definido para {TECNOLOGIA} todavía."` y continuar

### 2.6 Template de salida
- **PR pequeño (<10 archivos, <200 líneas)** → Usar formato single (`output/templates.md` — sección single)
- **PR grande (>20 archivos o >500 líneas)** → Usar formato por fases (`output/templates.md` — sección phased)

## Paso 3: Variables a definir antes de continuar

```
PR_NUMBER={número del PR}
REPO={nombre del repo}        # la organización siempre es melisource
RAMA_BASE={develop|main|master}
ANALYSIS_DATE=$(date +%Y-%m-%d)
OUTPUT_FILE=PR-{REPO}-{PR_NUMBER}-ANALISIS.md
```

## Paso 4: Ejecución

1. Cargar los módulos según las decisiones anteriores
2. Obtener diff + info del PR (comandos en SKILL.md)
3. Ejecutar cada fase de análisis
4. **Deduplicar issues**: si un issue ya fue reportado por un módulo anterior, no volver a incluirlo. El primer módulo que lo detecta es el "dueño" del issue. Casos comunes de solapamiento:
   - `breaking-changes.md` y `dependencias.md` pueden detectar el mismo major upgrade con breaking changes → reportar solo en `breaking-changes.md`
   - `seguridad-core.md` y `seguridad-apis.md` pueden coincidir en validación de input → reportar solo en `seguridad-apis.md` si es un endpoint HTTP
5. Generar output con el template correspondiente
6. Aplicar veredicto final (`output/veredicto.md`)

## Indicadores de progreso a mostrar

```
🔄 [1/N] Preparando entorno...
🔄 [2/N] Obteniendo información del PR...
🔄 [3/N] Analizando seguridad...
🔄 [4/N] Analizando código...
🔄 [5/N] Generando reporte...
✅ Análisis completado: {OUTPUT_FILE}
```

## Detección de tecnología — matriz rápida

| Archivo | Lenguaje | Framework probable |
|---------|----------|--------------------|
| `package.json` | Node.js | Express / NestJS / Next.js |
| `pom.xml` | Java | Spring Boot / Maven |
| `build.gradle` | Java/Kotlin | Spring Boot / Gradle |
| `requirements.txt` | Python | Django / Flask / FastAPI |
| `pyproject.toml` | Python | Poetry / FastAPI |
| `go.mod` | Go | Gin / Echo / Fiber |

## Detección de arquitectura

```bash
ls -d src/**/controllers src/**/services src/**/repositories 2>/dev/null && echo "LAYERED"
ls -d src/**/domain src/**/application src/**/infrastructure 2>/dev/null && echo "HEXAGONAL"
ls -d cmd pkg internal 2>/dev/null && echo "GO_STANDARD"
```
