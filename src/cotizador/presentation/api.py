from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cotizador.application.process_inbox import ProcessInboxUseCase
from cotizador.classifier import RuleBasedEmailClassifier
from cotizador.config.env import load_local_env
from cotizador.domain.entities import CargoType, Email, EmailCategory, ProcessedEmail
from cotizador.domain.rates import default_rate_table
from cotizador.infrastructure.json_email_repository import JsonEmailRepository
from cotizador.integrations import (
    CompositePublisher,
    GoogleSheetsPublisher,
    JsonlAuditPublisher,
    SafePublisher,
    WebhookPublisher,
    build_email_sender_from_env,
)
from cotizador.quotation import QuoteCalculator, ShipmentRequestExtractor
from cotizador.responder import ResponseBuilder


load_local_env()

app = FastAPI(title="Mini-cotizador Transportes La Serena", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_LATEST_RUN: Optional[Dict[str, Any]] = None


def _input_path() -> Path:
    return Path(os.getenv("COTIZADOR_EMAILS_PATH", "data/emails.json"))


def _audit_path() -> Path:
    return Path(os.getenv("COTIZADOR_AUDIT_PATH", "out/api_processed_emails.jsonl"))


def _build_use_case() -> ProcessInboxUseCase:
    rates = default_rate_table()
    audit_publisher = JsonlAuditPublisher(_audit_path())
    webhook_url = os.getenv("COTIZADOR_WEBHOOK_URL")
    sheets_webhook_url = os.getenv("COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL")
    publishers = [audit_publisher]
    if webhook_url:
        publishers.insert(0, SafePublisher(WebhookPublisher(webhook_url)))
    if sheets_webhook_url:
        publishers.insert(0, SafePublisher(GoogleSheetsPublisher(sheets_webhook_url)))
    publisher = CompositePublisher(*publishers)

    return ProcessInboxUseCase(
        repository=JsonEmailRepository(_input_path()),
        publisher=publisher,
        classifier=RuleBasedEmailClassifier(),
        extractor=ShipmentRequestExtractor(rates),
        calculator=QuoteCalculator(rates),
        response_builder=ResponseBuilder(),
        email_sender=build_email_sender_from_env(),
    )


def _extractor() -> ShipmentRequestExtractor:
    return ShipmentRequestExtractor(default_rate_table())


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "mode": "fastapi-local"}


@app.get("/integrations/status")
def integrations_status() -> Dict[str, Any]:
    return _integration_status()


@app.get("/emails")
def emails() -> List[Dict[str, Any]]:
    repository = JsonEmailRepository(_input_path())
    return [_email_to_api(email) for email in repository.list_inbox()]


@app.post("/process")
def process() -> Dict[str, Any]:
    global _LATEST_RUN
    results = _build_use_case().execute()
    run = _run_to_api(results)
    _LATEST_RUN = run
    return run


@app.get("/runs/latest")
def latest_run() -> Optional[Dict[str, Any]]:
    if _LATEST_RUN is None:
        return None
    return _LATEST_RUN


def _run_to_api(results: List[ProcessedEmail]) -> Dict[str, Any]:
    api_results = [_processed_to_api(result) for result in results]
    return {
        "run_id": f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "integrations": _integration_status(),
        "metrics": {
            "total": len(api_results),
            "cotizaciones_generadas": sum(
                1 for result in api_results if result["action"] == "responder_cotizacion"
            ),
            "solicitudes_incompletas": sum(
                1 for result in api_results if result["action"] == "solicitar_info"
            ),
            "filtrados_derivados": sum(
                1
                for result in api_results
                if result["action"] in {"archivar", "derivar_operaciones"}
            ),
        },
        "results": api_results,
    }


