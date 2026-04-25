from __future__ import annotations

import json
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from cotizador.application.ports import IntegrationPublisher
from cotizador.domain.entities import ProcessedEmail


class JsonlAuditPublisher(IntegrationPublisher):
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def publish(self, processed_email: ProcessedEmail) -> None:
        with self._output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(_to_payload(processed_email), ensure_ascii=False) + "\n")


class WebhookPublisher(IntegrationPublisher):
    def __init__(self, url: str, timeout_seconds: int = 10) -> None:
        self._url = url
        self._timeout_seconds = timeout_seconds

    def publish(self, processed_email: ProcessedEmail) -> None:
        body = json.dumps(_to_payload(processed_email), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds):
            return


class GoogleSheetsPublisher(IntegrationPublisher):
    """Publishes a compact row payload to a Google Apps Script Web App.

    The Apps Script writes each payload into a Google Sheet. This avoids storing
    Google credentials in the project and still integrates with a real external
    tool owned by the user.
    """

    def __init__(self, url: str, timeout_seconds: int = 10) -> None:
        self._url = url
        self._timeout_seconds = timeout_seconds

    def publish(self, processed_email: ProcessedEmail) -> None:
        body = json.dumps(_to_google_sheets_payload(processed_email), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds):
            return


class CompositePublisher(IntegrationPublisher):
    def __init__(self, *publishers: IntegrationPublisher) -> None:
        self._publishers = publishers

    def publish(self, processed_email: ProcessedEmail) -> None:
        for publisher in self._publishers:
            publisher.publish(processed_email)


class SafePublisher(IntegrationPublisher):
    def __init__(self, publisher: IntegrationPublisher, fallback: Optional[IntegrationPublisher] = None) -> None:
        self._publisher = publisher
        self._fallback = fallback

    def publish(self, processed_email: ProcessedEmail) -> None:
        try:
            self._publisher.publish(processed_email)
        except Exception as exc:  # pragma: no cover - exercised manually with network failures.
            if self._fallback is not None:
                self._fallback.publish(processed_email)
            print(f"WARNING: external publish failed for {processed_email.email.id}: {exc}")


def _to_payload(processed_email: ProcessedEmail) -> dict:
    payload = asdict(processed_email)
    payload["classification"]["category"] = processed_email.classification.category.value
    if processed_email.quote is not None:
        payload["quote"] = asdict(processed_email.quote)
    return payload


def _to_google_sheets_payload(processed_email: ProcessedEmail) -> dict:
    quote_total = processed_email.quote.total_clp if processed_email.quote else ""
    contract_total = processed_email.quote.contract_total_clp if processed_email.quote else ""
    response = processed_email.response or ""
    return {
        "email_id": processed_email.email.id,
        "sender": processed_email.email.sender,
        "classification": processed_email.classification.category.value,
        "action": processed_email.action,
        "quote_total_clp": quote_total,
        "contract_total_clp": contract_total or "",
        "missing_fields": ", ".join(processed_email.missing_fields),
        "response": response,
        "reason": processed_email.classification.reason,
    }
