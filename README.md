# olimpus-claude-skills

[![claude-code-plugin](https://img.shields.io/badge/claude--code-plugin-blueviolet)](https://github.com/olimpus-soft/olimpus-claude-skills)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)

Plugin marketplace de Claude Code de OlimpusSoft — 13 skills para review exhaustivo de PRs, análisis de calidad de tests y guías de arquitectura por stack.

## Instalación

```
/plugin marketplace add olimpus-soft/olimpus-claude-skills
/plugin install pr-review-toolkit@latest
```

## Plugins disponibles

### pr-review-toolkit

| Skill | Descripción |
|---|---|
| `/pr-review` | Análisis exhaustivo de PR con veredicto formal (APROBADO / CAMBIOS REQUERIDOS / RECHAZADO) y comentarios inline en GitHub |
| `/quality-test` | Auditoría de calidad de tests: smells, cobertura, mutación readiness, edge cases |
| `/pr-comments-resolver` | Clasifica y resuelve comentarios activos de PR (fix de código o respuesta) |
| `/pr-generate` | Genera descripción completa del PR lista para publicar en GitHub |
| `/commitmsg` | Genera mensaje de commit en formato OlimpusSoft con tipo, ticket Jira y co-autor del modelo |
| `/review-py` | Checklist de revisión específico para Python: ruff, mypy, FastAPI, pydantic, async |
| `/review-frontend` | Checklist para TypeScript/React: hooks, accesibilidad, bundle size, performance |
| `/review-go` | Checklist para Go: error handling, goroutines, interfaces, testing |
| `/review-java` | Checklist para Java/Spring Boot: SOLID, inyección, transacciones, excepciones |
| `/arch-py` | Patrones de arquitectura Python: hexagonal, ports & adapters, DDD, async |
| `/arch-frontend` | Patrones frontend: componentes, estado, routing, design system |
| `/arch-go` | Patrones Go: clean architecture, handlers, middlewares, repositories |
| `/arch-java` | Patrones Java: hexagonal, Spring layers, aggregate roots, eventos de dominio |

## Uso en CI — `claude.yml`

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    model: claude-opus-4-7
    prompt: |
      /plugin marketplace add olimpus-soft/olimpus-claude-skills
      /plugin install pr-review-toolkit@latest
      /pr-review ${{ github.repository }}#${{ github.event.pull_request.number }}
      /quality-test
    claude_args: |
      --effort high
      --append-system-prompt "Responde en español colombiano neutro. Aplica reglas del repo (CLAUDE.md + AGENTS.md). Prioriza seguridad. Cierra con /pr-comments-resolver y/o Paso 6 desbloqueo del pr-review."
    allowed_tools: "Bash,Read,Write,Edit,Grep,Glob,Skill"
  env:
    GITHUB_TOKEN: ${{ secrets.GH_PACKAGES_READ_TOKEN }}
```

## Changelog

Ver [CHANGELOG.md](CHANGELOG.md).
