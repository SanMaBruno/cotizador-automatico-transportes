from __future__ import annotations

from typing import List

from cotizador.config.business_rules import (
    INSURANCE_RATE,
    MINIMUM_INSURANCE_PER_TRIP_CLP,
    MONTHLY_CONTRACT_DISCOUNT_RATE,
    MONTHLY_CONTRACT_MINIMUM_TRIPS,
    SEMESTER_CONTRACT_DISCOUNT_RATE,
    SEMESTER_CONTRACT_MINIMUM_MONTHS,
    URGENCY_SURCHARGE_RATE,
)
from cotizador.domain.entities import QuoteBreakdown, ShipmentRequest
from cotizador.domain.rates import RateTable


class QuoteCalculator:
    def __init__(self, rates: RateTable) -> None:
        self._rates = rates

    def missing_fields(self, request: ShipmentRequest) -> List[str]:
        missing = []
        if request.route is None:
            missing.append("origen y destino dentro de los tramos tarifados")
        if request.pallet_count is None:
            missing.append("cantidad de pallets o equivalencia exacta de cajas a pallets")
        if request.cargo_type is None:
            missing.append("tipo de pallet: estandar o refrigerado")
        return missing

    def can_quote_with_minimums(self, request: ShipmentRequest) -> bool:
        required = [request.route, request.pallet_count, request.cargo_type]
        return all(value is not None for value in required)

    def calculate(self, request: ShipmentRequest) -> QuoteBreakdown:
        if not self.can_quote_with_minimums(request):
            raise ValueError("Cannot calculate quote with missing route, pallets or cargo type.")

        assert request.route is not None
        assert request.pallet_count is not None
        assert request.cargo_type is not None

        per_pallet = self._rates.get_rate(request.route).price_for(request.cargo_type)
        base_subtotal = per_pallet * request.pallet_count * request.monthly_trips
        urgency = round(base_subtotal * URGENCY_SURCHARGE_RATE) if request.urgent_less_than_48h else 0
        discounted_subtotal = base_subtotal + urgency

        monthly_discount = 0
        if request.monthly_trips >= MONTHLY_CONTRACT_MINIMUM_TRIPS:
            monthly_discount = round(discounted_subtotal * MONTHLY_CONTRACT_DISCOUNT_RATE)
            discounted_subtotal -= monthly_discount

        semester_discount = 0
        if request.contract_months is not None and request.contract_months >= SEMESTER_CONTRACT_MINIMUM_MONTHS:
            semester_discount = round(discounted_subtotal * SEMESTER_CONTRACT_DISCOUNT_RATE)
            discounted_subtotal -= semester_discount

        assumptions: List[str] = list(request.notes)
        insurance = self._calculate_insurance(request)
        if request.insurance_requested and request.declared_value_clp is None:
            assumptions.append(
                "Seguro calculado con minimo de 15.000 CLP por viaje por no indicar valor declarado."
            )
        if request.monthly_trips > 1:
            assumptions.append(f"Precio mensual calculado con {request.monthly_trips} viajes al mes.")

        total = discounted_subtotal + insurance
        contract_total = total * request.contract_months if request.contract_months else None

        return QuoteBreakdown(
            base_subtotal_clp=base_subtotal,
            urgency_surcharge_clp=urgency,
            monthly_discount_clp=monthly_discount,
            semester_discount_clp=semester_discount,
            insurance_clp=insurance,
            total_clp=total,
            contract_total_clp=contract_total,
            assumptions=assumptions,
        )

    def _calculate_insurance(self, request: ShipmentRequest) -> int:
        if not request.insurance_requested:
            return 0

        minimum = MINIMUM_INSURANCE_PER_TRIP_CLP * max(request.monthly_trips, 1)
        if request.declared_value_clp is None:
            return minimum

        variable = round(request.declared_value_clp * INSURANCE_RATE)
        return max(variable, minimum)
