// Tipos compartidos entre mock local y backend FastAPI.
export type Classification =
  | "cotizacion"
  | "seguimiento"
  | "spam_comercial"
  | "otro";

export type Action =
  | "responder_cotizacion"
  | "solicitar_info"
  | "derivar_operaciones"
  | "archivar";

export interface Email {
  id: string;
  from: string;
  subject?: string;
  body: string;
  received_at?: string;
}

export interface Quote {
  tramo: string;
  pallets: number;
  tipo_pallet: "estandar" | "refrigerado";
  precio_base_clp: number;
  recargos: { label: string; amount_clp: number }[];
  descuentos: { label: string; amount_clp: number }[];
  total_clp: number;
  total_contrato_clp?: number | null;
  viajes_mensuales?: number;
  meses_contrato?: number;
}

export interface ProcessedEmail {
  email: Email;
  classification: Classification;
  confidence: number;
  action: Action;
  quote?: Quote;
  missing_fields?: string[];
  reply?: string;
  reason?: string;
}

export interface ProcessRunMetrics {
  total: number;
  cotizaciones_generadas: number;
  solicitudes_incompletas: number;
  filtrados_derivados: number;
}

export interface ProcessRun {
  run_id: string;
  processed_at: string;
  metrics: ProcessRunMetrics;
  results: ProcessedEmail[];
}
