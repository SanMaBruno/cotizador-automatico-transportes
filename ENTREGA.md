# Entrega Jaiar Labs - Mini-cotizador

## A. Flujo funcional

El backend Python toma `data/emails.json`, clasifica los 5 emails, calcula cotizaciones con las tarifas del PDF y expone el flujo por CLI y por FastAPI.

Comando con integracion externa real:

```bash
PYTHONPATH=src python3 -m cotizador.presentation.cli --input data/emails.json --audit-log out/entrega_webhook.jsonl --webhook-url https://httpbin.org/post
```

API local para el frontend:

```bash
PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app --reload --host 127.0.0.1 --port 8000
```

API con integracion externa real por webhook:

```bash
COTIZADOR_WEBHOOK_URL=https://httpbin.org/post PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app --reload --host 127.0.0.1 --port 8000
```

API con Google Sheets real:

```bash
COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL="https://script.google.com/macros/s/..." PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app --reload --host 127.0.0.1 --port 8000
```

El Apps Script esta en `docs/google-sheets-apps-script.js`. Al procesar, cada email queda como fila en Google Sheets.

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## B. Demostracion visual

Dashboard React/Vite en `frontend/`, conectado al backend FastAPI local. Screenshots:

- `docs/screenshots/frontend-connected-desktop.png`
- `docs/screenshots/frontend-connected-mobile.png`

La UI muestra metricas, cada email procesado, clasificacion, accion tomada, cotizacion/respuesta si corresponde y derivacion/archivo si no aplica.

## C. README / Doc explicativo

El archivo `README.md` responde herramienta elegida, descartes, modelo IA, prompt literal, comparacion de modelos, clasificacion, ambiguos y observabilidad para 500 emails/mes.

## Estado verificado

- Backend: `20 tests OK`.
- Frontend: `npm test -- --run` OK (`3 tests`).
- Frontend build: `npm run build` OK.
- Integracion navegador: Playwright contra `http://127.0.0.1:5173` + FastAPI en `http://127.0.0.1:8000` OK.
- Tiempo de procesamiento local: muy inferior a 5 minutos para los 5 emails.

## Criterios de evaluacion

- Flujo funcional 25%: corre por CLI, API y frontend; integra con webhook/Google Sheets; respuestas tienen tarifas correctas.
- Clasificacion 20%: separa cotizacion, solicitud incompleta, oferta comercial y tracking; no envia precios a no cotizables.
- Stack 20%: Python/FastAPI + React + webhook; costo bajo, curva razonable, reglas testeables.
- Prompt 20%: prompt literal en README, con negocio, faltantes y prohibicion de inventar precios.
- Criterio IA 15%: no se usa IA para calcular, se evitan alucinaciones, queda auditoria JSONL y plan de observabilidad.
