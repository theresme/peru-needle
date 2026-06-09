import { useAgo } from "../hooks/usePoll";

export default function Header({ lastFetch, fonte, pollSeconds, onRefresh, error }) {
  const ago = useAgo(lastFetch);
  return (
    <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-gray-500">
          <span className="live-dot inline-block h-2 w-2 rounded-full bg-emerald-400" />
          Painel ao vivo · não-oficial
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold text-gray-50 mt-1 leading-tight">
          2ª volta · Peru 2026
        </h1>
        <p className="text-sm text-gray-400">
          Keiko Fujimori <span className="text-gray-600">vs</span> Roberto Sánchez
        </p>
      </div>

      <div className="flex items-center gap-3 text-right">
        <div className="text-xs text-gray-400">
          <div>
            atualizado <span className="text-gray-200">{ago}</span>
          </div>
          <div className="text-gray-600">
            fonte: {fonte || "—"} · auto a cada {pollSeconds || 45}s
          </div>
          {error && <div className="text-amber-400">aviso: {error}</div>}
        </div>
        <button
          onClick={onRefresh}
          className="rounded-lg border border-hair bg-panel px-3 py-2 text-sm text-gray-200 hover:bg-panel2 transition"
          title="Atualizar agora"
        >
          ↻
        </button>
      </div>
    </header>
  );
}
