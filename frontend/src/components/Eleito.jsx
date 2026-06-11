import { int, pct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";
const NOMES = { keiko: "Keiko Fujimori", sanchez: "Roberto Sánchez" };
const CURTO = { keiko: "Keiko", sanchez: "Sánchez" };
const COR = { keiko: KEIKO, sanchez: SANCHEZ };

// "Já está eleito?" — verdade dura (matemática), não probabilidade.
export default function Eleito({ eleito }) {
  if (!eleito || eleito.estado === "indefinido") return null;

  // ---------- ESTADO 1: matematicamente eleito ----------
  if (eleito.estado === "eleito") {
    const cor = COR[eleito.quem];
    return (
      <div
        className="relative overflow-hidden rounded-2xl border-2 p-6 fade-in text-center"
        style={{ borderColor: cor, background: `${cor}14` }}
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{ background: `radial-gradient(60% 80% at 50% 0%, ${cor}33, transparent 70%)` }}
        />
        <div className="relative">
          <div className="text-3xl mb-1">🏆</div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-gray-400">
            Matematicamente eleito
          </div>
          <div className="num text-3xl sm:text-4xl font-extrabold mt-1" style={{ color: cor }}>
            {NOMES[eleito.quem]}
          </div>
          <p className="mt-3 text-sm text-gray-300 max-w-md mx-auto">
            Mesmo que <span className="font-semibold">todos</span> os votos restantes fossem
            para {CURTO[eleito.perdedor]}, a liderança de{" "}
            <span className="num font-semibold" style={{ color: cor }}>
              {int(eleito.gap)}
            </span>{" "}
            votos não pode mais ser revertida.
          </p>
          <p className="mt-2 text-[11px] text-gray-500">
            {pct(eleito.pctApurado, 2)} apurado · proclamação oficial cabe ao JNE
          </p>
        </div>
      </div>
    );
  }

  // ---------- ESTADO 2: em aberto (ainda reversível) ----------
  const corL = COR[eleito.quem];
  const corA = COR[eleito.perdedor];
  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="live-dot inline-block h-2 w-2 rounded-full bg-amber-400" />
          <span className="text-sm font-semibold text-gray-200">Já está eleito?</span>
        </div>
        <span className="rounded-full bg-gray-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gray-400">
          ainda não · reversível
        </span>
      </div>

      <p className="text-sm text-gray-300">
        <span className="font-semibold" style={{ color: corL }}>{CURTO[eleito.quem]}</span>{" "}
        lidera por <span className="num font-semibold" style={{ color: corL }}>{int(eleito.gap)}</span>{" "}
        votos, mas ainda podem entrar até{" "}
        <span className="num font-semibold text-gray-200">{int(eleito.maxReversivel)}</span>{" "}
        votos ({int(eleito.atasRestantes)} atas) — matematicamente, dá pra virar.
      </p>

      {/* o número mágico */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">
            {CURTO[eleito.quem]} crava se garantir
          </div>
          <div className="num text-lg font-bold mt-0.5" style={{ color: corL }}>
            {int(eleito.faltamParaCravar)}
          </div>
          <div className="num text-[11px] text-gray-500">
            ≈ {pct(eleito.faltamPctParaCravar, 4)} do que falta
          </div>
        </div>
        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">
            {CURTO[eleito.perdedor]} vira se levar
          </div>
          <div className="num text-lg font-bold mt-0.5" style={{ color: corA }}>
            {pct(eleito.perseguidorPrecisaPct, 4)}
          </div>
          <div className="num text-[11px] text-gray-500">
            dos ~{int(eleito.votosRestEstimados)} votos restantes
          </div>
        </div>
      </div>

      <p className="mt-3 text-[11px] text-gray-500">
        "Matematicamente eleito" = nem todos os votos restantes juntos revertem a liderança.
        A probabilidade do modelo é outra leitura (acima); aqui é só a aritmética dura.
      </p>
    </div>
  );
}
