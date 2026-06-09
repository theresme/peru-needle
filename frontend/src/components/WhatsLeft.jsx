import { int, pct, signedPct } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

function AmbitoRow({ titulo, block, badge }) {
  if (!block) return null;
  const lider = block.lider;
  const lc = lider === "keiko" ? KEIKO : SANCHEZ;
  const lnome = lider === "keiko" ? "Keiko" : "Sánchez";
  const pctLider = Math.max(block.pctK, block.pctS);

  return (
    <div className="rounded-xl bg-panel2 border border-hair p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-gray-400">{titulo}</span>
        {badge}
      </div>

      {/* barra K vs S */}
      <div className="mt-2 flex h-2 overflow-hidden rounded-full bg-hair">
        <div style={{ width: `${block.pctK}%`, background: KEIKO }} />
        <div style={{ width: `${block.pctS}%`, background: SANCHEZ }} />
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span style={{ color: lc }} className="num font-semibold">
          {lnome} {pct(pctLider, 1)}
        </span>
        <span className="num text-gray-500">{pct(block.pct, 1)} apurado</span>
      </div>

      {block.restantes > 0 && (
        <div className="mt-1.5 num text-[11px] text-gray-500">
          faltam {int(block.restantes)} atas · ~{int(block.votosRestantesEstimados)} votos
        </div>
      )}
    </div>
  );
}

export default function WhatsLeft({ atas, domestico, exterior, modelo }) {
  if (!modelo) return null;
  const extPct = exterior?.pct ?? 0;
  const extZero = extPct < 10;
  const extLeanKeiko = (exterior?.pctK ?? 0) > (exterior?.pctS ?? 0);

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="text-sm font-semibold text-gray-200 mb-3">
        Peru × Exterior · o que falta
      </div>

      <div className="space-y-3">
        <AmbitoRow titulo="Peru (doméstico)" block={domestico} />
        <AmbitoRow
          titulo="Voto do exterior"
          block={exterior}
          badge={
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                extZero ? "bg-amber-500/20 text-amber-300" : "bg-emerald-500/20 text-emerald-300"
              }`}
            >
              {pct(extPct, 0)} apurado
            </span>
          }
        />
      </div>

      {/* o porquê — auditável, com os leans do voto que ainda falta */}
      {modelo && (
        <div className="mt-3 rounded-xl bg-panel2/60 border border-hair p-3">
          <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1.5">
            Por que a agulha aponta assim
          </div>
          <p className="text-xs leading-relaxed text-gray-400">
            Do voto <span className="text-gray-300">doméstico</span> que falta (~
            <span className="num">{int(modelo.votosRestantesDom)}</span>), o lean é{" "}
            <span
              className="font-semibold"
              style={{ color: modelo.leanRestanteDomSanchez >= 50 ? SANCHEZ : KEIKO }}
            >
              {modelo.leanRestanteDomSanchez >= 50
                ? `Sánchez ${pct(modelo.leanRestanteDomSanchez, 1)}`
                : `Keiko ${pct(100 - modelo.leanRestanteDomSanchez, 1)}`}
            </span>{" "}
            (onde estão as atas pendentes, ex.: Lambayeque). O{" "}
            <span className="text-gray-300">exterior</span> que falta (~
            <span className="num">{int(modelo.votosRestantesExt)}</span>) tende a{" "}
            <span className="font-semibold" style={{ color: KEIKO }}>
              Keiko {pct(modelo.leanRestanteExtKeiko, 1)}
            </span>
            , mas com {pct(extPct, 0)} apurado a incerteza é alta.
          </p>
        </div>
      )}

      {/* probabilidade e margem final */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">
            Prob. de vencer
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span
              className="num text-2xl font-bold"
              style={{ color: modelo.favorito === "keiko" ? KEIKO : SANCHEZ }}
            >
              {pct(modelo.pFavorito * 100, 0)}
            </span>
            <span className="text-xs text-gray-400">
              {modelo.favorito === "keiko" ? "Keiko" : "Sánchez"}
            </span>
          </div>
        </div>

        <div className="rounded-xl bg-panel2 border border-hair p-3">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">
            Margem final proj.
          </div>
          <div className="num text-2xl font-bold text-gray-100 mt-1">
            {signedPct(modelo.margemP50, 1)}
          </div>
          <div className="num text-[10px] text-gray-500">
            80%: {signedPct(modelo.margemP10, 1)} a {signedPct(modelo.margemP90, 1)}
          </div>
        </div>
      </div>
    </div>
  );
}
