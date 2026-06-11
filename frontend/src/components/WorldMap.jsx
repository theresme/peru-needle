import { useEffect, useMemo, useRef, useState } from "react";
import { int, pct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";
const NEUTRO = "#2b1c21";   // país sem voto peruano
const PERU = "#9ca3af";     // o próprio Peru

// equiretangular, recortando latitudes extremas (Antártida/Ártico)
const W = 1000, H = 500;
const LAT_TOP = 83, LAT_BOT = -56;
const yTop = ((90 - LAT_TOP) / 180) * H;
const yBot = ((90 - LAT_BOT) / 180) * H;
const proj = ([lon, lat]) => [((lon + 180) / 360) * W, ((90 - lat) / 180) * H];

function geoPath(geom) {
  const polys = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
  let d = "";
  for (const poly of polys) {
    for (const ring of poly) {
      for (let i = 0; i < ring.length; i++) {
        const [x, y] = proj(ring[i]);
        d += (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1) + " ";
      }
      d += "Z ";
    }
  }
  return d;
}

// cor do país: vencedor + opacidade pela margem (50%→0.4, 100%→1)
function corPais(c) {
  if (!c) return NEUTRO;
  const base = c.lider === "keiko" ? KEIKO : SANCHEZ;
  const margem = Math.max(c.pctK, c.pctS); // 50..100
  const op = Math.max(0.4, Math.min(1, 0.4 + ((margem - 50) / 50) * 0.6));
  // mistura com o fundo escuro pela opacidade (cor sólida calculada)
  return mix(base, "#12090b", op);
}

// mistura hex a com hex b por t (t=1 => a puro)
function mix(a, b, t) {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const r = pa.map((v, i) => Math.round(v * t + pb[i] * (1 - t)));
  return `#${r.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

export default function WorldMap({ paises }) {
  const [features, setFeatures] = useState(null);
  const [hover, setHover] = useState(null); // {nome, lider, pctK, pctS, votos, x, y}
  const wrapRef = useRef(null);

  useEffect(() => {
    fetch("/world.geo.json")
      .then((r) => r.json())
      .then((j) => setFeatures(j.features))
      .catch(() => {});
  }, []);

  // índice ISO -> país (com voto)
  const porIso = useMemo(() => {
    const m = {};
    for (const p of paises || []) {
      if (p.iso && (p.vK + p.vS) > 0) m[p.iso] = p;
    }
    return m;
  }, [paises]);

  const totais = useMemo(() => {
    let k = 0, s = 0;
    for (const p of paises || []) {
      if (p.vK + p.vS === 0) continue;
      if (p.lider === "keiko") k++; else s++;
    }
    return { k, s };
  }, [paises]);

  if (!paises?.length) return null;

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-base">🗺️</span>
          <span className="text-sm font-semibold text-gray-200">Mapa do voto no exterior</span>
        </div>
        <div className="flex items-center gap-3 text-[11px] num">
          <span className="inline-flex items-center gap-1" style={{ color: KEIKO }}>
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: KEIKO }} /> Fujimori · {totais.k}
          </span>
          <span className="inline-flex items-center gap-1" style={{ color: SANCHEZ }}>
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: SANCHEZ }} /> Sánchez · {totais.s}
          </span>
        </div>
      </div>
      <p className="text-[11px] text-gray-500 mb-3">
        Cada país pintado pela cor de quem venceu ali; tom mais forte = vitória mais folgada.
      </p>

      <div ref={wrapRef} className="relative">
        {features ? (
          <svg
            viewBox={`0 ${yTop.toFixed(0)} ${W} ${(yBot - yTop).toFixed(0)}`}
            className="w-full"
            style={{ display: "block" }}
            onMouseLeave={() => setHover(null)}
          >
            {features.map((f, idx) => {
              const iso = f.id;
              const c = porIso[iso];
              const fill = iso === "PER" ? PERU : corPais(c);
              return (
                <path
                  key={`${iso}-${idx}`}
                  d={geoPath(f.geometry)}
                  fill={fill}
                  stroke="#0e0709"
                  strokeWidth="0.6"
                  style={{ cursor: c ? "pointer" : "default", transition: "fill .2s" }}
                  onMouseEnter={(e) => {
                    if (!c && iso !== "PER") return setHover(null);
                    const r = wrapRef.current.getBoundingClientRect();
                    setHover({
                      ...(c || { nombre: "Peru", lider: null }),
                      x: e.clientX - r.left,
                      y: e.clientY - r.top,
                    });
                  }}
                />
              );
            })}
          </svg>
        ) : (
          <div className="h-48 flex items-center justify-center text-xs text-gray-600">
            carregando mapa…
          </div>
        )}

        {hover && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-hair bg-ink/95 px-3 py-2 text-xs shadow-lg backdrop-blur"
            style={{
              left: Math.min(hover.x + 12, (wrapRef.current?.clientWidth || 300) - 150),
              top: hover.y + 12,
            }}
          >
            <div className="font-semibold text-gray-100">{hover.nombre}</div>
            {hover.lider ? (
              <>
                <div className="num" style={{ color: hover.lider === "keiko" ? KEIKO : SANCHEZ }}>
                  {hover.lider === "keiko" ? "Fujimori" : "Sánchez"} {pct(Math.max(hover.pctK, hover.pctS), 1)}
                </div>
                <div className="num text-[11px] text-gray-500">{int(hover.vK + hover.vS)} votos</div>
              </>
            ) : (
              <div className="text-[11px] text-gray-500">país de origem</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
