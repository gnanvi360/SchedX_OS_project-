import { Process, SimulationResponse, FAASDecisionStep, WorkloadSummary } from './types';

// In production (GitHub Pages) calls go to the hosted Render backend.
// In local dev the Vite proxy forwards /api → http://127.0.0.1:8000.
const IS_GH_PAGES = import.meta.env.MODE === 'production';
const PROD_BACKEND = 'https://schedx-api.onrender.com';
const API_BASE = IS_GH_PAGES ? `${PROD_BACKEND}/api` : '/api';

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export async function getPresets(): Promise<Record<string, Process[]>> {
  const res = await fetch(`${API_BASE}/presets`);
  if (!res.ok) throw new Error('Failed to load presets');
  const data = await res.json();
  return data.presets;
}

export async function getDistributions(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/distributions`);
  if (!res.ok) throw new Error('Failed to load distributions');
  const data = await res.json();
  return data.distributions;
}

export async function generateProcessesApi(params: {
  num_processes: number;
  min_arrival: number;
  max_arrival: number;
  min_burst: number;
  max_burst: number;
  distribution: string;
  seed?: number;
}): Promise<{ processes: Process[]; summary: WorkloadSummary }> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to generate processes');
  }
  return res.json();
}

export async function runSimulationApi(
  processes: Process[],
  faas_quantum = 2,
  faas_alpha = 4.0,
  faas_starvation_threshold = 8
): Promise<SimulationResponse> {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      processes,
      faas_quantum,
      faas_alpha,
      faas_starvation_threshold,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Simulation execution failed');
  }
  return res.json();
}

export async function fetchFaasInspectorApi(
  processes: Process[],
  faas_quantum = 2,
  faas_alpha = 4.0,
  faas_starvation_threshold = 8
): Promise<FAASDecisionStep[]> {
  const res = await fetch(`${API_BASE}/faas-inspector`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      processes,
      faas_quantum,
      faas_alpha,
      faas_starvation_threshold,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to inspect FAAS decisions');
  }
  const data = await res.json();
  return data.steps;
}
