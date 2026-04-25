// Reglas de negocio: tarifas, recargos y descuentos del brief.
// Espejo de la lógica del backend Python — única fuente de verdad para el mock.

export type Tramo =
  | "Santiago ↔ La Serena"
  | "Valparaíso ↔ La Serena"
  | "Valparaíso ↔ Santiago"
  | "La Serena ↔ Antofagasta"
  | "Santiago ↔ Puerto Montt";

export const TARIFAS: Record<Tramo, { estandar: number; refrigerado: number }> = {
  "Santiago ↔ La Serena": { estandar: 18000, refrigerado: 28000 },
  "Valparaíso ↔ La Serena": { estandar: 19500, refrigerado: 29500 },
  "Valparaíso ↔ Santiago": { estandar: 8000, refrigerado: 12000 },
  "La Serena ↔ Antofagasta": { estandar: 32000, refrigerado: 48000 },
  "Santiago ↔ Puerto Montt": { estandar: 38000, refrigerado: 55000 },
};

export const RECARGOS = {
  urgencia_pct: 0.15, // <48h
  seguro_pct: 0.02, // 2% valor declarado, mínimo 15.000
  seguro_min_clp: 15000,
};

export const DESCUENTOS = {
  contrato_mensual_pct: 0.1, // ≥4 viajes/mes
  contrato_semestral_extra_pct: 0.05, // adicional sobre el mensual
};

export function formatCLP(amount: number): string {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(amount);
}
