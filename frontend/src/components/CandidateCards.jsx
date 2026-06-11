import { int, pct } from "../format";
import { useCountUp } from "../hooks/useCountUp";

// Seta de momentum: ▲ sobe (verde) · ▼ desce (vermelho).
// A fatia exata dos votos recentes já aparece no box "Votos na última hora",
// então aqui fica só a seta (sem texto redundante).
function Momentum({ tendencia }) {
  if (!tendencia) return null;
  const sobe = tendencia === "sobe";
  const cor = sobe ? "#10b981" : "#ef4444";
  const seta = sobe ? "▲" : "▼";
  return (
    <span
      className="inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-bold leading-none"
      style={{ background: `${cor}1f`, color: cor }}
      title={sobe
        ? "Ganhando terreno: leva uma fatia dos votos recentes acima da sua média"
        : "Perdendo terreno: leva uma fatia dos votos recentes abaixo da sua média"}
    >
      {seta}
    </span>
  );
}

function Card({ c, lider, tendencia }) {
  const pctAnim = useCountUp(c.pctAtual);
  const votosAnim = useCountUp(c.votos);
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

      <div className="mt-4 flex items-end gap-3">
        <div className="num text-4xl sm:text-5xl font-extrabold leading-none" style={{ color: c.cor }}>
          {pct(pctAnim, 4)}
        </div>
        <div className="mb-1">
          <Momentum tendencia={tendencia} />
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between">
        <div className="num text-sm text-gray-300">{int(votosAnim)} votos</div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">projeção final</div>
          <div className="num text-base font-semibold text-gray-200">{pct(c.projFinal, 1)}</div>
        </div>
      </div>
    </div>
  );
}

export default function CandidateCards({ candidatos, ultimaHora }) {
  if (!candidatos) return null;
  const [a, b] = candidatos;
  const liderId = a.pctAtual >= b.pctAtual ? a.id : b.id;

  // tendência por candidato a partir do momentum da última hora
  const uh = ultimaHora;
  const tend = (id) => {
    if (!uh || !uh.suficiente || !uh.subindo) return null;
    return uh.subindo === id ? "sobe" : "desce";
  };
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <Card c={a} lider={a.id === liderId} tendencia={tend(a.id)} />
      <Card c={b} lider={b.id === liderId} tendencia={tend(b.id)} />
    </div>
  );
}
