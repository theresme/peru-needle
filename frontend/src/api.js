// Cliente da API do painel. Em dev, /api é proxyado pro FastAPI (vite.config).
const BASE = import.meta.env.VITE_API_BASE || "";

export async function fetchState() {
  const r = await fetch(`${BASE}/api/state`, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchHistory() {
  const r = await fetch(`${BASE}/api/history`, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
