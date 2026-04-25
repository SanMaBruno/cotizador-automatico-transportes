from __future__ import annotations

import os
import unittest

os.environ["COTIZADOR_GOOGLE_SHEETS_WEBHOOK_URL"] = ""
os.environ["COTIZADOR_EMAIL_DRY_RUN"] = "true"
os.environ["COTIZADOR_EMAIL_DRY_RUN_PATH"] = "/tmp/cotizador_api_contract_emails.jsonl"
os.environ["COTIZADOR_EMAIL_OVERRIDE_TO"] = "test@example.com"

from fastapi.testclient import TestClient

from cotizador.presentation.api import app


class ApiContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_integrations_status_exposes_configuration(self) -> None:
        response = self.client.get("/integrations/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("google_sheets", payload)
        self.assertIn("email", payload)
        self.assertIn("warnings", payload)

    def test_process_matches_frontend_contract(self) -> None:
        response = self.client.post("/process")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("integrations", payload)
        self.assertEqual(payload["metrics"]["total"], 5)
        self.assertEqual(payload["metrics"]["cotizaciones_generadas"], 2)
        self.assertEqual(payload["metrics"]["solicitudes_incompletas"], 1)
        self.assertEqual(payload["metrics"]["filtrados_derivados"], 2)
        self.assertEqual(payload["results"][0]["action"], "responder_cotizacion")
        self.assertEqual(payload["results"][0]["quote"]["total_clp"], 82_800)
        self.assertEqual(payload["results"][1]["action"], "solicitar_info")
        self.assertNotIn("quote", payload["results"][1])
        self.assertEqual(payload["results"][2]["quote"]["total_clp"], 1_629_240)
        self.assertEqual(payload["results"][2]["quote"]["total_contrato_clp"], 9_775_440)
        self.assertNotIn("missing_fields", payload["results"][2])

    def test_latest_run_is_available_after_process(self) -> None:
        created = self.client.post("/process").json()

        response = self.client.get("/runs/latest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run_id"], created["run_id"])


if __name__ == "__main__":
    unittest.main()
