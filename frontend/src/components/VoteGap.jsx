import { useEffect, useState } from "react";
import { int } from "../format";
import { fetchHistory } from "../api";
import { useCountUp } from "../hooks/useCountUp";
import Avatar, { iniciaisDe } from "./Avatar";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

// Gráfico da diferença (vK - vS) ao longo do tempo. Cruza o zero = virada.
function GapChart({ history }) {
  if (!history || history.length < 2) return null;
  const gaps = history
    .filter((h) => h.vK != null && h.vS != null)
    .map((h) => h.vK - h.vS);
  if (gaps.length < 2) return null;

  const W = 320, H = 90, pad = 10;
  const maxAbs = Math.max(...gaps.map((g) => Math.abs(g)), 1);
  const x = (i) => (i / (gaps.length - 1)) * W;
  const y = (g) => H / 2 - (g / maxAbs) * (H / 2 - pad);

  const line = gaps.map((g, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(g).toFixed(1)}`).join(" ");
  const area = `${line} L ${W} ${H / 2} L 0 ${H / 2} Z`;
  const ultimo = gaps[gaps.length - 1];
  const cor = ultimo >= 0 ? KEIKO : SANCHEZ;

  return (
    <div className="mt-4">
      <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">
        evolução da diferença
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 90 }} preserveAspectRatio="none">
        {/* faixa Keiko (cima) e Sánchez (baixo) sutil */}
        <line x1="0" y1={H / 2} x2={W} y2={H / 2} stroke="#4a2f36" strokeWidth="1" strokeDasharray="4 4" />
        <path d={area} fill={cor} opacity="0.13" />
        <path d={line} fill="none" stroke={cor} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={x(gaps.length - 1)} cy={y(ultimo)} r="3.5" fill={cor} />
      </svg>
      <div className="flex justify-between num text-[9px] uppercase tracking-wider text-gray-600">
        <span>↑ Keiko à frente</span>
        <span>Sánchez à frente ↓</span>
      </div>
    </div>
  );
}

export default function VoteGap({ candidatos, tick }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory()
      .then((d) => setHistory(d.history || []))
      .catch(() => {});
  }, [tick]);

  // hooks sempre antes de qualquer return condicional
  const ok = candidatos && candidatos.length >= 2;
  const [a, b] = ok ? candidatos : [null, null];
  const keiko = ok ? (a.id === "keiko" ? a : b) : null;
  const sanchez = ok ? (a.id === "sanchez" ? a : b) : null;
  const gap = ok ? Math.abs(keiko.votos - sanchez.votos) : 0;
  const gapAnim = useCountUp(gap);
  const vKAnim = useCountUp(keiko?.votos ?? 0);
  const vSAnim = useCountUp(sanchez?.votos ?? 0);
  if (!ok) return null;
  const lider = keiko.votos >= sanchez.votos ? keiko : sanchez;

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="text-sm font-semibold text-gray-200 mb-3">Diferença de votos</div>

      {/* gap em destaque */}
      <div className="text-center">
        <div className="text-[10px] uppercase tracking-widest text-gray-500">
          {lider.id === "keiko" ? "Keiko" : "Sánchez"} à frente por
        </div>
        <div className="num text-4xl sm:text-5xl font-extrabold leading-tight" style={{ color: lider.cor }}>
          {int(gapAnim)}
        </div>
        <div className="num text-[11px] text-gray-500">votos</div>
      </div>

      {/* dois candidatos: foto (quadrado) + votos */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="flex items-center gap-3 rounded-xl bg-panel2 border border-hair p-3">
          <Avatar id={keiko.id} cor={keiko.cor} iniciais={iniciaisDe(keiko.nome)} size={48} />
          <div className="min-w-0">
            <div className="text-xs font-semibold" style={{ color: KEIKO }}>Keiko</div>
            <div className="num text-base font-bold text-gray-100 leading-tight">{int(vKAnim)}</div>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl bg-panel2 border border-hair p-3">
          <Avatar id={sanchez.id} cor={sanchez.cor} iniciais={iniciaisDe(sanchez.nome)} size={48} />
          <div className="min-w-0">
            <div className="text-xs font-semibold" style={{ color: SANCHEZ }}>Sánchez</div>
            <div className="num text-base font-bold text-gray-100 leading-tight">{int(vSAnim)}</div>
          </div>
        </div>
      </div>

      <GapChart history={history} />
    </div>
  );
}