def _integration_status() -> Dict[str, Any]:
    sheets_url = os.getenv("COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL", "").strip()
    dry_run = os.getenv("COTIZADOR_EMAIL_DRY_RUN", "").lower() == "true"
    override_to = os.getenv("COTIZADOR_EMAIL_OVERRIDE_TO", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM", "").strip()
    smtp_configured = all([smtp_host, smtp_username, smtp_password, smtp_from])
    email_enabled = dry_run or smtp_configured
    warnings = []

    if not sheets_url:
        warnings.append("Google Sheets no esta configurado: falta COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL.")
    if not email_enabled:
        warnings.append("Envio de email no esta configurado: falta SMTP o COTIZADOR_EMAIL_DRY_RUN=true.")
    if email_enabled and not override_to:
        warnings.append("COTIZADOR_EMAIL_OVERRIDE_TO no esta configurado; se enviaria al remitente original del dataset.")

    return {
        "google_sheets": {
            "configured": bool(sheets_url),
            "target": _safe_url(sheets_url) if sheets_url else None,
        },
        "email": {
            "enabled": email_enabled,
            "dry_run": dry_run,
            "smtp_configured": smtp_configured,
            "override_to": override_to or None,
            "from": smtp_from or None,
        },
        "warnings": warnings,
    }


def _safe_url(url: str) -> str:
    if len(url) <= 46:
        return url
    return f"{url[:32]}...{url[-10:]}"


def _processed_to_api(processed: ProcessedEmail) -> Dict[str, Any]:
    request = _extractor().extract(processed.email)
    payload: Dict[str, Any] = {
        "email": _email_to_api(processed.email),
        "classification": _classification_to_api(processed.classification.category),
        "confidence": processed.classification.confidence,
        "action": _action_to_api(processed.action),
    }

    if processed.response:
        payload["reply"] = processed.response
    if processed.action == "reply_request_missing_quote_data" and processed.missing_fields:
        payload["missing_fields"] = processed.missing_fields
    if processed.quote:
        payload["quote"] = _quote_to_api(processed, request)
    if not processed.response:
        payload["reason"] = processed.classification.reason
    return payload


def _email_to_api(email: Email) -> Dict[str, Any]:
    return {
        "id": email.id,
        "from": email.sender,
        "subject": _subject_for(email),
        "body": email.body,
    }


def _subject_for(email: Email) -> str:
    subjects = {
        "email-1": "Cotizacion flete Santiago a La Serena",
        "email-2": "Cajas de vino al sur",
        "email-3": "Cotizacion contrato semanal refrigerado",
        "email-4": "Oferta plataforma GPS",
        "email-5": "Seguimiento guia 4782",
    }
    return subjects.get(email.id, "Email de ventas")


def _classification_to_api(category: EmailCategory) -> str:
    if category == EmailCategory.QUOTE:
        return "cotizacion"
    if category == EmailCategory.TRACKING:
        return "seguimiento"
    if category == EmailCategory.SUPPLIER_OFFER:
        return "spam_comercial"
    return "otro"


def _action_to_api(action: str) -> str:
    if action == "reply_with_quote":
        return "responder_cotizacion"
    if action == "reply_request_missing_quote_data":
        return "solicitar_info"
    if action == "forward_to_operations_tracking_queue":
        return "derivar_operaciones"
    return "archivar"


def _quote_to_api(processed: ProcessedEmail, request: Any) -> Dict[str, Any]:
    assert processed.quote is not None
    assert request.route is not None
    assert request.pallet_count is not None
    assert request.cargo_type is not None

    recargos = []
    if processed.quote.urgency_surcharge_clp:
        recargos.append(
            {
                "label": "Urgencia (<48h) +15%",
                "amount_clp": processed.quote.urgency_surcharge_clp,
            }
        )
    if processed.quote.insurance_clp:
        recargos.append(
            {
                "label": "Seguro de carga",
                "amount_clp": processed.quote.insurance_clp,
            }
        )

    descuentos = []
    if processed.quote.monthly_discount_clp:
        descuentos.append(
            {
                "label": "Contrato mensual fijo -10%",
                "amount_clp": -processed.quote.monthly_discount_clp,
            }
        )
    if processed.quote.semester_discount_clp:
        descuentos.append(
            {
                "label": "Contrato semestral -5% adicional",
                "amount_clp": -processed.quote.semester_discount_clp,
            }
        )

    return {
        "tramo": f"{request.route.origin} -> {request.route.destination}",
        "pallets": request.pallet_count,
        "tipo_pallet": _cargo_type_to_api(request.cargo_type),
        "precio_base_clp": processed.quote.base_subtotal_clp,
        "recargos": recargos,
        "descuentos": descuentos,
        "total_clp": processed.quote.total_clp,
        "viajes_mensuales": request.monthly_trips,
        "meses_contrato": request.contract_months,
        "total_contrato_clp": processed.quote.contract_total_clp,
    }


def _cargo_type_to_api(cargo_type: CargoType) -> str:
    if cargo_type == CargoType.REFRIGERATED:
        return "refrigerado"
    return "estandar"
