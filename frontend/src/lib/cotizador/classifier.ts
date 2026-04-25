// Clasificador heurístico determinista (mock local).
// El backend Python puede usar LLM; aquí emulamos con reglas robustas.
import type { Classification, Email } from "./types";

const COTIZACION_KW = [
  "cotizar",
  "cotización",
  "cotizacion",
  "cotizarme",
  "cuánto",
  "cuanto",
  "precio",
  "tarifa",
  "flete",
  "viaje",
  "viajes",
  "pallet",
  "pallets",
  "cajas",
  "carga",
];

const SEGUIMIENTO_KW = [
  "guía",
  "guia",
  "despacho",
  "dónde está",
  "donde esta",
  "no tengo noticias",
  "ya debería haber llegado",
  "ya deberia haber llegado",
  "rastrear",
  "estado del envío",
  "estado del envio",
  "seguimiento",
];

const SPAM_KW = [
  "ofrecerles",
  "agendar una reunión",
  "agendar una reunion",
  "descuento exclusivo",
  "plataforma",
  "nuestros planes",
  "saludos cordiales",
  "estimados",
];

function score(text: string, kws: string[]): number {
  const t = text.toLowerCase();
  return kws.reduce((acc, kw) => acc + (t.includes(kw) ? 1 : 0), 0);
}

export function classify(email: Email): {
  classification: Classification;
  confidence: number;
} {
  const text = `${email.subject ?? ""}\n${email.body}`;
  const sSeg = score(text, SEGUIMIENTO_KW);
  const sSpam = score(text, SPAM_KW);
  const sCot = score(text, COTIZACION_KW);

  // Seguimiento gana si menciona guía/despacho explícitamente.
  if (sSeg >= 2 || /gu[ií]a\s+(de\s+)?despacho/i.test(text)) {
    return { classification: "seguimiento", confidence: 0.92 };
  }
  // Spam comercial: ofrecen producto/servicio al cliente.
  if (sSpam >= 3 && sCot <= 1) {
    return { classification: "spam_comercial", confidence: 0.88 };
  }
  if (sCot >= 2) {
    return { classification: "cotizacion", confidence: 0.9 };
  }
  return { classification: "otro", confidence: 0.5 };
}
