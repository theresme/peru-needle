import { useEffect, useState } from "react";
import { int } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

// Quadradinho com foto (se houver em /fotos/<id>.png) ou inicial.
function MiniFace({ id, cor, inicial }) {
  const [erro, setErro] = useState(false);
  return (
    <span
      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md overflow-hidden"
      style={{ background: `${cor}22`, boxShadow: `inset 0 0 0 1.5px ${cor}` }}
    >
      {!erro ? (
        <img
          src={`/fotos/${id}.png`}
          alt=""
          className="h-full w-full object-cover"
          onError={() => setErro(true)}
        />
      ) : (
        <span className="num text-[11px] font-extrabold" style={{ color: cor }}>
          {inicial}
        </span>
      )}
    </span>
  );
}

// Placar fixo no topo: aparece quando o usuário rola além do hero.
// Mostra % dos dois, quem lidera por quantos votos e a agulha resumida.
export default function StickyScore({ state }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 420);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (!state?.candidatos || state.candidatos.length < 2) return null;
  const [a, b] = state.candidatos;
  const keiko = a.id === "keiko" ? a : b;
  const sanchez = a.id === "sanchez" ? a : b;
  const gap = Math.abs(keiko.votos - sanchez.votos);
  const liderK = keiko.votos >= sanchez.votos;
  const liderCor = liderK ? KEIKO : SANCHEZ;
  const liderIni = liderK ? "K" : "S";

  const pFav = state.modelo ? Math.round((state.modelo.pFavorito ?? 0.5) * 100) : null;
  const favK = state.modelo?.favorito === "keiko";
  const favCor = favK ? KEIKO : SANCHEZ;

  const fmtPct = (n) =>
    n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div
      className={`fixed inset-x-0 top-0 z-50 transition-transform duration-300 ${
        show ? "translate-y-0" : "-translate-y-full"
      }`}
    >
      <div className="border-b border-hair bg-ink/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-2">
          {/* Keiko */}
          <div className="flex items-center gap-2 min-w-0">
            <MiniFace id="keiko" cor={KEIKO} inicial="KF" />
            <div className="leading-tight">
              <div className="num text-sm font-extrabold" style={{ color: KEIKO }}>
                {fmtPct(keiko.pctAtual)}%
              </div>
              <div className="hidden sm:block text-[9px] uppercase tracking-wider text-gray-500">
                Keiko
              </div>
            </div>
          </div>

          {/* centro: gap + apurado */}
          <div className="text-center leading-tight min-w-0">
            <div className="num text-xs sm:text-sm font-bold" style={{ color: liderCor }}>
              {liderIni} +{int(gap)}
            </div>
            <div className="num text-[9px] uppercase tracking-wider text-gray-500">
              {fmtPct(state.pctApurado ?? 0)}% apurado
            </div>
          </div>

          {/* agulha resumida */}
          {pFav != null && (
            <div
              className="hidden sm:flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wider"
              style={{ background: `${favCor}1c`, color: favCor }}
              title="Probabilidade de vitória (modelo)"
            >
              🎯 {favK ? "Keiko" : "Sánchez"} {pFav}%
            </div>
          )}

          {/* Sánchez */}
          <div className="flex flex-row-reverse items-center gap-2 min-w-0">
            <MiniFace id="sanchez" cor={SANCHEZ} inicial="RS" />
            <div className="leading-tight text-right">
              <div className="num text-sm font-extrabold" style={{ color: SANCHEZ }}>
                {fmtPct(sanchez.pctAtual)}%
              </div>
              <div className="hidden sm:block text-[9px] uppercase tracking-wider text-gray-500">
                Sánchez
              </div>
            </div>
          </div>
        </div>

        {/* régua de disputa: proporção K × S nos votos válidos */}
        <div className="flex h-[3px] w-full">
          <div
            className="h-full"
            style={{
              width: `${(100 * keiko.votos) / (keiko.votos + sanchez.votos || 1)}%`,
              background: KEIKO,
            }}
          />
          <div className="h-full flex-1" style={{ background: SANCHEZ }} />
        </div>
      </div>
    </div>
  );
}
