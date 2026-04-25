from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class CargoType(str, Enum):
    STANDARD = "standard"
    REFRIGERATED = "refrigerated"


class EmailCategory(str, Enum):
    QUOTE = "quote_request"
    SUPPLIER_OFFER = "supplier_offer"
    TRACKING = "tracking_request"
    OTHER = "other"


@dataclass(frozen=True)
class Email:
    id: str
    sender: str
    body: str


@dataclass(frozen=True)
class Classification:
    category: EmailCategory
    is_quote_request: bool
    reason: str
    confidence: float


@dataclass(frozen=True)
class Route:
    origin: str
    destination: str
    distance_km: int

    @property
    def label(self) -> str:
        return f"{self.origin} -> {self.destination}"


@dataclass(frozen=True)
class ShipmentRequest:
    route: Optional[Route]
    pallet_count: Optional[int]
    cargo_type: Optional[CargoType]
    urgent_less_than_48h: bool = False
    monthly_trips: int = 1
    insurance_requested: bool = False
    declared_value_clp: Optional[int] = None
    contract_months: Optional[int] = None
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class QuoteBreakdown:
    base_subtotal_clp: int
    urgency_surcharge_clp: int
    monthly_discount_clp: int
    semester_discount_clp: int
    insurance_clp: int
    total_clp: int
    assumptions: List[str]
    contract_total_clp: Optional[int] = None


@dataclass(frozen=True)
class ProcessedEmail:
    email: Email
    classification: Classification
    action: str
    response: Optional[str]
    quote: Optional[QuoteBreakdown] = None
    missing_fields: List[str] = field(default_factory=list)
