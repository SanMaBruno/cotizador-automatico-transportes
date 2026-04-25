import { cn } from "@/lib/utils";
import type { Action, Classification } from "@/lib/cotizador/types";

const CLASSIFICATION_LABEL: Record<Classification, string> = {
  cotizacion: "Cotización",
  seguimiento: "Seguimiento",
  spam_comercial: "Spam comercial",
  otro: "Sin clasificar",
};

const ACTION_LABEL: Record<Action, string> = {
  responder_cotizacion: "Cotización generada",
  solicitar_info: "Solicitud incompleta",
  derivar_operaciones: "Derivado a operaciones",
  archivar: "Archivado",
};

const ACTION_TONE: Record<
  Action,
  { dot: string; bg: string; text: string; ring: string }
> = {
  responder_cotizacion: {
    dot: "bg-success",
    bg: "bg-success-soft",
    text: "text-success",
    ring: "ring-success/20",
  },
  solicitar_info: {
    dot: "bg-warning",
    bg: "bg-warning-soft",
    text: "text-warning",
    ring: "ring-warning/20",
  },
  derivar_operaciones: {
    dot: "bg-info",
    bg: "bg-info-soft",
    text: "text-info",
    ring: "ring-info/20",
  },
  archivar: {
    dot: "bg-muted-foreground",
    bg: "bg-neutral-soft",
    text: "text-muted-foreground",
    ring: "ring-border",
  },
};

export function ClassificationBadge({ value }: { value: Classification }) {
  return (
    <span className="inline-flex items-center rounded-md border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
      {CLASSIFICATION_LABEL[value]}
    </span>
  );
}

export function ActionBadge({ value }: { value: Action }) {
  const tone = ACTION_TONE[value];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        tone.bg,
        tone.text,
        tone.ring,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", tone.dot)} />
      {ACTION_LABEL[value]}
    </span>
  );
}

export { ACTION_TONE };
