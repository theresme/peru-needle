import { int, pct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";
const COR = { keiko: KEIKO, sanchez: SANCHEZ };
const CURTO = { keiko: "Keiko", sanchez: "Sánchez" };

// "Onde vivem os votos que faltam?" — o pacote travado no Jurado Electoral.
// Achado: contabilizadas + enviadas + pendentes = total. Tudo que falta
// apurar está no JEE; aqui mostramos onde está e pra quem pende.
export default function JeeCard({ jee }) {
  if (!jee || jee.estado !== "ativo" || !jee.atas) return null;

  const corFav = COR[jee.favorece];
  const corAtras = COR[jee.atras];
  const max = Math.max(1, ...jee.regioes.map((r) => Math.abs(r.netSanchez)));

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-base">⚖️</span>
          <span className="text-sm font-semibold text-gray-200">Atas no JEE</span>
        </div>
        <span className="num rounded-full bg-gray-500/15 px-2 py-0.5 text-[11px] font-bold text-gray-300">
          {int(jee.atas)} atas · {pct(jee.pctDoTotal, 2)}
        </span>
      </div>
      <p className="text-[11px] text-gray-500 mb-4">
        Contadas + enviadas ao JEE + pendentes = total. <span className="text-gray-400">Todo o
        voto que ainda falta está travado no Jurado Electoral</span> — ~{int(jee.votosEstimados)} votos.
      </p>

      {/* veredito */}
      <div
        className="rounded-xl border p-3 mb-4"
        style={{ borderColor: `${corFav}55`, background: `${corFav}10` }}
      >
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-xs text-gray-300">
            No padrão atual de cada região, o pacote favorece
          </span>
          <span className="num text-sm font-extrabold" style={{ color: corFav }}>
            {CURTO[jee.favorece]} +{int(Math.abs(jee.netSanchez))}
          </span>
        </div>
        <p className="mt-1.5 text-[11px] leading-relaxed text-gray-400">
          {jee.viraSeLeanAtual ? (
            <>
              <span className="font-semibold" style={{ color: corAtras }}>{CURTO[jee.atras]}</span>{" "}
              precisa de <span className="num">{int(jee.gap)}</span> líquido e o JEE lhe daria{" "}
              <span className="num font-semibold" style={{ color: corAtras }}>+{int(jee.saldoParaAtras)}</span> —
              dá pra virar.
            </>
          ) : (
            <>
              <span className="font-semibold" style={{ color: corAtras }}>{CURTO[jee.atras]}</span>{" "}
              precisaria de <span className="num">{int(jee.gap)}</span> votos líquidos, mas o lean das
              regiões com atas no JEE lhe é{" "}
              <span className="num font-semibold" style={{ color: corFav }}>
                {int(jee.saldoParaAtras)}
              </span>{" "}
              — o JEE é o seguro de {CURTO[jee.lider]}, não a virada.
            </>
          )}
        </p>
      </div>

      {/* onde estão (top regiões por saldo líquido) */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-gray-500 mb-1">
          <span>Onde estão (estimativa)</span>
          <span>saldo líquido →</span>
        </div>
        {jee.regioes.map((r) => {
          const cor = r.netSanchez >= 0 ? SANCHEZ : KEIKO;
          const w = (Math.abs(r.netSanchez) / max) * 100;
          return (
            <div key={r.nombre} className="flex items-center gap-2 text-xs">
              <span className="w-28 shrink-0 truncate text-gray-300">
                {r.nombre}
                {r.esExterior && <span className="text-gray-600"> ·ext</span>}
              </span>
              <span className="num w-16 shrink-0 text-right text-gray-500">{int(r.atas)} atas</span>
              <div className="relative h-3 flex-1 rounded bg-panel2 overflow-hidden">
                <div
                  className="absolute top-0 bottom-0 rounded"
                  style={{
                    background: cor,
                    width: `${w}%`,
                    right: r.netSanchez >= 0 ? "50%" : "auto",
                    left: r.netSanchez >= 0 ? "auto" : "50%",
                  }}
                />
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-hair" />
              </div>
              <span className="num w-16 shrink-0 text-right font-semibold" style={{ color: cor }}>
                +{int(Math.abs(r.netSanchez))}
              </span>
            </div>
          );
        })}
      </div>

      <p className="mt-3 text-[11px] text-gray-500">
        Saldo = votos estimados da região × lean observado ali. Azul puxa p/ Sánchez,
        âmbar p/ Keiko. Contagem de atas por região é estimada do % apurado; o total
        ({int(jee.atas)}) é oficial da ONPE.
      </p>
    </div>
  );
}
