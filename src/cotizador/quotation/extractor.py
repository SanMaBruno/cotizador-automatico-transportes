from __future__ import annotations

import re
from typing import List, Optional

from cotizador.config.business_rules import WEEKLY_TO_MONTHLY_CONTRACT_TRIPS_FACTOR
from cotizador.domain.entities import CargoType, Email, ShipmentRequest
from cotizador.domain.rates import RateTable
from cotizador.domain.text import normalize_text


class ShipmentRequestExtractor:
    def __init__(self, rates: RateTable) -> None:
        self._rates = rates

    def extract(self, email: Email) -> ShipmentRequest:
        text = normalize_text(email.body)
        route = self._extract_route(text)
        pallet_count = self._extract_pallet_count(text)
        cargo_type = self._extract_cargo_type(text)
        weekly_trips = self._extract_int_before_phrase(text, "viajes semanales")
        monthly_trips = weekly_trips * WEEKLY_TO_MONTHLY_CONTRACT_TRIPS_FACTOR if weekly_trips else 1

        notes: List[str] = []
        if "cajas" in text and pallet_count is None:
            notes.append("El email informa cajas, pero la tarifa disponible esta definida por pallet.")

        return ShipmentRequest(
            route=route,
            pallet_count=pallet_count,
            cargo_type=cargo_type,
            urgent_less_than_48h="manana" in text or "menos de 48" in text,
            monthly_trips=monthly_trips,
            insurance_requested="seguro" in text,
            declared_value_clp=self._extract_declared_value(text),
            contract_months=self._extract_contract_months(text),
            notes=notes,
        )

    def _extract_route(self, text: str):
        locations = sorted(self._rates.known_locations(), key=len, reverse=True)
        positions = []
        for location in locations:
            normalized = normalize_text(location)
            index = text.find(normalized)
            if index >= 0:
                positions.append((index, location))

        present = [location for _, location in sorted(positions, key=lambda item: item[0])]
        if len(present) < 2:
            return None

        try:
            return self._rates.find_route(present[0], present[1])
        except KeyError:
            return None

    @staticmethod
    def _extract_pallet_count(text: str) -> Optional[int]:
        match = re.search(r"(\d+)\s+pallets?", text)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _extract_cargo_type(text: str) -> Optional[CargoType]:
        if "refrigerad" in text:
            return CargoType.REFRIGERATED
        if "estandar" in text:
            return CargoType.STANDARD
        return None

    @staticmethod
    def _extract_int_before_phrase(text: str, phrase: str) -> Optional[int]:
        match = re.search(rf"(\d+)\s+{re.escape(phrase)}", text)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _extract_contract_months(text: str) -> Optional[int]:
        if "semestral" in text:
            return 6
        match = re.search(r"(\d+)\s+meses", text)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _extract_declared_value(text: str) -> Optional[int]:
        match = re.search(r"valor declarado(?: de)? \$?([\d\.]+)", text)
        if not match:
            return None
        return int(match.group(1).replace(".", ""))

