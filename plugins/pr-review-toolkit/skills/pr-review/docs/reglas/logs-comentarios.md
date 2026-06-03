# 📝 Reglas — Logs y Comentarios

---

## 1. Idioma

**Regla:** Logs y comentarios **en inglés**.

```javascript
// ❌ Incorrecto
logger.info("Procesando orden del usuario");
// Este método calcula el total

// ✅ Correcto
logger.info("Processing user order");
// This method calculates the total
```

Si se encuentran logs o comentarios en español: marcar como MEJORA (prioridad media).

---

## 2. Niveles de log

| Nivel | Cuándo usar |
|-------|-------------|
| **ERROR** | Errores que requieren atención (fallo de BD, servicio externo caído) |
| **WARN** | Situaciones anormales pero manejables (retry, rate limit cercano) |
| **INFO** | Eventos importantes del flujo normal (request procesado, operación completada) |
| **DEBUG** | Detalles para debugging (valores de variables, pasos internos) |

```javascript
// ❌ Niveles incorrectos
logger.info(`Variable x = ${x}`);          // debería ser DEBUG
logger.debug("User logged in");            // debería ser INFO
logger.error("Invalid input received");    // debería ser WARN (recuperable)

// ✅ Niveles correctos
logger.debug(`Processing item: ${itemId}`);
logger.info("Order created successfully", { orderId, userId });
logger.warn("Rate limit approaching threshold", { current, limit });
logger.error("Database connection failed", { error: err.message });
```

---

## 3. Contenido de logs

### Incluir
- ✅ IDs de entidades (`orderId`, `userId`, `siteId`)
- ✅ Operación que se realiza
- ✅ Resultado de la operación
- ✅ Duración de operaciones importantes (`executionTime`)
- ✅ Correlation IDs para trazabilidad

### Evitar
- ❌ Datos sensibles (passwords, tokens, PII)
- ❌ Logs dentro de loops sin control de volumen
- ❌ Stack traces completos en nivel INFO

```javascript
// ❌ Información sensible
logger.info(`User login: email=${email}, password=${password}`);

// ❌ Log en loop sin control (puede ser millones de items)
for (const item of items) {
    logger.info(`Processing ${item}`);
}

// ✅ Correcto
logger.info(`Processing batch of ${items.length} items`, { userId, siteId });
```

---

## 4. Comentarios en código

### Comentar
- ✅ El "por qué", no el "qué"
- ✅ Decisiones no obvias
- ✅ Advertencias sobre edge cases
- ✅ TODOs con ticket de referencia

### No comentar
- ❌ Código obvio
- ❌ Código comentado (eliminarlo)
- ❌ Comentarios desactualizados

```javascript
// ❌ Inútil
counter += 1; // Increment counter by 1

// ❌ Código muerto comentado
// old_implementation();

// ✅ Útil — explica el POR QUÉ
// Using 5s timeout: external API has 3s SLA + buffer for network jitter
const TIMEOUT = 5000;

// ✅ TODO con contexto
// TODO(TICKET-123): Remove this workaround when new API is available
```

---

## 5. Checklist

- [ ] ¿Logs y comentarios están en inglés?
- [ ] ¿Los niveles de log son apropiados?
- [ ] ¿No se loggean datos sensibles?
- [ ] ¿Los comentarios explican "por qué", no "qué"?
- [ ] ¿No hay código comentado (dead code)?
- [ ] ¿Los TODOs tienen contexto/ticket?
