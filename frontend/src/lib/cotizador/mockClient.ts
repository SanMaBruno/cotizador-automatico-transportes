// Mock client local — implementa la misma API que el backend FastAPI.
import { classify } from "./classifier";
import { SAMPLE_EMAILS } from "./emails";
import { buildMissingInfoReply, buildReply, calcQuote, extract } from "./quote";
import type {
  Email,
  ProcessedEmail,
  ProcessRun,
  ProcessRunMetrics,
} from "./types";

let LATEST_RUN: ProcessRun | null = null;

function processEmail(email: Email): ProcessedEmail {
  const { classification, confidence } = classify(email);

  if (classification === "seguimiento") {
    return {
      email,
      classification,
      confidence,
      action: "derivar_operaciones",
      reason:
        "Consulta de estado de envío. Se deriva al equipo de operaciones con la guía de despacho mencionada.",
    };
  }

  if (classification === "spam_comercial") {
    return {
      email,
      classification,
      confidence,
      action: "archivar",
      reason: "Email comercial no solicitado. Se archiva sin generar respuesta de cotización.",
    };
  }

  if (classification === "otro") {
    return {
      email,
      classification,
      confidence,
      action: "derivar_operaciones",
      reason: "No se pudo clasificar con confianza. Se deriva a revisión humana.",
    };
  }

  // cotización
  const ext = extract(email);
  const quote = calcQuote(ext);
  if (!quote) {
    return {
      email,
      classification,
      confidence,
      action: "solicitar_info",
      missing_fields: ext.missing,
      reply: buildMissingInfoReply(email, ext.missing),
      reason: "Falta información clave para cotizar — no se inventan datos.",
    };
  }

  return {
    email,
    classification,
    confidence,
    action: "responder_cotizacion",
    quote,
    reply: buildReply(email, quote),
  };
}

function buildMetrics(results: ProcessedEmail[]): ProcessRunMetrics {
  return {
    total: results.length,
    cotizaciones_generadas: results.filter((r) => r.action === "responder_cotizacion").length,
    solicitudes_incompletas: results.filter((r) => r.action === "solicitar_info").length,
    filtrados_derivados: results.filter(
      (r) => r.action === "archivar" || r.action === "derivar_operaciones",
    ).length,
  };
}

export const mockClient = {
  async health() {
    return { status: "ok", mode: "mock-local" as const };
  },
  async getEmails(): Promise<Email[]> {
    return SAMPLE_EMAILS;
  },
  async process(): Promise<ProcessRun> {
    // Simula latencia de un flujo real con LLM.
    await new Promise((r) => setTimeout(r, 700));
    const results = SAMPLE_EMAILS.map(processEmail);
    const run: ProcessRun = {
      run_id: `run_${Date.now()}`,
      processed_at: new Date().toISOString(),
      metrics: buildMetrics(results),
      results,
    };
    LATEST_RUN = run;
    try {
      localStorage.setItem("cotizador.latest_run", JSON.stringify(run));
    } catch {
      /* ignore */
    }
    return run;
  },
  async latestRun(): Promise<ProcessRun | null> {
    if (LATEST_RUN) return LATEST_RUN;
    try {
      const raw = localStorage.getItem("cotizador.latest_run");
      if (raw) {
        LATEST_RUN = JSON.parse(raw) as ProcessRun;
        return LATEST_RUN;
      }
    } catch {
      /* ignore */
    }
    return null;
  },
};
