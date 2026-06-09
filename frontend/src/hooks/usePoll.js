import { useCallback, useEffect, useRef, useState } from "react";
import { fetchState } from "../api";

const POLL_MS = 45_000;

export function usePoll() {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState(null); // Date local da última resposta
  const timer = useRef(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchState();
      if (data.ready === false) {
        setError(data.error || "carregando…");
      } else {
        setState(data);
        setError(data.error || null);
        setLastFetch(new Date());
      }
    } catch (e) {
      setError(e.message || "falha de rede");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    timer.current = setInterval(load, POLL_MS);
    return () => clearInterval(timer.current);
  }, [load]);

  return { state, error, loading, lastFetch, refresh: load };
}

// "atualizado há 12s" — recalcula a cada segundo
export function useAgo(date) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);
  if (!date) return "—";
  const s = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (s < 60) return `há ${s}s`;
  const m = Math.floor(s / 60);
  return `há ${m}min ${s % 60}s`;
}
