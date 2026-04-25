import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import type { Action, IntegrationStatus, ProcessRun } from "@/lib/cotizador/types";
import { formatCLP } from "@/lib/cotizador/rules";
import { getQuotedTotalClp, getRunTotalSeconds } from "@/lib/cotizador/presentation";
import { MetricCard } from "@/components/cotizador/MetricCard";
import { EmailResultCard } from "@/components/cotizador/EmailResultCard";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Inbox,
  Loader2,
  Play,
  AlertTriangle,
  Archive,
  ArrowRight,
  Clock3,
  ExternalLink,
  FileSpreadsheet,
  MailCheck,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type ResultFilter = "todos" | "cotizados" | "incompletos" | "filtrados";

const Index = () => {
  const [health, setHealth] = useState<{ status: string; mode?: string } | null>(null);
  const [run, setRun] = useState<ProcessRun | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [flowProgress, setFlowProgress] = useState(0);
  const [filter, setFilter] = useState<ResultFilter>("todos");

  useEffect(() => {
    document.title = "Mini-cotizador · Transportes La Serena";
    api
      .health()
      .then(setHealth)
      .catch(() => setHealth({ status: "down" }));
    api
      .integrationsStatus()
      .then(setIntegrations)
      .catch(() => setIntegrations(null));
    api.latestRun().then((r) => r && setRun(r));
  }, []);

  async function handleProcess() {
    setLoading(true);
    setFlowProgress(1);
    const progressTimer = window.setInterval(() => {
      setFlowProgress((current) => Math.min(current + 1, 4));
    }, 240);
    try {
      const r = await api.process();
      setRun(r);
      if (r.integrations) {
        setIntegrations(r.integrations);
      }
      setFlowProgress(5);
      toast({
        title: "Procesamiento completado",
        description: `${r.metrics.total} emails procesados — ${r.metrics.cotizaciones_generadas} cotizaciones generadas.`,
      });
    } catch (e) {
      toast({
        title: "Error procesando emails",
        description: e instanceof Error ? e.message : "Error desconocido",
        variant: "destructive",
      });
    } finally {
      window.clearInterval(progressTimer);
      setLoading(false);
    }
  }

  const m = run?.metrics;
  const healthy = health?.status === "ok";
  const quotedTotal = getQuotedTotalClp(run);
  const runTotalSeconds = getRunTotalSeconds(run);
  const visibleResults = run?.results.filter((result) => matchesFilter(result.action, filter)) ?? [];
  const effectiveIntegrations = run?.integrations ?? integrations;
  const sheetsConfigured = Boolean(effectiveIntegrations?.google_sheets.configured);
  const emailEnabled = Boolean(effectiveIntegrations?.email.enabled);
  const integrationWarnings = effectiveIntegrations?.warnings ?? [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-card/95 backdrop-blur">
        <div className="container flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-lg border border-border bg-white">
              <img
                src="/brand/jaiar-labs-logo.png"
                alt="Jaiar Labs"
                className="h-10 w-10 object-contain"
              />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                JAIAR LABS · AI Consulting
              </p>
              <h1 className="text-xl font-semibold leading-tight">
                Centro de automatización comercial
              </h1>
              <p className="text-sm text-muted-foreground">
                Demo end-to-end para Transportes La Serena: clasifica, cotiza y registra.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  healthy ? "bg-success" : "bg-destructive"
                }`}
              />
              <span className="font-medium">
                {healthy ? "Backend OK" : "Backend caído"}
              </span>
              <span className="text-muted-foreground hidden sm:inline">
                · {api.mode === "remote" ? api.baseUrl : "mock local"}
              </span>
            </div>
            <Button onClick={handleProcess} disabled={loading} size="lg">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Procesando…
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" /> Procesar emails
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-8 space-y-8">
        <section className="grid gap-4 lg:grid-cols-[1.4fr_0.9fr]">
          <Card className="overflow-hidden border-border bg-card shadow-sm">
            <div className="flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-md bg-[#1D9E75]/10 px-2.5 py-1 text-xs font-medium text-[#137A5A] dark:text-[#7EE0BE]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Operación comercial asistida por IA
                </div>
                <h2 className="mt-4 text-2xl font-semibold tracking-normal">
                  De email desordenado a cotización auditada en segundos.
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  El backend calcula precios con Python, no con IA. El frontend muestra cada
                  decisión y permite comprobar que los emails no cotizables no reciben precio.
                </p>
              </div>
              <Button onClick={handleProcess} disabled={loading} size="lg" className="h-12 px-5">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Procesando flujo
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" /> Procesar 5 emails
                  </>
                )}
              </Button>
            </div>
            <div className="grid border-t border-border bg-muted/35 sm:grid-cols-3">
              <Step icon={Inbox} title="1. Lee emails" text="Carga los 5 casos reales del PDF." />
              <Step icon={ShieldCheck} title="2. Clasifica antes" text="Cotiza, pide datos, archiva o deriva." />
              <Step icon={MailCheck} title="3. Responde seguro" text="Dry-run o SMTP con redirección para demo." />
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-info-soft p-2 text-info">
                <ExternalLink className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-semibold">Integración externa</h2>
                <p className="text-xs text-muted-foreground">
                  Backend listo para Google Sheets o cualquier webhook.
                </p>
              </div>
            </div>
            <div className="mt-4 space-y-3 text-sm">
              <IntegrationRow label="API" value={api.mode === "remote" ? api.baseUrl : "mock local"} ok={healthy} />
              <IntegrationRow label="Auditoría" value="out/api_processed_emails.jsonl" ok />
              <IntegrationRow
                label="Google Sheets"
                value={effectiveIntegrations?.google_sheets.target ?? "No configurado"}
                ok={sheetsConfigured}
              />
              <IntegrationRow
                label="Correo demo"
                value={emailTargetLabel(effectiveIntegrations)}
                ok={emailEnabled}
              />
            </div>
            {integrationWarnings.length > 0 ? (
              <div className="mt-4 rounded-md border border-warning/30 bg-warning-soft p-3 text-xs text-warning">
                <div className="mb-1 flex items-center gap-1.5 font-semibold">
                  <AlertCircle className="h-3.5 w-3.5" />
                  Integración incompleta
                </div>
                {integrationWarnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            ) : (
              <p className="mt-4 rounded-md bg-muted p-3 text-xs text-muted-foreground">
                Google Sheets y email están configurados en el backend activo.
              </p>
            )}
          </Card>
        </section>

        <section aria-labelledby="metrics-title">
          <h2 id="metrics-title" className="sr-only">
            Métricas del último run
          </h2>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Emails procesados"
              value={m?.total ?? "—"}
              icon={Inbox}
              tone="default"
              detail={runTotalSeconds ? `${runTotalSeconds.toFixed(1)}s total` : undefined}
              hint={run ? `Run ${run.run_id.slice(-6)}` : "Esperando ejecución"}
            />
            <MetricCard
              label="Cotizaciones generadas"
              value={m?.cotizaciones_generadas ?? "—"}
              icon={CheckCircle2}
              tone="success"
              detail={run ? `${formatCLP(quotedTotal)} cotizado` : undefined}
              hint="Respuesta con tarifa calculada"
            />
            <MetricCard
              label="Solicitudes incompletas"
              value={m?.solicitudes_incompletas ?? "—"}
              icon={AlertTriangle}
              tone="warning"
              hint="Sin precio inventado"
            />
            <MetricCard
              label="Filtrados / derivados"
              value={m?.filtrados_derivados ?? "—"}
              icon={Archive}
              tone="info"
              hint="No reciben cotización"
            />
          </div>
        </section>

        <section aria-labelledby="results-title" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 id="results-title" className="text-base font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              Resultados del procesamiento
            </h2>
            {run && (
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <Clock3 className="h-3.5 w-3.5" />
                {new Date(run.processed_at).toLocaleString("es-CL")}
              </span>
            )}
          </div>

          <FlowProgress completedSteps={flowProgress} isRunning={loading} hasRun={Boolean(run)} />

          {!run ? (
            <Card className="p-10 text-center">
              <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium">Aún no hay resultados</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Presiona <strong>Procesar emails</strong> para ejecutar el flujo sobre los 5 emails de la bandeja.
              </p>
            </Card>
          ) : (
            <div className="grid gap-4">
              <ResultFilters
                active={filter}
                onChange={setFilter}
                counts={{
                  todos: run.results.length,
                  cotizados: run.results.filter((result) => result.action === "responder_cotizacion").length,
                  incompletos: run.results.filter((result) => result.action === "solicitar_info").length,
                  filtrados: run.results.filter((result) => isFilteredAction(result.action)).length,
                }}
              />
              <div className="grid gap-3 rounded-lg border border-border bg-card p-4 text-sm md:grid-cols-3">
                <SummaryItem title="Se cotiza" value="Emails 1 y 3" />
                <SummaryItem title="Se pide información" value="Email 2" />
                <SummaryItem title="Se filtra sin precio" value="Emails 4 y 5" />
              </div>
              {visibleResults.map((r, index) => (
                <EmailResultCard key={r.email.id} result={r} index={index} />
              ))}
            </div>
          )}
        </section>

        <footer className="pt-6 pb-2 text-xs text-muted-foreground">
          JAIAR LABS AI Consulting · Tarifas según brief · Cálculo oficial en backend FastAPI.
        </footer>
      </main>
    </div>
  );
};

function Step({
  icon: Icon,
  title,
  text,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
}) {
  return (
    <div className="flex gap-3 border-border p-4 sm:border-r last:border-r-0">
      <div className="mt-0.5 rounded-md bg-card p-2 text-primary shadow-sm">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="text-xs text-muted-foreground">{text}</p>
      </div>
    </div>
  );
}

function emailTargetLabel(status: IntegrationStatus | null | undefined): string {
  if (!status?.email.enabled) return "No configurado";
  if (status.email.dry_run) return `Dry-run ${status.email.override_to ?? ""}`.trim();
  return status.email.override_to ?? status.email.from ?? "SMTP configurado";
}

function matchesFilter(action: Action, filter: ResultFilter): boolean {
  if (filter === "todos") return true;
  if (filter === "cotizados") return action === "responder_cotizacion";
  if (filter === "incompletos") return action === "solicitar_info";
  return isFilteredAction(action);
}

function isFilteredAction(action: Action): boolean {
  return action === "archivar" || action === "derivar_operaciones";
}

function ResultFilters({
  active,
  onChange,
  counts,
}: {
  active: ResultFilter;
  onChange: (filter: ResultFilter) => void;
  counts: Record<ResultFilter, number>;
}) {
  const filters: { id: ResultFilter; label: string }[] = [
    { id: "todos", label: "Todos" },
    { id: "cotizados", label: "Cotizados" },
    { id: "incompletos", label: "Incompletos" },
    { id: "filtrados", label: "Filtrados" },
  ];

  return (
    <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-card p-2">
      {filters.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChange(item.id)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            active === item.id
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          {item.label}
          <span className="ml-2 rounded bg-background/30 px-1.5 py-0.5 text-xs">{counts[item.id]}</span>
        </button>
      ))}
    </div>
  );
}

const FLOW_STEPS = ["Leer emails", "Clasificar", "Calcular tarifa", "Redactar", "Registrar Sheets"];

function FlowProgress({
  completedSteps,
  isRunning,
  hasRun,
}: {
  completedSteps: number;
  isRunning: boolean;
  hasRun: boolean;
}) {
  const visibleSteps = hasRun && !isRunning ? FLOW_STEPS.length : completedSteps;
  return (
    <Card className="overflow-hidden border-border bg-card">
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Flujo de automatización</p>
            <p className="text-xs text-muted-foreground">
              {isRunning ? "Procesando bandeja de entrada" : hasRun ? "Última ejecución completada" : "Esperando ejecución"}
            </p>
          </div>
          <span className="rounded-md bg-neutral-soft px-2.5 py-1 text-xs font-medium text-muted-foreground">
            {Math.min(visibleSteps, FLOW_STEPS.length)}/{FLOW_STEPS.length}
          </span>
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          {FLOW_STEPS.map((step, index) => {
            const stepNumber = index + 1;
            const done = visibleSteps >= stepNumber;
            const active = isRunning && visibleSteps === stepNumber;
            return (
              <div key={step} className="flex items-center gap-2 md:block">
                <div className="flex items-center md:w-full">
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-colors ${
                      done
                        ? "border-[#1D9E75] bg-[#1D9E75] text-white"
                        : active
                          ? "border-warning bg-warning-soft text-warning"
                          : "border-border bg-muted text-muted-foreground"
                    }`}
                  >
                    {done ? "✓" : stepNumber}
                  </span>
                  {index < FLOW_STEPS.length - 1 && (
                    <span
                      className={`hidden h-0.5 flex-1 md:block ${
                        visibleSteps > stepNumber ? "bg-[#1D9E75]" : "bg-border"
                      }`}
                    />
                  )}
                </div>
                <p className={`text-xs font-medium md:mt-2 ${done ? "text-[#137A5A]" : "text-muted-foreground"}`}>
                  {step}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

function IntegrationRow({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2">
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
        <p className="truncate text-xs text-foreground">{value}</p>
      </div>
      <span className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-success" : "bg-destructive"}`} />
    </div>
  );
}

function SummaryItem({ title, value }: { title: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{title}</span>
      <span className="inline-flex items-center gap-1 font-medium">
        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
        {value}
      </span>
    </div>
  );
}

export default Index;
