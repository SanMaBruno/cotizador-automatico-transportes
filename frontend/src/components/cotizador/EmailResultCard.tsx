import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ACTION_TONE, ActionBadge, ClassificationBadge } from "./StatusBadges";
import { cn } from "@/lib/utils";
import { formatCLP } from "@/lib/cotizador/rules";
import type { ProcessedEmail } from "@/lib/cotizador/types";
import { buildDecisionSteps, getDecisionTone, getProcessingNote } from "@/lib/cotizador/presentation";
import { AlertTriangle, Check, Clock3, Copy, Mail, MapPin, Package } from "lucide-react";

export function EmailResultCard({ result, index }: { result: ProcessedEmail; index: number }) {
  const [copied, setCopied] = useState(false);
  const tone = ACTION_TONE[result.action];
  const decisionTone = getDecisionTone(result.action);
  const decisionSteps = buildDecisionSteps(result);

  async function copyReply() {
    if (!result.reply) return;
    await navigator.clipboard.writeText(result.reply);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Card className={cn("overflow-hidden border-l-4 transition-shadow hover:shadow-lg", "border-l-transparent")}
      style={{ borderLeftColor: `hsl(var(--${
        result.action === "responder_cotizacion" ? "success" :
        result.action === "solicitar_info" ? "warning" :
        result.action === "derivar_operaciones" ? "info" : "border"
      }))` }}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-mono">{result.email.id}</span>
              <span>·</span>
              <Mail className="h-3.5 w-3.5" />
              <span className="truncate">{result.email.from}</span>
            </div>
            {result.email.subject && (
              <h3 className="mt-1 text-base font-semibold text-foreground">
                {result.email.subject}
              </h3>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <ClassificationBadge value={result.classification} />
            <ActionBadge value={result.action} />
          </div>
        </div>

        <div className="mt-4 overflow-x-auto rounded-md border border-border bg-muted/25 px-3 py-2">
          <div className="flex min-w-max items-center gap-2">
            {decisionSteps.map((step, stepIndex) => (
              <DecisionStepPill
                key={`${step.label}-${stepIndex}`}
                label={step.label}
                tone={step.tone}
                showArrow={stepIndex < decisionSteps.length - 1}
              />
            ))}
          </div>
        </div>

        <div className="mt-3 rounded-md bg-muted/60 p-3 text-sm text-foreground/80">
          {result.email.body}
        </div>

        {/* Quote breakdown */}
        {result.quote && (
          <div className="mt-4 rounded-md border border-border bg-card">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 text-xs text-muted-foreground border-b border-border">
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" /> {result.quote.tramo}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Package className="h-3.5 w-3.5" />
                {result.quote.pallets} pallet(s) {result.quote.tipo_pallet}
              </span>
              {result.quote.viajes_mensuales && (
                <span>· {result.quote.viajes_mensuales} viajes/mes</span>
              )}
            </div>
            <div className="px-4 py-3 space-y-1 text-sm">
              <Row label="Tarifa base" value={formatCLP(result.quote.precio_base_clp)} />
              {result.quote.recargos.map((r) => (
                <Row key={r.label} label={r.label} value={`+${formatCLP(r.amount_clp)}`} tone="warning" />
              ))}
              {result.quote.descuentos.map((d) => (
                <Row key={d.label} label={d.label} value={formatCLP(d.amount_clp)} tone="success" />
              ))}
              <Separator className="my-2" />
              <Row
                label="Total cotizado"
                value={formatCLP(result.quote.total_clp)}
                bold
              />
              {result.quote.total_contrato_clp && (
                <Row
                  label={`Total contrato ${result.quote.meses_contrato} meses`}
                  value={formatCLP(result.quote.total_contrato_clp)}
                  bold
                />
              )}
            </div>
          </div>
        )}

        {/* Missing fields */}
        {result.missing_fields && result.missing_fields.length > 0 && (
          <div className="mt-4 rounded-md border border-warning/30 bg-warning-soft p-3">
            <div className="flex items-center gap-2 text-sm font-medium text-warning">
              <AlertTriangle className="h-4 w-4" />
              Información faltante
            </div>
            <ul className="mt-2 space-y-1 text-sm text-foreground/80 list-disc pl-5">
              {result.missing_fields.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Reply / reason */}
        {result.reply && (
          <details className="mt-4 group">
            <summary className="flex cursor-pointer items-center justify-between gap-3 text-sm font-medium text-foreground/80 hover:text-foreground select-none">
              <span>Ver respuesta generada</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 gap-1.5"
                onClick={(event) => {
                  event.preventDefault();
                  copyReply();
                }}
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copiada" : "Copiar"}
              </Button>
            </summary>
            <pre className="mt-2 whitespace-pre-wrap rounded-md bg-primary/5 p-3 text-sm text-foreground/90 font-sans">
              {result.reply}
            </pre>
          </details>
        )}
        {result.reason && !result.reply && (
          <p className={cn("mt-3 text-sm", tone.text)}>{result.reason}</p>
        )}

        <div
          className={cn(
            "mt-4 flex items-center gap-1.5 border-t border-border pt-3 text-xs",
            decisionTone === "success" && "text-success",
            decisionTone === "warning" && "text-warning",
            decisionTone === "neutral" && "text-muted-foreground",
          )}
        >
          <Clock3 className="h-3.5 w-3.5" />
          <span>{getProcessingNote(result, index)}</span>
        </div>
      </div>
    </Card>
  );
}

function DecisionStepPill({
  label,
  tone,
  showArrow,
}: {
  label: string;
  tone: "success" | "warning" | "neutral";
  showArrow: boolean;
}) {
  return (
    <>
      <span
        className={cn(
          "inline-flex h-7 items-center rounded-md border px-2.5 text-xs font-semibold",
          tone === "success" && "border-[#1D9E75]/25 bg-[#1D9E75]/10 text-[#137A5A]",
          tone === "warning" && "border-warning/25 bg-warning-soft text-warning",
          tone === "neutral" && "border-border bg-neutral-soft text-muted-foreground",
        )}
      >
        {label}
      </span>
      {showArrow && <span className="text-muted-foreground">→</span>}
    </>
  );
}

function Row({
  label,
  value,
  bold,
  tone,
}: {
  label: string;
  value: string;
  bold?: boolean;
  tone?: "success" | "warning";
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className={cn("text-muted-foreground", bold && "text-foreground font-semibold")}>
        {label}
      </span>
      <span
        className={cn(
          "tabular-nums",
          bold && "text-base font-semibold",
          tone === "success" && "text-success",
          tone === "warning" && "text-warning",
        )}
      >
        {value}
      </span>
    </div>
  );
}
