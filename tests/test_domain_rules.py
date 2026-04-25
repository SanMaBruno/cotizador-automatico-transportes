from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cotizador.classifier import RuleBasedEmailClassifier
from cotizador.domain.entities import CargoType, Email, EmailCategory, ShipmentRequest
from cotizador.domain.rates import default_rate_table
from cotizador.infrastructure.publishers import JsonlAuditPublisher
from cotizador.quotation import QuoteCalculator, ShipmentRequestExtractor


class ClassificationRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = RuleBasedEmailClassifier()

    def test_detects_quote_request_with_price_language(self) -> None:
        email = Email("1", "cliente@example.com", "Cuanto me cobran por un flete a La Serena?")

        result = self.classifier.classify(email)

        self.assertTrue(result.is_quote_request)
        self.assertEqual(result.category, EmailCategory.QUOTE)

    def test_detects_supplier_offer_before_quote_like_noise(self) -> None:
        email = Email(
            "1",
            "proveedor@example.com",
            "Queremos ofrecerles una plataforma con planes desde $45.000 y agendar una reunion.",
        )

        result = self.classifier.classify(email)

        self.assertFalse(result.is_quote_request)
        self.assertEqual(result.category, EmailCategory.SUPPLIER_OFFER)

    def test_detects_tracking_request(self) -> None:
        email = Email("1", "cliente@example.com", "Mi pedido con guia de despacho 4782 no llego.")

        result = self.classifier.classify(email)

        self.assertFalse(result.is_quote_request)
        self.assertEqual(result.category, EmailCategory.TRACKING)

    def test_unknown_email_is_not_auto_quoted(self) -> None:
        email = Email("1", "cliente@example.com", "Hola, necesito hablar con ventas.")

        result = self.classifier.classify(email)

        self.assertFalse(result.is_quote_request)
        self.assertEqual(result.category, EmailCategory.OTHER)


class ExtractionRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = ShipmentRequestExtractor(default_rate_table())

    def test_extracts_route_in_textual_order(self) -> None:
        email = Email("1", "cliente@example.com", "Flete desde Santiago a La Serena, 4 pallets estandar.")

        request = self.extractor.extract(email)

        self.assertIsNotNone(request.route)
        self.assertEqual(request.route.origin, "Santiago")
        self.assertEqual(request.route.destination, "La Serena")

    def test_extracts_reverse_route_supported_by_bidirectional_rates(self) -> None:
        email = Email("1", "cliente@example.com", "Cotizar desde La Serena a Santiago, 2 pallets estandar.")

        request = self.extractor.extract(email)

        self.assertIsNotNone(request.route)
        self.assertEqual(request.route.origin, "La Serena")
        self.assertEqual(request.route.destination, "Santiago")

    def test_extracts_monthly_trips_contract_and_refrigerated_cargo(self) -> None:
        email = Email(
            "1",
            "cliente@example.com",
            "Ruta Valparaiso a La Serena, 8 pallets refrigerados, 2 viajes semanales, contrato a 6 meses.",
        )

        request = self.extractor.extract(email)

        self.assertEqual(request.pallet_count, 8)
        self.assertEqual(request.cargo_type, CargoType.REFRIGERATED)
        self.assertEqual(request.monthly_trips, 8)
        self.assertEqual(request.contract_months, 6)


class QuoteCalculatorRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rates = default_rate_table()
        self.calculator = QuoteCalculator(self.rates)

    def test_applies_declared_value_insurance_when_above_minimum(self) -> None:
        route = self.rates.find_route("Santiago", "La Serena")
        request = ShipmentRequest(
            route=route,
            pallet_count=1,
            cargo_type=CargoType.STANDARD,
            insurance_requested=True,
            declared_value_clp=2_000_000,
        )

        quote = self.calculator.calculate(request)

        self.assertEqual(quote.insurance_clp, 40_000)
        self.assertEqual(quote.total_clp, 58_000)

    def test_applies_minimum_insurance_per_trip_when_value_missing(self) -> None:
        route = self.rates.find_route("Valparaiso", "La Serena")
        request = ShipmentRequest(
            route=route,
            pallet_count=8,
            cargo_type=CargoType.REFRIGERATED,
            monthly_trips=8,
            insurance_requested=True,
            declared_value_clp=None,
        )

        quote = self.calculator.calculate(request)

        self.assertEqual(quote.insurance_clp, 120_000)

    def test_applies_monthly_and_semester_discounts_sequentially(self) -> None:
        route = self.rates.find_route("Valparaiso", "La Serena")
        request = ShipmentRequest(
            route=route,
            pallet_count=8,
            cargo_type=CargoType.REFRIGERATED,
            monthly_trips=8,
            contract_months=6,
        )

        quote = self.calculator.calculate(request)

        self.assertEqual(quote.base_subtotal_clp, 1_888_000)
        self.assertEqual(quote.monthly_discount_clp, 188_800)
        self.assertEqual(quote.semester_discount_clp, 84_960)
        self.assertEqual(quote.total_clp, 1_614_240)

    def test_rejects_calculation_when_required_fields_are_missing(self) -> None:
        request = ShipmentRequest(route=None, pallet_count=None, cargo_type=None)

        missing = self.calculator.missing_fields(request)

        self.assertEqual(
            missing,
            [
                "origen y destino dentro de los tramos tarifados",
                "cantidad de pallets o equivalencia exacta de cajas a pallets",
                "tipo de pallet: estandar o refrigerado",
            ],
        )
        with self.assertRaises(ValueError):
            self.calculator.calculate(request)


class PublisherTest(unittest.TestCase):
    def test_jsonl_audit_publisher_writes_processed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "audit.jsonl"
            publisher = JsonlAuditPublisher(output)
            processed = RuleBasedEmailClassifier().classify(
                Email("1", "cliente@example.com", "Necesito cotizar un flete")
            )

            from cotizador.domain.entities import ProcessedEmail

            publisher.publish(
                ProcessedEmail(
                    email=Email("1", "cliente@example.com", "Necesito cotizar un flete"),
                    classification=processed,
                    action="reply_request_missing_quote_data",
                    response="faltan datos",
                )
            )

            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["email"]["id"], "1")
            self.assertEqual(payload["classification"]["category"], "quote_request")


if __name__ == "__main__":
    unittest.main()
