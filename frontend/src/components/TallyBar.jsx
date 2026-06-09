import { int, pct } from "../format";

// Barra de apuração com segmentos: contabilizadas / observadas / restante.
export default function TallyBar({ atas, pctApurado }) {
  if (!atas) return null;
  const total = atas.total || 1;
  const contab = atas.contabilizadas || 0;
  const observ = atas.observadas || 0;
  const restante = atas.restantes ?? Math.max(0, total - contab);

  const wContab = (100 * (contab - observ)) / total;
  const wObserv = (100 * observ) / total;
  const wRest = (100 * restante) / total;

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-baseline justify-between mb-3">
        <span className="text-sm font-semibold text-gray-200">Apuração de atas</span>
        <span className="num text-sm text-gray-400">
          {pct(pctApurado, 1)} apurado
        </span>
      </div>

      <div className="h-4 w-full rounded-full overflow-hidden bg-panel2 flex">
        <div className="h-full bg-emerald-500/80" style={{ width: `${wContab}%` }} title="contabilizadas" />
        <div className="h-full bg-amber-400/70" style={{ width: `${wObserv}%` }} title="observadas" />
        <div className="h-full bg-gray-600/40" style={{ width: `${wRest}%` }} title="por apurar" />
      </div>

      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-gray-400">
        <Legend color="bg-emerald-500/80" label="Contabilizadas" v={int(contab - observ)} />
        <Legend color="bg-amber-400/70" label="Observadas" v={int(observ)} />
        <Legend color="bg-gray-600/60" label="Por apurar" v={int(restante)} />
      </div>
      <div className="mt-2 num text-sm text-gray-300">
        Apurado {pct(pctApurado, 1)} · faltam ~{int(restante)} atas
      </div>
    </div>
  );
}

function Legend({ color, label, v }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block h-2.5 w-2.5 rounded-sm ${color}`} />
      {label} <span className="num text-gray-300">{v}</span>
    </span>
  );
}
