# 📖 Contexto del Proyecto — README y AGENTS.md

Cargar **siempre, antes de analizar el diff**. El README y AGENTS.md del proyecto revelan convenciones que el diff no muestra.

---

## Por qué es importante

Sin este contexto, el análisis puede:
- Marcar como "code smell" un patrón que es convención del proyecto
- Pasar por alto violations de convenciones internas
- Proponer refactors que contradicen decisiones de arquitectura documentadas
- Ignorar testing requirements específicos del equipo

---

## Comandos para obtener el contexto

```bash
# README del proyecto
gh api repos/melisource/{REPO}/contents/README.md \
  --jq '.content' | base64 -d 2>/dev/null || \
gh api repos/melisource/{REPO}/contents/README.md \
  --jq '.content' | base64 --decode

# AGENTS.md (convenciones para agentes/LLMs)
gh api repos/melisource/{REPO}/contents/AGENTS.md \
  --jq '.content' | base64 -d 2>/dev/null

# CLAUDE.md (si existe)
gh api repos/melisource/{REPO}/contents/CLAUDE.md \
  --jq '.content' | base64 -d 2>/dev/null

# CONTRIBUTING.md
gh api repos/melisource/{REPO}/contents/CONTRIBUTING.md \
  --jq '.content' | base64 -d 2>/dev/null

# Verificar qué archivos de convención existen
gh api repos/melisource/{REPO}/contents/ \
  --jq '.[].name' | grep -iE "(readme|agents|claude|contributing|conventions|architecture)"
```

---

## Qué extraer del README

### Arquitectura y estructura
- ¿Qué patrón arquitectónico usa el proyecto (layered, hexagonal, microservices)?
- ¿Cómo está organizado el código (directorios, módulos)?
- ¿Cuáles son los componentes principales?

### Convenciones de desarrollo
- Estilo de código, linters configurados
- Cómo se nombran variables, funciones, archivos
- Patrones de manejo de errores del proyecto
- Cómo se estructura el logging

### Contexto de dominio
- ¿Qué hace el servicio?
- ¿Cuáles son los conceptos clave del dominio?
- ¿Hay glosario de términos?

### Testing
- ¿Qué framework de tests se usa?
- ¿Qué cobertura mínima se requiere?
- ¿Hay tests de integración requeridos?

---

## Qué extraer del AGENTS.md

`AGENTS.md` es específicamente para guiar a agentes/LLMs en el proyecto. Contiene:
- Qué hacer y qué no hacer al modificar código
- Patrones específicos del proyecto
- Reglas de naming
- Cómo correr tests localmente
- Qué archivos son críticos y requieren especial cuidado

> Si existe `AGENTS.md`, tiene **máxima prioridad** sobre las guías genéricas de los módulos de análisis.

---

## Cómo usar el contexto en el análisis

Una vez leídos, usar el contexto para:

1. **Calibrar los puntos fuertes**: validar que el código sigue las convenciones del proyecto
2. **Filtrar falsos positivos**: no marcar como "mejora" algo que es convención intencional
3. **Detectar violations**: código que contradice lo establecido en README/AGENTS
4. **Enriquecer recomendaciones**: sugerir cambios alineados con el estilo del proyecto

### Ejemplo de aplicación
```
README dice: "Todos los servicios usan patrón Repository con singleton"
Diff muestra: new Repository() dentro del service

→ Esto es una violation de la convención del proyecto → MEJORA
```

```
README dice: "Usamos fire-and-forget para operaciones de auditoría"
Diff muestra: auditPendingAsync con setImmediate

→ Esto cumple la convención → no marcar como problema
```

---

## Si los archivos no existen

Si `README.md` o `AGENTS.md` no están disponibles:
- Inferir convenciones del código existente en el PR
- Mencionar en el análisis que no se encontró documentación de convenciones
- Basar el análisis solo en mejores prácticas generales (módulos 01-15)
