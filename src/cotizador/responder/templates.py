from __future__ import annotations

from typing import List

from cotizador.domain.entities import Email, QuoteBreakdown, ShipmentRequest
from cotizador.domain.money import format_clp


class ResponseBuilder:
    def missing_data_response(self, email: Email, missing: List[str]) -> str:
        fields = ", ".join(missing)
        return (
            "Hola,\n\n"
            "Gracias por escribir a Transportes La Serena. Podemos cotizar el traslado, "
            "pero para entregar un precio correcto nos falta la siguiente informacion: "
            f"{fields}.\n\n"
            "Apenas nos confirmes esos datos, te enviamos la cotizacion.\n\n"
            "Saludos,\n"
            "Equipo Transportes La Serena"
        )

    def quote_response(self, email: Email, request: ShipmentRequest, quote: QuoteBreakdown) -> str:
        assert request.route is not None
        assert request.pallet_count is not None
        assert request.cargo_type is not None

        cargo_label = "refrigerado" if request.cargo_type.value == "refrigerated" else "estandar"
        lines = [
            "Hola,",
            "",
            "Gracias por escribir a Transportes La Serena. Te compartimos la cotizacion solicitada:",
            "",
            f"Ruta: {request.route.label} (~{request.route.distance_km} km)",
            f"Carga: {request.pallet_count} pallets {cargo_label}",
            f"Viajes considerados: {request.monthly_trips}",
            f"Subtotal base: {format_clp(quote.base_subtotal_clp)}",
        ]

        if quote.urgency_surcharge_clp:
            lines.append(f"Recargo por urgencia (<48h): {format_clp(quote.urgency_surcharge_clp)}")
        if quote.monthly_discount_clp:
            lines.append(f"Descuento contrato mensual fijo: -{format_clp(quote.monthly_discount_clp)}")
        if quote.semester_discount_clp:
            lines.append(f"Descuento contrato semestral: -{format_clp(quote.semester_discount_clp)}")
        if quote.insurance_clp:
            lines.append(f"Seguro de carga: {format_clp(quote.insurance_clp)}")

        total_label = "Total mensual estimado" if request.monthly_trips > 1 else "Total estimado"
        lines.extend(["", f"{total_label}: {format_clp(quote.total_clp)}"])

        if quote.contract_total_clp:
            lines.append(f"Total estimado contrato {request.contract_months} meses: {format_clp(quote.contract_total_clp)}")

        if quote.assumptions:
            lines.append("")
            lines.append("Consideraciones:")
            lines.extend(f"- {assumption}" for assumption in quote.assumptions)

        lines.extend(
            [
                "",
                "La cotizacion queda sujeta a confirmacion de disponibilidad operativa.",
                "",
                "Saludos,",
                "Equipo Transportes La Serena",
            ]
        )
        return "\n".join(lines)

