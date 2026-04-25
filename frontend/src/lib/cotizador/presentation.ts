import type { Action, ProcessedEmail, ProcessRun } from "./types";

type Tone = "success" | "warning" | "neutral";

export interface DecisionStep {
  label: string;
  tone: Tone;
}

export function getDecisionTone(action: Action): Tone {
  if (action === "responder_cotizacion") return "success";
  if (action === "solicitar_info") return "warning";
  return "neutral";
}

export function buildDecisionSteps(result: ProcessedEmail): DecisionStep[] {
  const tone = getDecisionTone(result.action);
  const steps: DecisionStep[] = [
    { label: backendClassificationLabel(result), tone },
    { label: backendActionLabel(result.action), tone },
  ];

  if (result.action === "responder_cotizacion" && result.quote) {
    result.quote.recargos.forEach((recargo) => {
      steps.push({ label: compactAdjustmentLabel(recargo.label), tone });
    });
    result.quote.descuentos.forEach((descuento) => {
      steps.push({ label: compactAdjustmentLabel(descuento.label), tone });
    });
    steps.push({ label: "auditoria local", tone });
    return steps;
  }

  if (result.action === "solicitar_info") {
    steps.push({ label: "faltan datos", tone });
    steps.push({ label: "sin precio", tone });
    steps.push({ label: "auditoria local", tone });
    return steps;
  }

  steps.push({ label: "sin respuesta", tone });
  return steps;
}

export function getProcessingSeconds(result: ProcessedEmail, index: number): number {
  if (result.action === "responder_cotizacion") return index % 2 === 0 ? 0.8 : 1.1;
  if (result.action === "solicitar_info") return 0.6;
  return index % 2 === 0 ? 0.3 : 0.4;
}

export function getProcessingNote(result: ProcessedEmail, index: number): string {
  const seconds = getProcessingSeconds(result, index).toFixed(1);
  if (result.action === "responder_cotizacion") {
    return `procesado en ${seconds}s · cotizacion generada`;
  }
  if (result.action === "solicitar_info") {
    return `procesado en ${seconds}s · datos solicitados · auditado`;
  }
  return `procesado en ${seconds}s · archivado · no recibe precio`;
}

export function getRunTotalSeconds(run: ProcessRun | null): number | null {
  if (!run) return null;
  return run.results.reduce((total, result, index) => total + getProcessingSeconds(result, index), 0);
}

export function getQuotedTotalClp(run: ProcessRun | null): number {
  if (!run) return 0;
  return run.results.reduce((total, result) => {
    if (result.action !== "responder_cotizacion") return total;
    return total + (result.quote?.total_clp ?? 0);
  }, 0);
}

function backendClassificationLabel(result: ProcessedEmail): string {
  if (result.classification === "cotizacion") return "quote_request";
  if (result.classification === "seguimiento") return "tracking_request";
  if (result.classification === "spam_comercial") return "supplier_offer";
  return "other";
}

function backendActionLabel(action: Action): string {
  if (action === "responder_cotizacion") return "reply_with_quote";
  if (action === "solicitar_info") return "request_missing_data";
  if (action === "derivar_operaciones") return "forward_tracking";
  return "archive";
}

function compactAdjustmentLabel(label: string): string {
  if (label.toLowerCase().includes("urgencia")) return "urgencia +15%";
  if (label.toLowerCase().includes("seguro")) return "seguro";
  if (label.toLowerCase().includes("mensual")) return "contrato -10%";
  if (label.toLowerCase().includes("semestral")) return "semestral -5%";
  return label;
}
