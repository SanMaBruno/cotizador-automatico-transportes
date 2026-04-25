// Cliente API: por defecto usa FastAPI local.
// Para demo sin backend: VITE_USE_MOCK=true.
import { mockClient } from "./cotizador/mockClient";
import type { Email, IntegrationStatus, ProcessRun } from "./cotizador/types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  mode: USE_MOCK ? ("mock" as const) : ("remote" as const),
  baseUrl: USE_MOCK ? "(mock local)" : BASE,

  async health() {
    if (USE_MOCK) return mockClient.health();
    return http<{ status: string; mode?: string }>("/health");
  },
  async integrationsStatus(): Promise<IntegrationStatus> {
    if (USE_MOCK) return mockClient.integrationsStatus();
    return http<IntegrationStatus>("/integrations/status");
  },
  async getEmails(): Promise<Email[]> {
    if (USE_MOCK) return mockClient.getEmails();
    return http<Email[]>("/emails");
  },
  async process(): Promise<ProcessRun> {
    if (USE_MOCK) return mockClient.process();
    return http<ProcessRun>("/process", { method: "POST" });
  },
  async latestRun(): Promise<ProcessRun | null> {
    if (USE_MOCK) return mockClient.latestRun();
    try {
      return await http<ProcessRun>("/runs/latest");
    } catch {
      return null;
    }
  },
};
