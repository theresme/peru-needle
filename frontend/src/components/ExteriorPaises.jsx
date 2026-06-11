import { useState } from "react";
import { int, pct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";
const NOMES = { keiko: "Keiko", sanchez: "Sánchez" };

const TOP_FECHADO = 6; // quantos países mostrar antes do "ver todos"

function Row({ p }) {
  const validos = p.vK + p.vS;
  const cor = p.lider === "keiko" ? KEIKO : SANCHEZ;
  const wK = validos ? (100 * p.vK) / validos : 0;
  const aberto = p.atasTotal > 0;
  return (
    <div className="py-2.5 border-b border-hair/50 last:border-0">
      <div className="flex items-baseline justify-between gap-2">
        <div className="min-w-0">
          <span className="text-sm text-gray-200">{p.nombre}</span>
          {p.continente && (
            <span className="ml-2 text-[9px] uppercase tracking-wider text-gray-600">
              {p.continente}
            </span>
          )}
        </div>
        <div className="shrink-0 num text-sm font-semibold" style={{ color: cor }}>
          {validos > 0 ? `${NOMES[p.lider]} ${pct(Math.max(p.pctK, p.pctS), 1)}` : "—"}
        </div>
      </div>

      {/* split K × S */}
      <div className="mt-1.5 flex h-1.5 w-full overflow-hidden rounded-full bg-panel2">
        <div className="h-full" style={{ width: `${wK}%`, background: KEIKO }} />
        <div className="h-full flex-1" style={{ background: validos ? SANCHEZ : "transparent" }} />
      </div>

      <div className="mt-1 flex items-center justify-between num text-[11px] text-gray-500">
        <span>{int(validos)} votos</span>
        <span>
          {aberto ? (
            p.atasRestantes > 0 ? (
              <>
                {pct(p.pctApurado, 1)} apurado ·{" "}
                <span className="text-amber-300/90">
                  faltam {int(p.atasRestantes)} atas (~{int(p.votosRestantesEstimados)} votos)
                </span>
              </>
            ) : (
              <span className="text-emerald-400/80">100% apurado ✓</span>
            )
          ) : (
            "sem ata apurada ainda"
          )}
        </span>
      </div>
    </div>
  );
}

// "Peruanos no estrangeiro": desglose oficial por país, expansível.
export default function ExteriorPaises({ paises, exterior }) {
  const [aberto, setAberto] = useState(false);
  const [todos, setTodos] = useState(false);

  if (!paises?.length) return null;

  const visiveis = todos ? paises : paises.slice(0, TOP_FECHADO);
  const pendentes = paises.filter((p) => p.atasRestantes > 0).length;

  return (
    <div className="rounded-2xl bg-panel border border-hair fade-in overflow-hidden">
      {/* cabeçalho clicável */}
      <button
        onClick={() => setAberto((v) => !v)}
        className="w-full flex items-center justify-between gap-3 p-5 text-left hover:bg-panel2/50 transition"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-base">🌎</span>
          <span className="text-sm font-semibold text-gray-200">
            Peruanos no estrangeiro · por país
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {exterior && (
            <span className="hidden sm:inline num text-xs text-gray-400">
              {pct(exterior.pct ?? 0, 1)} apurado ·{" "}
              <span style={{ color: exterior.lider === "keiko" ? KEIKO : SANCHEZ }}>
                {NOMES[exterior.lider] ?? ""} {pct(Math.max(exterior.pctK ?? 0, exterior.pctS ?? 0), 1)}
              </span>
            </span>
          )}
          <span className="text-[10px] uppercase tracking-wider text-gray-500">
            {paises.length} países
          </span>
          <span
            className={`text-gray-400 transition-transform duration-200 ${aberto ? "rotate-180" : ""}`}
          >
            ▾
          </span>
        </div>
      </button>

      {aberto && (
        <div className="px-5 pb-5">
          {pendentes > 0 && (
            <div className="mb-2 text-[11px] text-gray-500">
              {pendentes} {pendentes === 1 ? "país ainda tem" : "países ainda têm"} atas por
              apurar — ordenado por votos.
            </div>
          )}
          {visiveis.map((p) => (
            <Row key={p.nombre} p={p} />
          ))}
          {paises.length > TOP_FECHADO && (
            <button
              onClick={() => setTodos((v) => !v)}
              className="mt-3 w-full rounded-lg border border-hair bg-panel2 py-2 text-xs text-gray-300 hover:border-peru/50 transition"
            >
              {todos ? "Mostrar menos" : `Ver todos os ${paises.length} países`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
