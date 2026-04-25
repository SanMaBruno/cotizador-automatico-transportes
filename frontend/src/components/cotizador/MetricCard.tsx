import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone?: "default" | "success" | "warning" | "info";
  hint?: string;
  detail?: string;
}

const toneStyles: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "bg-neutral-soft text-foreground",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  info: "bg-info-soft text-info",
};

export function MetricCard({ label, value, icon: Icon, tone = "default", hint, detail }: MetricCardProps) {
  return (
    <Card className="flex min-h-[126px] items-start gap-4 p-5">
      <div className={cn("rounded-md p-2.5", toneStyles[tone])}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p className="mt-1 text-3xl font-semibold tabular-nums leading-none">{value}</p>
        {detail && <p className="mt-2 text-sm font-medium text-foreground">{detail}</p>}
        {hint && <p className="mt-1.5 text-xs text-muted-foreground">{hint}</p>}
      </div>
    </Card>
  );
}
