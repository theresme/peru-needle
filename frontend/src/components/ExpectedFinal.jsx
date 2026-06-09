import { int, pct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

// Linha de uma candidatura: faixa P10–P90 + ponto na mediana, num eixo comum.
function RangeRow({ nome, cor, p10, p50, p90, votos, vlo, vhi, lo, hi }) {
  const posic = (v) => `${((v - lo) / (hi - lo)) * 100}%`;
  const left = ((p10 - lo) / (hi - lo)) * 100;
  const right = ((p90 - lo) / (hi - lo)) * 100;

  return (
    <div className="py-2">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-sm font-semibold" style={{ color: cor }}>
          {nome}
        </span>
        <span className="num text-lg font-bold" style={{ color: cor }}>
          {pct(p50, 1)}
        </span>
      </div>

      {/* trilho com faixa de incerteza */}
      <div className="relative h-6">
        {/* eixo base */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-hair" />
        {/* faixa P10–P90 */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-2 rounded-full"
          style={{ left: `${left}%`, width: `${right - left}%`, background: `${cor}55` }}
        />
        {/* mediana */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-4 w-1.5 rounded-full"
          style={{ left: posic(p50), transform: "translate(-50%, -50%)", background: cor }}
        />
      </div>

      <div className="mt-1 flex items-center justify-between num text-[11px] text-gray-500">
        <span>
          faixa {pct(p10, 1)}–{pct(p90, 1)}
        </span>
        <span>
          ~{int(votos)} votos
        </span>
      </div>
    </div>
  );
}

export default function ExpectedFinal({ modelo }) {
  if (!modelo) return null;

  // eixo comum (zoom na zona de disputa)
  const lo = Math.min(modelo.projFinalKeikoP10, modelo.projFinalSanchezP10) - 0.2;
  const hi = Math.max(modelo.projFinalKeikoP90, modelo.projFinalSanchezP90) + 0.2;
  const pos50 = ((50 - lo) / (hi - lo)) * 100;
  const dentro = pos50 >= 0 && pos50 <= 100;

  const favCor = modelo.favorito === "keiko" ? KEIKO : SANCHEZ;
  const favNome = modelo.favorito === "keiko" ? "Keiko Fujimori" : "Roberto Sánchez";

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-center justify-between mb-1">
        <div className="text-sm font-semibold text-gray-200">Votação final esperada</div>
        <span className="text-[10px] uppercase tracking-wider text-gray-500">projeção</span>
      </div>
      <p className="text-xs text-gray-500 mb-3">
        Onde o resultado deve aterrissar quando 100% das atas forem contadas
        (mediana e faixa de 80% do modelo).
      </p>

      <div className="relative">
        {/* linha da maioria (50%) atravessando as duas faixas */}
        {dentro && (
          <div
            className="pointer-events-none absolute top-7 bottom-7 w-px bg-gray-500/40 z-10"
            style={{ left: `${pos50}%` }}
          >
            <span className="absolute -top-4 -translate-x-1/2 text-[9px] uppercase tracking-wider text-gray-500 whitespace-nowrap">
              50% · maioria
            </span>
          </div>
        )}

        <RangeRow
          nome="Keiko Fujimori"
          cor={KEIKO}
          p10={modelo.projFinalKeikoP10}
          p50={modelo.projFinalKeiko}
          p90={modelo.projFinalKeikoP90}
          votos={modelo.projVotosKeiko}
          vlo={modelo.projVotosKeikoP10}
          vhi={modelo.projVotosKeikoP90}
          lo={lo}
          hi={hi}
        />
        <RangeRow
          nome="Roberto Sánchez"
          cor={SANCHEZ}
          p10={modelo.projFinalSanchezP10}
          p50={modelo.projFinalSanchez}
          p90={modelo.projFinalSanchezP90}
          votos={modelo.projVotosSanchez}
          vlo={modelo.projVotosSanchezP10}
          vhi={modelo.projVotosSanchezP90}
          lo={lo}
          hi={hi}
        />
      </div>

      {/* desfecho */}
      <div className="mt-4 rounded-xl bg-panel2 border border-hair p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Desfecho mais provável</span>
          <span className="num text-xs text-gray-500">
            total ~{int(modelo.projVotosTotal)} votos válidos
          </span>
        </div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-base font-bold" style={{ color: favCor }}>
            {favNome}
          </span>
          <span className="num text-sm text-gray-300">
            por {Math.abs(modelo.margemP50).toLocaleString("pt-BR", {
              minimumFractionDigits: 1,
              maximumFractionDigits: 1,
            })} pp
          </span>
          <span className="num text-xs text-gray-500">
            ({pct(modelo.pFavorito * 100, 0)} de probabilidade)
          </span>
        </div>
      </div>
    </div>
  );
}
