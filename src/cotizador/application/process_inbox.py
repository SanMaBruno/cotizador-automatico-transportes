from __future__ import annotations

from typing import List, Optional

from cotizador.application.ports import EmailRepository, EmailSender, IntegrationPublisher
from cotizador.domain.entities import Email, EmailCategory, ProcessedEmail
from cotizador.classifier import RuleBasedEmailClassifier
from cotizador.quotation import QuoteCalculator, ShipmentRequestExtractor
from cotizador.responder import ResponseBuilder


class ProcessInboxUseCase:
    def __init__(
        self,
        repository: EmailRepository,
        publisher: IntegrationPublisher,
        classifier: RuleBasedEmailClassifier,
        extractor: ShipmentRequestExtractor,
        calculator: QuoteCalculator,
        response_builder: ResponseBuilder,
        email_sender: Optional[EmailSender] = None,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._classifier = classifier
        self._extractor = extractor
        self._calculator = calculator
        self._response_builder = response_builder
        self._email_sender = email_sender

    def execute(self) -> List[ProcessedEmail]:
        results: List[ProcessedEmail] = []
        for email in self._repository.list_inbox():
            processed = self._process_one(email)
            self._send_quote_reply(processed)
            self._publisher.publish(processed)
            results.append(processed)
        return results

    def _process_one(self, email: Email) -> ProcessedEmail:
        classification = self._classifier.classify(email)
        if not classification.is_quote_request:
            return ProcessedEmail(
                email=email,
                classification=classification,
                action=self._non_quote_action(classification.category),
                response=None,
            )

        request = self._extractor.extract(email)
        missing = self._calculator.missing_fields(request)

        if not self._calculator.can_quote_with_minimums(request):
            return ProcessedEmail(
                email=email,
                classification=classification,
                action="reply_request_missing_quote_data",
                response=self._response_builder.missing_data_response(email, missing),
                missing_fields=missing,
            )

        quote = self._calculator.calculate(request)
        return ProcessedEmail(
            email=email,
            classification=classification,
            action="reply_with_quote",
            response=self._response_builder.quote_response(email, request, quote),
            quote=quote,
            missing_fields=missing,
        )

    @staticmethod
    def _non_quote_action(category: EmailCategory) -> str:
        if category == EmailCategory.TRACKING:
            return "forward_to_operations_tracking_queue"
        if category == EmailCategory.SUPPLIER_OFFER:
            return "archive_supplier_offer_and_notify_admin"
        return "archive_no_quote"

    def _send_quote_reply(self, processed: ProcessedEmail) -> None:
        if self._email_sender is None:
            return
        if processed.action != "reply_with_quote" or processed.response is None:
            return
        self._email_sender.send(
            to=processed.email.sender,
            subject=f"Cotizacion Transportes La Serena - {processed.email.id}",
            body=processed.response,
        )
