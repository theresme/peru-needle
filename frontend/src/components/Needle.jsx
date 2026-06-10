import { useEffect, useRef } from "react";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

// geometria do gauge
const W = 460;
const H = 272;
const CX = W / 2;
const CY = 232;
const R = 196;
const RAD = Math.PI / 180;

// pKeiko (0..1) -> ângulo da agulha em graus (-90 = Sánchez, 0 = empate, +90 = Keiko)
const pToAngle = (pK) => (pK - 0.5) * 180;

// ângulo da agulha (-90..+90, 0=topo) -> ponto no arco
function arcPoint(t, r = R) {
  const a = (90 - t) * RAD;
  return { x: CX + r * Math.cos(a), y: CY - r * Math.sin(a) };
}

// constrói "d" de um setor de arco entre dois ângulos de agulha
function bandPath(t0, t1, rOuter, rInner) {
  const o0 = arcPoint(t0, rOuter);
  const o1 = arcPoint(t1, rOuter);
  const i1 = arcPoint(t1, rInner);
  const i0 = arcPoint(t0, rInner);
  return [
    `M ${o0.x} ${o0.y}`,
    `A ${rOuter} ${rOuter} 0 0 1 ${o1.x} ${o1.y}`,
    `L ${i1.x} ${i1.y}`,
    `A ${rInner} ${rInner} 0 0 0 ${i0.x} ${i0.y}`,
    "Z",
  ].join(" ");
}

// faixas de cor (em ângulo de agulha): tossup central cinza, leans/likely/solid
const BANDS = [
  { from: -90, to: -54, color: SANCHEZ, op: 0.95 },
  { from: -54, to: -27, color: SANCHEZ, op: 0.6 },
  { from: -27, to: -9, color: SANCHEZ, op: 0.32 },
  { from: -9, to: 9, color: "#6b7280", op: 0.45 },
  { from: 9, to: 27, color: KEIKO, op: 0.32 },
  { from: 27, to: 54, color: KEIKO, op: 0.6 },
  { from: 54, to: 90, color: KEIKO, op: 0.95 },
];

export default function Needle({ modelo }) {
  const pK = modelo?.pVitoriaKeiko ?? 0.5;
  const favorito = modelo?.favorito ?? "keiko";
  const pFav = Math.round((modelo?.pFavorito ?? 0.5) * 100);

  const favColor = favorito === "keiko" ? KEIKO : SANCHEZ;
  const favNome = favorito === "keiko" ? "Keiko" : "Sánchez";
  // rótulo derivado do MESMO número exibido (evita "60% · Toss-up")
  const pf = pFav / 100;
  const bandLabel =
    pf < 0.6 ? "Toss-up" : pf < 0.75 ? "Leans" : pf < 0.9 ? "Likely" : "Solid";

  const lineRef = useRef(null);
  const hubRef = useRef(null);
  // alvos lidos pela rAF sem recriar o loop a cada update de dados
  const target = useRef({ angle: pToAngle(pK), jitter: 1.2, color: favColor });
  const display = useRef(pToAngle(pK));

  // atualiza alvos quando chegam novos dados (não recria o rAF)
  useEffect(() => {
    const confidence = Math.abs(2 * pK - 1); // 0 = empate
    target.current = {
      angle: pToAngle(pK),
      jitter: 1.2 + (1 - confidence) * 9, // graus
      color: favColor,
    };
  }, [pK, favColor]);

  // loop de animação imperativo: NÃO dispara re-render do React
  useEffect(() => {
    let t = 0;
    let raf;
    const loop = () => {
      t += 0.016;
      const { angle: tgt, jitter: amp, color } = target.current;
      display.current += (tgt - display.current) * 0.06; // easing
      const jitter =
        Math.sin(t * 2.1) * 0.5 * amp +
        Math.sin(t * 5.7 + 1.3) * 0.3 * amp +
        (Math.random() - 0.5) * 0.4 * amp;
      const tip = arcPoint(display.current + jitter, R - 14);
      if (lineRef.current) {
        lineRef.current.setAttribute("x2", tip.x.toFixed(2));
        lineRef.current.setAttribute("y2", tip.y.toFixed(2));
        lineRef.current.setAttribute("stroke", color);
      }
      if (hubRef.current) hubRef.current.setAttribute("stroke", color);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const tip0 = arcPoint(pToAngle(pK), R - 14);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[460px]">
        {BANDS.map((b, i) => (
          <path key={i} d={bandPath(b.from, b.to, R, R - 26)} fill={b.color} opacity={b.op} />
        ))}

        {[-90, -45, 0, 45, 90].map((tk) => {
          const a = arcPoint(tk, R - 28);
          const b = arcPoint(tk, R - 40);
          return <line key={tk} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#4a2f36" strokeWidth="2" />;
        })}

        <text x={CX - R + 2} y={CY + 26} fill={SANCHEZ} fontSize="13" fontWeight="700" textAnchor="start">
          Sánchez
        </text>
        <text x={CX + R - 2} y={CY + 26} fill={KEIKO} fontSize="13" fontWeight="700" textAnchor="end">
          Keiko
        </text>
        <text x={CX} y={28} fill="#8b95a3" fontSize="11" fontWeight="600" textAnchor="middle" letterSpacing="1">
          EMPATE
        </text>

        <line
          ref={lineRef}
          x1={CX}
          y1={CY}
          x2={tip0.x}
          y2={tip0.y}
          stroke={favColor}
          strokeWidth="4"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${favColor}66)` }}
        />
        <circle ref={hubRef} cx={CX} cy={CY} r="11" fill="#12090b" stroke={favColor} strokeWidth="3" />
      </svg>

      <div className="-mt-2 text-center fade-in">
        <div className="num text-5xl font-extrabold" style={{ color: favColor }}>
          {favNome} {pFav}%
        </div>
        <div className="mt-1 text-sm uppercase tracking-widest text-gray-400">
          provável · <span style={{ color: favColor }}>{bandLabel}</span>
        </div>
      </div>
    </div>
  );
}
