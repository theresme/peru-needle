import { useEffect, useState } from "react";

// cores por nível de evento
const NIVEL = {
  alerta:   { ring: "#ef4444", chip: "bg-red-500/15 text-red-300", label: "alerta" },
  virada:   { ring: "#f59e0b", chip: "bg-amber-500/15 text-amber-300", label: "virada" },
  exterior: { ring: "#3b82f6", chip: "bg-blue-500/15 text-blue-300", label: "exterior" },
  marco:    { ring: "#10b981", chip: "bg-emerald-500/15 text-emerald-300", label: "marco" },
  info:     { ring: "#6b7280", chip: "bg-gray-500/15 text-gray-300", label: "info" },
};

function haQuanto(iso, nowTick) {
  if (!iso) return "";
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `há ${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `há ${m}min`;
  const h = Math.floor(m / 60);
  return `há ${h}h ${m % 60}min`;
}

export default function EventFeed({ eventos }) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  if (!eventos || eventos.length === 0) {
    return (
      <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
        <Header n={0} />
        <p className="mt-3 text-sm text-gray-500">
          Aguardando movimento na apuração… os acontecimentos aparecem aqui em tempo real.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <Header n={eventos.length} />
      <div className="mt-4 max-h-[460px] overflow-y-auto pr-1">
        <ol className="relative border-l border-hair/70 ml-2">
          {eventos.map((e) => {
            const cfg = NIVEL[e.nivel] || NIVEL.info;
            return (
              <li key={e.id} className="mb-4 ml-5 fade-in">
                {/* bolinha da timeline */}
                <span
                  className="absolute -left-[7px] flex h-3.5 w-3.5 items-center justify-center rounded-full"
                  style={{ background: "#0e1116", boxShadow: `0 0 0 2px ${cfg.ring}` }}
                />
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-base leading-none">{e.icone}</span>
                      <span className="text-sm font-semibold text-gray-100">{e.titulo}</span>
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-gray-400">{e.texto}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${cfg.chip}`}>
                      {cfg.label}
                    </span>
                    <div className="mt-1 num text-[10px] text-gray-500">{haQuanto(e.t, tick)}</div>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}

function Header({ n }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="live-dot inline-block h-2 w-2 rounded-full bg-emerald-400" />
        <span className="text-sm font-semibold text-gray-200">Últimos acontecimentos</span>
      </div>
      {n > 0 && (
        <span className="text-[10px] uppercase tracking-wider text-gray-500">{n} eventos</span>
      )}
    </div>
  );
}
