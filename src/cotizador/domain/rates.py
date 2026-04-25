from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from cotizador.domain.entities import CargoType, Route


@dataclass(frozen=True)
class Rate:
    route: Route
    standard_pallet_clp: int
    refrigerated_pallet_clp: int

    def price_for(self, cargo_type: CargoType) -> int:
        if cargo_type == CargoType.STANDARD:
            return self.standard_pallet_clp
        return self.refrigerated_pallet_clp


class RateTable:
    def __init__(self, rates: Iterable[Rate]) -> None:
        self._rates: Dict[Tuple[str, str], Rate] = {}
        for rate in rates:
            self._rates[self._key(rate.route.origin, rate.route.destination)] = rate
            reverse = Route(rate.route.destination, rate.route.origin, rate.route.distance_km)
            self._rates[self._key(reverse.origin, reverse.destination)] = Rate(
                reverse,
                rate.standard_pallet_clp,
                rate.refrigerated_pallet_clp,
            )

    def find_route(self, origin: str, destination: str) -> Route:
        return self._rates[self._key(origin, destination)].route

    def get_rate(self, route: Route) -> Rate:
        return self._rates[self._key(route.origin, route.destination)]

    def known_locations(self) -> set[str]:
        locations = set()
        for rate in self._rates.values():
            locations.add(rate.route.origin)
            locations.add(rate.route.destination)
        return locations

    @staticmethod
    def _key(origin: str, destination: str) -> Tuple[str, str]:
        return (origin.lower(), destination.lower())


def default_rate_table() -> RateTable:
    return RateTable(
        [
            Rate(Route("Santiago", "La Serena", 470), 18_000, 28_000),
            Rate(Route("Valparaiso", "La Serena", 500), 19_500, 29_500),
            Rate(Route("Valparaiso", "Santiago", 120), 8_000, 12_000),
            Rate(Route("La Serena", "Antofagasta", 880), 32_000, 48_000),
            Rate(Route("Santiago", "Puerto Montt", 1030), 38_000, 55_000),
        ]
    )
