import { describe, expect, it } from "vitest";
import { SAMPLE_EMAILS } from "@/lib/cotizador/emails";
import { calcQuote, extract } from "@/lib/cotizador/quote";
import { buildDecisionSteps, getProcessingNote, getQuotedTotalClp } from "@/lib/cotizador/presentation";
import { mockClient } from "@/lib/cotizador/mockClient";

describe("cotizador frontend mock", () => {
  it("quotes email 1 with urgency surcharge", () => {
    const quote = calcQuote(extract(SAMPLE_EMAILS[0]));

    expect(quote?.precio_base_clp).toBe(72_000);
    expect(quote?.total_clp).toBe(82_800);
  });

  it("quotes email 3 with discounts, minimum insurance and contract total", () => {
    const quote = calcQuote(extract(SAMPLE_EMAILS[2]));

    expect(quote?.precio_base_clp).toBe(1_888_000);
    expect(quote?.total_clp).toBe(1_629_240);
    expect(quote?.total_contrato_clp).toBe(9_775_440);
  });

  it("does not invent a quote for ambiguous email 2", () => {
    const extracted = extract(SAMPLE_EMAILS[1]);

    expect(calcQuote(extracted)).toBeNull();
    expect(extracted.missing).toContain("Tramo / origen-destino preciso");
  });

  it("builds decision chains and run totals for the dashboard", async () => {
    const run = await mockClient.process();

    expect(getQuotedTotalClp(run)).toBe(1_712_040);
    expect(buildDecisionSteps(run.results[0]).map((step) => step.label)).toEqual([
      "quote_request",
      "reply_with_quote",
      "urgencia +15%",
      "auditoria local",
    ]);
    expect(buildDecisionSteps(run.results[3]).map((step) => step.label)).toEqual([
      "supplier_offer",
      "archive",
      "sin respuesta",
    ]);
    expect(getProcessingNote(run.results[4], 4)).toContain("no recibe precio");
  });
});
