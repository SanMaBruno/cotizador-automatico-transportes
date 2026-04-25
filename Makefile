.PHONY: install test run-backend run-frontend dev process health

install:
	pip install -r requirements.txt
	cd frontend && npm install

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
	cd frontend && npm test -- --run

run-backend:
	PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app \
		--host 127.0.0.1 --port 8000

run-frontend:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173

dev:
	@echo "Levantando backend y frontend..."
	@PYTHONPATH=src python3 -m uvicorn cotizador.presentation.api:app \
		--host 127.0.0.1 --port 8000 & \
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173

process:
	curl -X POST http://127.0.0.1:8000/process

health:
	curl http://127.0.0.1:8000/health
