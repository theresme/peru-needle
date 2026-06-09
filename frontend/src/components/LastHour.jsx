import { int } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

const f1 = (n) => (n ?? 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export default function LastHour({ ultimaHora }) {
  const uh = ultimaHora;

  const titulo = (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <span className="live-dot inline-block h-2 w-2 rounded-full bg-emerald-400" />
        <span className="text-sm font-semibold text-gray-200">Votos na última hora</span>
      </div>
      {uh && uh.spanMin > 0 && (
        <span className="num text-[10px] uppercase tracking-wider text-gray-500">
          {uh.spanMin >= 60 ? "últimos 60 min" : `últimos ${uh.spanMin} min`}
        </span>
      )}
    </div>
  );

  if (!uh || !uh.suficiente) {
    return (
      <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
        {titulo}
        <p className="text-sm text-gray-500">
          Coletando dados… o ritmo de votos aparece após alguns minutos de
          apuração (ou quando entram novas atas).
        </p>
      </div>
    );
  }

  const splitK = uh.splitK;
  const splitS = uh.splitS;
  const ganhador = splitK >= splitS ? "keiko" : "sanchez";
  const gCor = ganhador === "keiko" ? KEIKO : SANCHEZ;
  const gNome = ganhador === "keiko" ? "Keiko" : "Sánchez";
  const gSplit = Math.max(splitK, splitS);

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      {titulo}

      {/* dois contadores */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-xs font-semibold" style={{ color: KEIKO }}>Keiko</div>
          <div className="num text-2xl font-bold mt-0.5" style={{ color: KEIKO }}>
            +{int(uh.deltaVotosK)}
          </div>
          <div className="num text-[11px] text-gray-500">{f1(splitK)}% dos novos</div>
        </div>
        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-xs font-semibold" style={{ color: SANCHEZ }}>Sánchez</div>
          <div className="num text-2xl font-bold mt-0.5" style={{ color: SANCHEZ }}>
            +{int(uh.deltaVotosS)}
          </div>
          <div className="num text-[11px] text-gray-500">{f1(splitS)}% dos novos</div>
        </div>
      </div>

      {/* barra de divisão dos votos recentes */}
      <div className="mt-3 flex h-2.5 overflow-hidden rounded-full bg-hair">
        <div style={{ width: `${splitK}%`, background: KEIKO }} />
        <div style={{ width: `${splitS}%`, background: SANCHEZ }} />
      </div>

      <p className="mt-2 text-xs text-gray-400">
        Dos <span className="num text-gray-300">{int(uh.deltaVotosTotal)}</span> votos que
        entraram, <span className="font-semibold" style={{ color: gCor }}>{f1(gSplit)}% foram para {gNome}</span>
        {uh.subindo && (
          <> — quem está <span className="font-semibold" style={{ color: gCor }}>ganhando terreno</span> agora.</>
        )}
      </p>
    </div>
  );
}
