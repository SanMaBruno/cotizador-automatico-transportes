from __future__ import annotations

import unittest

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
        self.assertEqual(payload["results"][2]["quote"]["total_clp"], 1_734_240)
        self.assertEqual(payload["results"][2]["quote"]["total_contrato_clp"], 10_405_440)
        self.assertNotIn("missing_fields", payload["results"][2])

    def test_latest_run_is_available_after_process(self) -> None:
        created = self.client.post("/process").json()

        response = self.client.get("/runs/latest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run_id"], created["run_id"])


if __name__ == "__main__":
    unittest.main()
