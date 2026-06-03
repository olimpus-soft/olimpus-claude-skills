# Política de seguridad

## Versiones soportadas

| Versión | Soporte de seguridad |
|---|---|
| última en `main` | ✅ Activo |
| versiones anteriores | ❌ Sin soporte |

## Reportar una vulnerabilidad

**NO abrir un issue público para vulnerabilidades de seguridad.**

Reportar de forma privada a: **miguelmoralescoterio@gmail.com**

Incluir en el reporte:
- Descripción del problema
- Pasos para reproducirlo
- Impacto potencial estimado
- Versión afectada (commit o tag)

Tiempo de respuesta esperado: **48 horas hábiles**.

## Proceso de divulgación

1. Reporte recibido y acuse de recibo en < 48h
2. Evaluación de severidad e impacto
3. Desarrollo de fix en rama privada
4. Release de parche con nota en `CHANGELOG.md`
5. Divulgación pública tras el deploy (responsible disclosure)

## Reporte de uso no autorizado

Si detectas que este software está siendo utilizado, copiado o distribuido
sin autorización de Olimpus Soft SAS, repórtalo de inmediato a:
**miguelmoralescoterio@gmail.com** con asunto `[LEGAL] Uso no autorizado`.

Olimpus Soft SAS tomará las acciones legales correspondientes conforme a los
artículos 270, 271 y 272 del Código Penal colombiano y la Ley 23 de 1982.

## Buenas prácticas del proyecto

- Secretos y credenciales NUNCA en el repositorio — usar variables de entorno
- Imagen Docker construida desde usuario no-root
- Dependencias escaneadas con Trivy y Bandit (o equivalente según stack) en cada CI
- Dependabot habilitado para actualizaciones automáticas de dependencias
