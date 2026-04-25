# Demo rapida

La demo principal es el dashboard React/Vite en `frontend/`, conectado a FastAPI local.

```bash
PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev
```

Abrir `http://127.0.0.1:5173` y presionar `Procesar emails`.

Screenshots:

- `docs/screenshots/frontend-connected-desktop.png`
- `docs/screenshots/frontend-connected-mobile.png`

Integracion externa:

- Webhook generico: `COTIZADOR_WEBHOOK_URL`.
- Google Sheets real: `COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL` + `docs/google-sheets-apps-script.js`.

Validacion observada:

1. `email-1` cotiza `$82.800 CLP`.
2. `email-2` pide datos faltantes sin precio.
3. `email-3` cotiza `$1.734.240 CLP` mensual y `$10.405.440 CLP` por 6 meses.
4. `email-4` se archiva como oferta comercial.
5. `email-5` se deriva a operaciones.
