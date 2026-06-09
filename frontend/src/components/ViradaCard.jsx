import { int } from "../format";

const KEIKO = "#f59e0b";
const SANCHEZ = "#3b82f6";

function horaLima(iso) {
  try {
    return new Date(iso).toLocaleTimeString("pt-BR", {
      hour: "2-digit", minute: "2-digit", timeZone: "America/Lima",
    });
  } catch {
    return null;
  }
}

function etaTexto(min) {
  if (min == null) return null;
  if (min < 90) return `~${min} min`;
  return `~${(min / 60).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} h`;
}

export default function ViradaCard({ virada }) {
  if (!virada) return null;
  const v = virada;

  // já virou: Keiko (ou quem estava atrás) passou à frente
  if (v.estado === "virou") {
    return (
      <div className="rounded-2xl border p-5 fade-in" style={{ borderColor: `${KEIKO}66`, background: `${KEIKO}12` }}>
        <div className="flex items-center gap-2">
          <span className="text-lg">🎉</span>
          <span className="text-sm font-semibold" style={{ color: KEIKO }}>Virada confirmada</span>
        </div>
        <div className="mt-2 num text-2xl font-extrabold text-gray-100">
          Keiko assumiu a liderança
        </div>
        <div className="num text-sm text-gray-400 mt-1">
          à frente por {int(v.gapAtual)} votos
        </div>
      </div>
    );
  }

  const atrasCor = v.quemAtras === "keiko" ? KEIKO : SANCHEZ;
  const atrasNome = v.quemAtras === "keiko" ? "Keiko" : "Sánchez";
  const saldoKeiko = v.saldoRestante; // >0 favorece Keiko
  const saldoNome = saldoKeiko >= 0 ? "Keiko" : "Sánchez";
  const saldoCor = saldoKeiko >= 0 ? KEIKO : SANCHEZ;
  const hora = v.etaISO ? horaLima(v.etaISO) : null;

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="live-dot inline-block h-2 w-2 rounded-full bg-amber-400" />
          <span className="text-sm font-semibold text-gray-200">Conta-giro da virada</span>
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            v.projetaVirar ? "bg-amber-500/20 text-amber-300" : "bg-gray-500/15 text-gray-400"
          }`}
        >
          {v.projetaVirar ? "projeção: vira" : "projeção: não vira"}
        </span>
      </div>

      {/* falta pra virar */}
      <div className="text-center">
        <div className="text-[10px] uppercase tracking-widest text-gray-500">
          faltam p/ {atrasNome} virar
        </div>
        <div className="num text-4xl font-extrabold leading-tight" style={{ color: atrasCor }}>
          {int(v.faltamParaVirar)}
        </div>
        <div className="num text-[11px] text-gray-500">votos</div>
      </div>

      {/* saldo restante */}
      <div className="mt-4 rounded-xl bg-panel2 border border-hair p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Saldo no que falta contar</span>
          <span className="num text-sm font-bold" style={{ color: saldoCor }}>
            {saldoKeiko >= 0 ? "+" : "−"}{int(Math.abs(saldoKeiko))} {saldoNome}
          </span>
        </div>
        <div className="num text-[11px] text-gray-500 mt-1">
          exterior {v.saldoExt >= 0 ? "+" : "−"}{int(Math.abs(v.saldoExt))} K · doméstico{" "}
          {v.saldoDom >= 0 ? "+" : "−"}{int(Math.abs(v.saldoDom))} K
        </div>
      </div>

      {/* ETA ao vivo ou estado da contagem */}
      <div className="mt-3 text-sm">
        {v.estado === "pausada" ? (
          <p className="text-gray-400">
            ⏸️ Contagem <span className="text-gray-200 font-semibold">pausada</span>
            {v.minSemMovimento != null && <> há {v.minSemMovimento} min</>} — sem ritmo pra
            cravar horário. Mas o saldo restante {v.projetaVirar ? "vira" : "não vira"} o jogo.
          </p>
        ) : v.etaMin != null ? (
          <p className="text-gray-300">
            ⏱️ No ritmo atual, <span className="font-semibold" style={{ color: atrasCor }}>{atrasNome} vira em {etaTexto(v.etaMin)}</span>
            {hora && <> (~{hora} em Lima)</>}.
          </p>
        ) : (
          <p className="text-gray-400">
            📊 Calculando ritmo… {v.projetaVirar
              ? "o saldo restante projeta a virada."
              : "no momento o saldo não vira."}
          </p>
        )}
      </div>
    </div>
  );
}
