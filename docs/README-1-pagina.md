# Mini-cotizador Transportes La Serena - resumen de entrega

Autor: Bruno San Martin Navarro - https://www.linkedin.com/in/sanmabruno/

## Herramientas elegidas

Elegimos Python + FastAPI para el motor de clasificacion, extraccion y calculo porque las tarifas del brief tienen que ser testeables, auditables y reproducibles. React/Vite se usa como dashboard de demo para mostrar el flujo en vivo. Google Sheets Apps Script registra la auditoria externa y Gmail SMTP envia cotizaciones reales, cumpliendo el requisito de integracion real. Tambien queda disponible un webhook generico para conectar Make, Zapier, n8n, Slack o Airtable sin cambiar el nucleo.

Descartamos Make/Zapier como motor principal porque son rapidos para prototipos, pero pueden crecer en costo por tarea y son menos comodos para versionar reglas y tests. n8n es buena alternativa, pero agrega operacion self-hosted. Apps Script puro integra bien con Google, pero es mas debil para mantener calculos complejos y pruebas. Airtable sirve como interfaz operativa, pero no mejora el control del motor de tarifas.

## Uso de IA y prompt

Use IA para disenar el criterio de clasificacion/redaccion y para iterar el prompt. Para un flujo productivo usaria GPT-4.1 mini o equivalente liviano: buen espanol, bajo costo y latencia suficiente para responder bajo el SLA de 5 minutos. Los montos no se dejan libres al modelo; el sistema entrega al prompt un payload cerrado con clasificacion, faltantes, ruta, pallets, recargos, descuentos y totales calculados.

Prompt final literal:

```text
Actua como asistente de ventas de Transportes La Serena Ltda., empresa chilena de logistica.

Contexto operativo:
- Solo debes redactar respuestas para emails clasificados por el sistema como cotizacion o cotizacion_ambigua.
- Las tarifas y calculos ya fueron resueltos por el motor deterministico del sistema.
- No inventes rutas, origen, destino, cantidades, dimensiones, tipo de carga, valor declarado, seguro ni precios.
- Si el payload trae quote_total_clp, usa exactamente ese monto y no recalcules.
- Si faltan datos obligatorios, pide solo esos datos faltantes y no entregues precio.
- Si el email fue clasificado como spam_comercial, tracking_request u otro, no redactes cotizacion.

Tono:
- Profesional, claro y breve.
- Espanol de Chile, sin exceso de formalidad.
- Firma como "Equipo Transportes La Serena".

Entrada esperada:
- sender
- classification
- missing_fields
- route
- pallet_count
- cargo_type
- monthly_trips
- quote_total_clp
- contract_total_clp
- applied_surcharges
- applied_discounts
- assumptions

Salida:
- Un cuerpo de email listo para enviar.
- Explica recargos/descuentos solo si vienen en applied_surcharges o applied_discounts.
- Incluye consideraciones solo si vienen en assumptions.
```

La comparacion Claude vs GPT esta preparada en `scripts/run_model_comparison.py` y `docs/model-comparison.md`. No incluyo respuestas inventadas si no existen credenciales reales; el script genera `docs/model-comparison-results.md` cuando se configuran `OPENAI_API_KEY` y `ANTHROPIC_API_KEY`.

## Clasificacion y casos ambiguos

El flujo clasifica antes de cotizar. Email 1 y Email 3 son cotizaciones validas y reciben respuesta con precio. Email 2 es una solicitud ambigua: pide datos faltantes y no inventa monto. Email 4 es oferta comercial y se archiva. Email 5 es tracking y se deriva a operaciones. Si manana llega un email ambiguo fuera de categorias, queda como `other`: no recibe precio automatico y se deriva a revision humana.

## Escalabilidad y observabilidad

Para 500 emails mensuales cambiaria la entrada desde JSON a Gmail API con deduplicacion por `message_id`, cola de reintentos, estados por email, alertas cuando falle SMTP/Sheets y dashboard operativo. Hoy ya existe auditoria JSONL, registro en Google Sheets, resumen de metricas, endpoint `/integrations/status`, deduplicacion en Apps Script por `email_id` + fecha y tests backend/frontend para evitar regresiones.
