## Descripción

<!-- ¿Qué cambia y por qué? Referencia al Issue si aplica: Closes #123 -->
<!-- Jira: OLIMPUSSW-{número} -->

## Tipo de cambio

- [ ] `feat` — nueva funcionalidad
- [ ] `fix` — corrección de bug
- [ ] `refactor` — sin cambio de comportamiento
- [ ] `test` — solo tests
- [ ] `docs` — solo documentación
- [ ] `chore` — mantenimiento (deps, config, CI)
- [ ] `perf` — mejora de rendimiento

## Checklist

### Código
- [ ] Sin `print` ni logs de debug en código de producción
- [ ] Sin contraseñas, tokens ni secretos hardcodeados
- [ ] Type hints / tipos explícitos en funciones públicas (si aplica al stack)
- [ ] Sigue la arquitectura definida en `ANALISIS_APLICACION.md`

### Tests
- [ ] Cobertura >= 97% (verificado con `make test`)
- [ ] Tests nombrados por escenario de negocio
- [ ] Sin `skip` sin justificación documentada
- [ ] Tests de integración para endpoints/flujos nuevos

### Calidad
- [ ] `make lint` pasa sin errores
- [ ] `make format` aplicado
- [ ] CI verde en este PR

### Migraciones (si aplica)
- [ ] Migración incluida y probada (upgrade y downgrade)

### Documentación
- [ ] `CHANGELOG.md` actualizado en sección `[Unreleased]`
- [ ] `ENVIRONMENT.md` actualizado si hay variables nuevas
- [ ] `docs/guide/` actualizado si hay cambios de arquitectura

## Contexto adicional

<!-- Screenshots, diagramas, notas de implementación relevantes -->

---

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
