import { useEffect, useState } from "react";
import { fetchHistory } from "../api";

// Sparkline da evolução da P(vitória Keiko) nas últimas atualizações.
export default function Sparkline({ tick }) {
  const [pts, setPts] = useState([]);

  useEffect(() => {
    fetchHistory()
      .then((d) => setPts((d.history || []).map((h) => h.pKeiko)))
      .catch(() => {});
  }, [tick]);

  if (pts.length < 2) return null;

  const W = 220;
  const H = 40;
  const path = pts
    .map((p, i) => {
      const x = (i / (pts.length - 1)) * W;
      const y = H - p * H;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="mt-4 flex flex-col items-center">
      <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">
        evolução P(Keiko)
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-[220px] h-[40px]">
        <line x1="0" y1={H / 2} x2={W} y2={H / 2} stroke="#4a2f36" strokeWidth="1" strokeDasharray="3 3" />
        <path d={path} fill="none" stroke="#9aa4b2" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    </div>
  );
}
