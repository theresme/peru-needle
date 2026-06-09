import { int, pct } from "../format";

function Card({ c, lider }) {
  return (
    <div
      className="relative flex-1 rounded-2xl bg-panel border border-hair p-5 overflow-hidden fade-in"
      style={{ boxShadow: lider ? `inset 0 0 0 1px ${c.cor}55` : "none" }}
    >
      <div className="absolute top-0 left-0 h-1 w-full" style={{ background: c.cor }} />
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-lg font-bold" style={{ color: c.cor }}>
            {c.nome}
          </div>
          <div className="text-xs uppercase tracking-wider text-gray-400">{c.partido}</div>
        </div>
        {lider && (
          <span
            className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
            style={{ background: `${c.cor}22`, color: c.cor }}
          >
            na frente
          </span>
        )}
      </div>

      <div className="mt-4 num text-6xl font-extrabold leading-none" style={{ color: c.cor }}>
        {pct(c.pctAtual, 1)}
      </div>

      <div className="mt-3 flex items-end justify-between">
        <div className="num text-sm text-gray-300">{int(c.votos)} votos</div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">projeção final</div>
          <div className="num text-base font-semibold text-gray-200">{pct(c.projFinal, 1)}</div>
        </div>
      </div>
    </div>
  );
}

export default function CandidateCards({ candidatos }) {
  if (!candidatos) return null;
  const [a, b] = candidatos;
  const liderId = a.pctAtual >= b.pctAtual ? a.id : b.id;
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <Card c={a} lider={a.id === liderId} />
      <Card c={b} lider={b.id === liderId} />
    </div>
  );
}
