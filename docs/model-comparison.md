# Diff Claude vs GPT-4o

Estado: preparado, no ejecutado en esta maquina porque no existen `OPENAI_API_KEY` ni `ANTHROPIC_API_KEY` en el entorno. No se incluyen respuestas inventadas.

## Comando para ejecutar la comparacion real

```bash
cd /Users/relke/Documents/desafio-tecnico-jaiar-labs
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
python3 scripts/run_model_comparison.py
```

El script lee el prompt literal desde `prompts/final-response-prompt.md`, usa el payload del Email 1 y escribe `docs/model-comparison-results.md`.

## Payload usado para Email 1

```json
{
  "sender": "psepulveda@ferreteriaeltornillo.cl",
  "classification": "cotizacion",
  "missing_fields": [],
  "route": "Santiago -> La Serena",
  "pallet_count": 4,
  "cargo_type": "estandar",
  "monthly_trips": 1,
  "quote_total_clp": 82800,
  "contract_total_clp": "",
  "applied_surcharges": ["Urgencia (<48h) +15%: $10.800 CLP"],
  "applied_discounts": [],
  "assumptions": []
}
```

## Criterio de evaluacion del diff

- El modelo debe usar exactamente `$82.800 CLP`.
- No debe recalcular ni inventar peso, dimensiones, seguro, fecha exacta ni disponibilidad.
- Debe mencionar la ruta Santiago -> La Serena, 4 pallets estandar y recargo de urgencia.
- Debe cerrar con `Equipo Transportes La Serena`.
- Para Andrea, elegiria la salida mas breve y operacional: asunto claro, monto visible, recargo explicado en una linea y sin texto comercial innecesario.

