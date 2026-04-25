from __future__ import annotations

import argparse
from pathlib import Path

from cotizador.application.process_inbox import ProcessInboxUseCase
from cotizador.classifier import RuleBasedEmailClassifier
from cotizador.config.env import load_local_env
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Procesa emails y genera respuestas de cotizacion.")
    parser.add_argument("--input", default="data/emails.json", help="Ruta al JSON con emails de entrada.")
    parser.add_argument("--audit-log", default="out/processed_emails.jsonl", help="Ruta del log JSONL de salida.")
    parser.add_argument(
        "--webhook-url",
        default=None,
        help="URL de webhook externo para publicar cada resultado procesado.",
    )
    parser.add_argument(
        "--google-sheets-webhook-url",
        default=None,
        help="URL de Google Apps Script Web App para registrar resultados en Google Sheets.",
    )
    return parser


def main() -> None:
    load_local_env()
    args = build_parser().parse_args()

    rates = default_rate_table()
    repository = JsonEmailRepository(Path(args.input))
    audit = JsonlAuditPublisher(Path(args.audit_log))

    publishers = [audit]
    if args.webhook_url:
        publishers.insert(0, SafePublisher(WebhookPublisher(args.webhook_url)))
    if args.google_sheets_webhook_url:
        publishers.insert(0, SafePublisher(GoogleSheetsPublisher(args.google_sheets_webhook_url)))
    publisher = CompositePublisher(*publishers)

    use_case = ProcessInboxUseCase(
        repository=repository,
        publisher=publisher,
        classifier=RuleBasedEmailClassifier(),
        extractor=ShipmentRequestExtractor(rates),
        calculator=QuoteCalculator(rates),
        response_builder=ResponseBuilder(),
        email_sender=build_email_sender_from_env(),
    )

    results = use_case.execute()
    for result in results:
        print("=" * 80)
        print(f"{result.email.id} | {result.email.sender}")
        print(f"Clasificacion: {result.classification.category.value} | Accion: {result.action}")
        if result.response:
            print("\nRespuesta:")
            print(result.response)


if __name__ == "__main__":
    main()
