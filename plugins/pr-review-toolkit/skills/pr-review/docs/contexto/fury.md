# 🔥 Contexto — Servicios Fury (MercadoLibre)

Cargar cuando el PR pertenece a un repo de Fury / MeLi.

---

## 1. Rate Limit de Fury

**Algoritmo:** Token Bucket en ventana de 1 segundo. 1 token = 1 request.
**Respuesta si se excede:** HTTP 429 (Too Many Requests)
**Configuración:** En el panel de Fury, **no en la aplicación**.

### Cuándo usar Rate Limit
✅ El ámbito tiene dependencias en recursos/APIs inelásticos
✅ Se quiere proteger contra picos de tráfico inorgánicos (10x, 20x del normal)

### Cuándo NO usar Rate Limit
❌ El ámbito puede escalar elásticamente y se quiere atender todo el tráfico
❌ Se necesita rate limiting de grano fino desde la app
❌ Se necesita personalizar el payload/status de rechazo

### Checklist en PR
- [ ] ¿El PR modifica endpoints que podrían necesitar rate limiting?
- [ ] ¿Hay nuevas dependencias externas que requieran protección?
- [ ] ¿El código maneja HTTP 429 con backoff?

```javascript
// ✅ Manejar 429 correctamente
if (response.status === 429) {
    // Retry con exponential backoff, no retry storm
    await sleep(retryAfter || 1000);
    return retryRequest();
}
```

---

## 2. Observabilidad en Fury

### Métricas Datadog
- Nomenclatura: `{scope}.{metric_name}` con tags `site`, `operation`, `status`
- [ ] ¿Hay métricas para nuevos endpoints/operaciones?
- [ ] ¿Los tags permiten filtrar por site/ambiente?
- [ ] ¿Se mide tiempo de ejecución con `histogram`?

### Logs
- Formato estructurado (JSON), nivel INFO en producción
- [ ] ¿Los logs incluyen `request_id`/`correlation_id`?
- [ ] ¿No se loggean datos sensibles (PII, tokens)?
- [ ] ¿Los errores usan nivel ERROR, warnings nivel WARN?

### Headers de trazabilidad Fury
Headers estándar que deben propagarse:
```
x-request-id           → ID de request para trazabilidad
x-api-client-application → App origen
x-api-client-scope     → Scope origen
x-fury-user            → Usuario Fury
```

---

## 3. Base de datos en Fury

- [ ] ¿Hay migraciones de esquema incluidas en el PR?
- [ ] ¿Las queries tienen índices apropiados?
- [ ] ¿Las queries de listas tienen límite/paginación?
- [ ] ¿Se usan connection pools configurados en Fury?
- [ ] ¿Los valores monetarios usan `DECIMAL(15,2)`?

---

## 4. Deploy en Fury

### Checklist pre-deploy
- [ ] Verificar configuración por ambiente (staging, prod)
- [ ] Validar variables de entorno en panel de Fury
- [ ] Revisar límites de recursos (CPU, memoria)
- [ ] Verificar health checks (`/ping` endpoint)
- [ ] Confirmar que migraciones de BD se ejecutan antes del deploy del servicio

### Rollback
- Fury permite rollback automático
- Si hay migraciones: documentar pasos de rollback manual

---

## 5. Arquitectura típica de un scope Fury

```
/api
  /controllers    # Endpoints HTTP
  /services       # Lógica de negocio
  /domain
    /models       # Entidades / esquemas de BD
    /repository   # Acceso a datos
  /utils
    /constants    # Constantes compartidas
    /logger       # Wrapper de logging
/app              # Frontend (si aplica)
/tests
  /unit
```
