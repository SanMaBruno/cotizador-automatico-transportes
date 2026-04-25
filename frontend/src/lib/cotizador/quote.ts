// Extracción de parámetros y cálculo de cotización (espejo del backend).
import type { Email, Quote } from "./types";
import { DESCUENTOS, formatCLP, RECARGOS, TARIFAS, type Tramo } from "./rules";

interface Extracted {
  tramo?: Tramo;
  pallets?: number;
  tipo_pallet?: "estandar" | "refrigerado";
  urgente?: boolean;
  viajes_mensuales?: number;
  meses_contrato?: number;
  pide_seguro?: boolean;
  valor_declarado_clp?: number;
  cajas?: number;
  missing: string[];
}

function detectTramo(text: string): Tramo | undefined {
  const t = text.toLowerCase();
  const has = (a: string, b: string) => t.includes(a) && t.includes(b);
  if (has("santiago", "la serena")) return "Santiago ↔ La Serena";
  if (has("valparaíso", "la serena") || has("valparaiso", "la serena"))
    return "Valparaíso ↔ La Serena";
  if (has("valparaíso", "santiago") || has("valparaiso", "santiago"))
    return "Valparaíso ↔ Santiago";
  if (has("la serena", "antofagasta")) return "La Serena ↔ Antofagasta";
  if (has("santiago", "puerto montt")) return "Santiago ↔ Puerto Montt";
  return undefined;
}

export function extract(email: Email): Extracted {
  const text = `${email.subject ?? ""}\n${email.body}`.toLowerCase();
  const missing: string[] = [];

  const tramo = detectTramo(text);
  if (!tramo) missing.push("Tramo / origen-destino preciso");

  // pallets
  const palletMatch = text.match(/(\d+)\s*pallets?/);
  const pallets = palletMatch ? parseInt(palletMatch[1], 10) : undefined;

  // cajas (sin conversión a pallets — ambiguo, pedimos info)
  const cajasMatch = text.match(/(\d+)\s*cajas/);
  const cajas = cajasMatch ? parseInt(cajasMatch[1], 10) : undefined;

  if (!pallets && !cajas) missing.push("Cantidad de pallets");

  // tipo
  let tipo_pallet: "estandar" | "refrigerado" | undefined;
  if (/refriger/.test(text)) tipo_pallet = "refrigerado";
  else if (/est[áa]ndar/.test(text) || /pallets? est/.test(text))
    tipo_pallet = "estandar";

  if (!tipo_pallet && pallets) missing.push("Tipo de pallet (estándar o refrigerado)");

  // urgencia (<48h)
  const urgente =
    /urgente|mañana|manana|hoy|<\s*48|menos de 48/.test(text);

  // contrato
  const viajesMatch = text.match(/(\d+)\s*viajes?\s*(semanal|semanales|por semana|al mes|mensuales?)/);
  let viajes_mensuales: number | undefined;
  if (viajesMatch) {
    const n = parseInt(viajesMatch[1], 10);
    viajes_mensuales = /seman/.test(viajesMatch[2]) ? n * 4 : n;
  }
  const meses_contrato = /6\s*meses|semestral/.test(text) ? 6 : undefined;
  const pide_seguro = /seguro/.test(text);
  const valorMatch = text.match(/valor declarado(?: de)?\s*\$?([\d.]+)/);
  const valor_declarado_clp = valorMatch ? parseInt(valorMatch[1].replace(/\./g, ""), 10) : undefined;

  return {
    tramo,
    pallets,
    tipo_pallet,
    urgente,
    viajes_mensuales,
    meses_contrato,
    pide_seguro,
    valor_declarado_clp,
    cajas,
    missing,
  };
}

export function calcQuote(e: Extracted): Quote | null {
  if (!e.tramo || !e.pallets || !e.tipo_pallet) return null;

  const tarifaUnit = TARIFAS[e.tramo][e.tipo_pallet];
  const baseUnVuelta = tarifaUnit * e.pallets;
  const viajes = e.viajes_mensuales ?? 1;
  const baseTotal = baseUnVuelta * viajes;

  const recargos: Quote["recargos"] = [];
  const descuentos: Quote["descuentos"] = [];

  let total = baseTotal;

  if (e.urgente) {
    const r = Math.round(baseTotal * RECARGOS.urgencia_pct);
    recargos.push({ label: "Urgencia (<48h) +15%", amount_clp: r });
    total += r;
  }

  if (e.viajes_mensuales && e.viajes_mensuales >= 4) {
    const d = Math.round(total * DESCUENTOS.contrato_mensual_pct);
    descuentos.push({ label: "Contrato mensual fijo −10%", amount_clp: -d });
    total -= d;
    if (e.meses_contrato && e.meses_contrato >= 6) {
      const ds = Math.round(total * DESCUENTOS.contrato_semestral_extra_pct);
      descuentos.push({ label: "Contrato semestral −5% adicional", amount_clp: -ds });
      total -= ds;
    }
  }

  if (e.pide_seguro) {
    const viajesSeguro = viajes || 1;
    const minimo = RECARGOS.seguro_min_clp * viajesSeguro;
    const variable = e.valor_declarado_clp
      ? Math.round(e.valor_declarado_clp * RECARGOS.seguro_pct)
      : 0;
    const seguro = Math.max(variable, minimo);
    recargos.push({ label: "Seguro de carga", amount_clp: seguro });
    total += seguro;
  }

  const totalContrato = e.meses_contrato ? total * e.meses_contrato : undefined;

  return {
    tramo: e.tramo,
    pallets: e.pallets,
    tipo_pallet: e.tipo_pallet,
    precio_base_clp: baseTotal,
    recargos,
    descuentos,
    total_clp: total,
    total_contrato_clp: totalContrato,
    viajes_mensuales: e.viajes_mensuales,
    meses_contrato: e.meses_contrato,
  };
}

export function buildReply(email: Email, quote: Quote): string {
  const partes = [
    `Hola, gracias por escribir a Transportes La Serena.`,
    ``,
    `Cotización para ${quote.tramo} — ${quote.pallets} pallet(s) ${quote.tipo_pallet}${
      quote.viajes_mensuales ? `, ${quote.viajes_mensuales} viajes/mes` : ""
    }:`,
    `• Tarifa base: ${formatCLP(quote.precio_base_clp)}`,
    ...quote.recargos.map((r) => `• ${r.label}: +${formatCLP(r.amount_clp)}`),
    ...quote.descuentos.map((d) => `• ${d.label}: ${formatCLP(d.amount_clp)}`),
    `• ${quote.viajes_mensuales ? "Total mensual" : "Total"}: ${formatCLP(quote.total_clp)} CLP`,
    quote.total_contrato_clp
      ? `• Total contrato ${quote.meses_contrato} meses: ${formatCLP(quote.total_contrato_clp)} CLP`
      : "",
    ``,
    `Precio referencial sujeto a confirmación de fecha y disponibilidad de flota. Quedamos atentos.`,
    `Equipo Comercial — Transportes La Serena`,
  ];
  return partes.join("\n");
}

export function buildMissingInfoReply(email: Email, missing: string[]): string {
  return [
    `Hola, gracias por tu solicitud.`,
    ``,
    `Para entregarte una cotización precisa necesitamos confirmar:`,
    ...missing.map((m) => `• ${m}`),
    ``,
    `Apenas nos confirmes estos datos te enviamos el precio en menos de una hora.`,
    `Equipo Comercial — Transportes La Serena`,
  ].join("\n");
}
