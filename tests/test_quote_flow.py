from __future__ import annotations

import unittest
from pathlib import Path

from cotizador.application.ports import EmailSender
from cotizador.application.ports import IntegrationPublisher
from cotizador.application.process_inbox import ProcessInboxUseCase
from cotizador.classifier import RuleBasedEmailClassifier
from cotizador.domain.entities import ProcessedEmail
from cotizador.domain.rates import default_rate_table
from cotizador.infrastructure.json_email_repository import JsonEmailRepository
from cotizador.quotation import QuoteCalculator, ShipmentRequestExtractor
from cotizador.responder import ResponseBuilder
from cotizador.integrations.email_sender import RecipientOverrideEmailSender, _normalize_smtp_password


class MemoryPublisher(IntegrationPublisher):
    def __init__(self) -> None:
        self.items = []

    def publish(self, processed_email: ProcessedEmail) -> None:
        self.items.append(processed_email)


class MemoryEmailSender(EmailSender):
    def __init__(self) -> None:
        self.messages = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.messages.append({"to": to, "subject": subject, "body": body})


class QuoteFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        rates = default_rate_table()
        self.publisher = MemoryPublisher()
        self.use_case = ProcessInboxUseCase(
            repository=JsonEmailRepository(Path("data/emails.json")),
            publisher=self.publisher,
            classifier=RuleBasedEmailClassifier(),
            extractor=ShipmentRequestExtractor(rates),
            calculator=QuoteCalculator(rates),
            response_builder=ResponseBuilder(),
        )

    def test_processes_all_pdf_emails(self) -> None:
        results = self.use_case.execute()

        self.assertEqual(len(results), 5)
        self.assertEqual(len(self.publisher.items), 5)

    def test_quotes_email_1_with_urgency(self) -> None:
        result = self.use_case.execute()[0]

        self.assertEqual(result.action, "reply_with_quote")
        self.assertIsNotNone(result.quote)
        self.assertEqual(result.quote.total_clp, 82_800)
        self.assertIn("Ruta: Santiago -> La Serena", result.response or "")
        self.assertIn("$82.800 CLP", result.response or "")

    def test_email_2_is_quote_request_but_requires_missing_data(self) -> None:
        result = self.use_case.execute()[1]

        self.assertEqual(result.action, "reply_request_missing_quote_data")
        self.assertIn("origen y destino", result.missing_fields[0])
        self.assertIsNone(result.quote)
        self.assertNotIn("$", result.response or "")

    def test_quotes_email_3_with_contract_discounts_and_minimum_insurance(self) -> None:
        result = self.use_case.execute()[2]

        self.assertEqual(result.action, "reply_with_quote")
        self.assertIsNotNone(result.quote)
        self.assertEqual(result.quote.base_subtotal_clp, 1_888_000)
        self.assertEqual(result.quote.monthly_discount_clp, 188_800)
        self.assertEqual(result.quote.semester_discount_clp, 84_960)
        self.assertEqual(result.quote.insurance_clp, 15_000)
        self.assertEqual(result.quote.total_clp, 1_629_240)
        self.assertEqual(result.quote.contract_total_clp, 9_775_440)

    def test_non_quote_emails_do_not_get_quote_response(self) -> None:
        results = self.use_case.execute()

        supplier = results[3]
        tracking = results[4]

        self.assertEqual(supplier.action, "archive_supplier_offer_and_notify_admin")
        self.assertIsNone(supplier.response)
        self.assertEqual(tracking.action, "forward_to_operations_tracking_queue")
        self.assertIsNone(tracking.response)

    def test_sends_email_only_for_successful_quotes_when_sender_is_configured(self) -> None:
        rates = default_rate_table()
        sender = MemoryEmailSender()
        use_case = ProcessInboxUseCase(
            repository=JsonEmailRepository(Path("data/emails.json")),
            publisher=self.publisher,
            classifier=RuleBasedEmailClassifier(),
            extractor=ShipmentRequestExtractor(rates),
            calculator=QuoteCalculator(rates),
            response_builder=ResponseBuilder(),
            email_sender=sender,
        )

        use_case.execute()

        self.assertEqual(len(sender.messages), 2)
        self.assertEqual(sender.messages[0]["to"], "psepulveda@ferreteriaeltornillo.cl")
        self.assertEqual(sender.messages[1]["to"], "mgonzalez@supermercaderiascentral.cl")
        self.assertIn("$82.800 CLP", sender.messages[0]["body"])
        self.assertIn("$1.629.240 CLP", sender.messages[1]["body"])

    def test_can_redirect_quote_emails_to_demo_recipient(self) -> None:
        sender = MemoryEmailSender()
        redirect = RecipientOverrideEmailSender(sender, "brunorodolfosanmartinnavarro@gmail.com")

        redirect.send("cliente@example.com", "Cotizacion", "Monto $82.800 CLP")

        self.assertEqual(sender.messages[0]["to"], "brunorodolfosanmartinnavarro@gmail.com")
        self.assertIn("[DEMO para cliente@example.com]", sender.messages[0]["subject"])

    def test_normalizes_gmail_app_password_spaces(self) -> None:
        self.assertEqual(_normalize_smtp_password("abcd efgh ijkl mnop"), "abcdefghijklmnop")


if __name__ == "__main__":
    unittest.main()
