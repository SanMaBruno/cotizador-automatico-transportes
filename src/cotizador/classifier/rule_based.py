from __future__ import annotations

from cotizador.domain.entities import Classification, Email, EmailCategory
from cotizador.domain.text import normalize_text


class RuleBasedEmailClassifier:
    def classify(self, email: Email) -> Classification:
        text = normalize_text(email.body)

        if any(token in text for token in ["guia de despacho", "donde esta", "consultar donde esta", "pedido"]):
            return Classification(
                category=EmailCategory.TRACKING,
                is_quote_request=False,
                reason="Consulta por estado de carga o guia de despacho, no solicita precio.",
                confidence=0.98,
            )

        if any(token in text for token in ["ofrecerles", "plataforma", "planes desde", "agendar una reunion"]):
            return Classification(
                category=EmailCategory.SUPPLIER_OFFER,
                is_quote_request=False,
                reason="Email comercial entrante ofreciendo un servicio a la empresa.",
                confidence=0.98,
            )

        if any(token in text for token in ["cotizar", "cotizarme", "cuanto me cobran", "flete"]):
            return Classification(
                category=EmailCategory.QUOTE,
                is_quote_request=True,
                reason="Solicita precio o cotizacion de transporte.",
                confidence=0.95,
            )

        return Classification(
            category=EmailCategory.OTHER,
            is_quote_request=False,
            reason="No contiene una solicitud clara de cotizacion.",
            confidence=0.60,
        )

