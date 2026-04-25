# Guion video demo - menos de 3 minutos

Objetivo del video: mostrar que el flujo corre en vivo, clasifica antes de cotizar, escribe en Google Sheets y envia emails reales solo cuando corresponde.

## Antes de grabar

1. Abre tres ventanas: frontend, Google Sheets y Gmail.
2. En la terminal valida integraciones:

```bash
curl http://127.0.0.1:8000/integrations/status
```

Debe mostrar:

- `google_sheets.configured: true`
- `email.enabled: true`
- `dry_run: false`
- `warnings: []`

3. En Google Sheets, deja la hoja `cotizador_jaiar_labs` limpia o con solo 5 filas.
4. En Gmail, prepara una busqueda:

```text
subject:"Cotizacion Transportes La Serena"
```

## Guion sugerido

### 0:00 - 0:20 | Contexto

"Hola, soy Bruno San Martin Navarro. Este es el mini-cotizador para Transportes La Serena. El objetivo es procesar cinco emails de ventas, clasificar primero cuales son cotizables y responder solo los que corresponden, con integracion real a Google Sheets y Gmail."

Mostrar:

- Frontend en `http://127.0.0.1:5173`.
- Panel de integraciones sin warnings.

### 0:20 - 0:45 | Arquitectura y criterio

"Elegi Python con FastAPI para el motor porque las tarifas deben ser auditables y testeables. React muestra la operacion en vivo. Google Sheets deja auditoria externa y Gmail prueba envio real. La IA se usa con criterio para clasificacion/redaccion sobre datos estructurados; los montos no quedan libres al modelo para evitar alucinaciones."

Mostrar:

- Tarjeta de integracion externa.
- Metricas vacias o ultimo run.

### 0:45 - 1:20 | Procesamiento en vivo

"Ahora proceso los cinco emails. Antes de cotizar, el flujo clasifica cada mensaje."

Accion:

- Click en `Procesar 5 emails`.

Decir mientras carga:

"Email 1 y Email 3 son cotizaciones validas. Email 2 es ambiguo, entonces pide datos y no inventa precio. Email 4 es oferta comercial y Email 5 es tracking, por eso no reciben cotizacion."

Mostrar:

- Metricas: 5 procesados, 2 cotizaciones, 1 incompleto, 2 filtrados/derivados.
- Tarjetas de Email 1 y Email 3 con totales.

### 1:20 - 1:55 | Google Sheets

"Ahora voy a Google Sheets. Aca queda la auditoria externa del flujo. Cada email queda con `email_id`, clasificacion, accion, total cotizado y respuesta. Tambien agregue deduplicacion: si proceso de nuevo el mismo `email_id` el mismo dia, no duplica filas."

Mostrar:

- Hoja `cotizador_jaiar_labs`.
- 5 filas esperadas.
- Email 1 con `$82.800 CLP`.
- Email 3 con `$1.734.240 CLP` y contrato `$10.405.440 CLP`.

### 1:55 - 2:25 | Gmail real

"Finalmente, Gmail. Como active `COTIZADOR_EMAIL_OVERRIDE_TO`, las respuestas reales llegan a mi correo de demo y no a remitentes ficticios del dataset. Solo llegan dos emails: Email 1 y Email 3."

Mostrar:

- Busqueda `subject:"Cotizacion Transportes La Serena"`.
- Abrir Email 1: asunto con `email-1`, monto `$82.800 CLP`.
- Abrir Email 3: asunto con `email-3`, monto `$1.734.240 CLP`.

### 2:25 - 2:55 | Cierre

"Con esto se cumplen los dos requisitos no negociables: integracion real con herramientas externas y clasificacion previa antes de cotizar. Para escalar a 500 emails mensuales agregaria Gmail API como entrada, cola de reintentos, trazabilidad por `message_id`, dashboard de errores y alertas cuando falle Sheets, SMTP o quede un email ambiguo."

Mostrar:

- Frontend con resultado final.
- Opcional: README o `docs/README-1-pagina.md`.

## Checklist visual rapido

- Frontend procesa los 5 emails en vivo.
- Google Sheets tiene 5 filas sin duplicados.
- Gmail muestra solo 2 correos reales.
- Email 2, 4 y 5 no reciben cotizacion.
