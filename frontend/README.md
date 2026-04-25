# Frontend - Mini-cotizador

Dashboard React/Vite para visualizar el flujo de cotizacion. Por defecto consume el backend FastAPI local.

## Ejecutar

```bash
npm install
cp .env.example .env
npm run dev
```

Variables:

```bash
VITE_API_BASE_URL=http://localhost:8000
# VITE_USE_MOCK=true  # solo para preview sin backend Python
```

Para mostrar estado real de Google Sheets en el flujo, levanta el backend con:

```bash
COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL="https://script.google.com/macros/s/..." PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app --reload --host 127.0.0.1 --port 8000
```

## Scripts

```bash
npm test -- --run
npm run build
```
