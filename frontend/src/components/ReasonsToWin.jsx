import { pct } from "../format";

// Ícone de check/x/pendente
function Icon({ status }) {
  if (status === "ok")
    return <span className="text-emerald-400 font-bold text-sm leading-none">✓</span>;
  if (status === "nao")
    return <span className="text-red-400/70 font-bold text-sm leading-none">✗</span>;
  return <span className="text-amber-400/80 text-sm leading-none">◎</span>;
}

function Item({ status, label, valor }) {
  const dim = status === "nao";
  return (
    <div className={`flex items-start gap-2 ${dim ? "opacity-40" : ""}`}>
      <div className="mt-0.5 shrink-0">
        <Icon status={status} />
      </div>
      <div className="min-w-0">
        <span className="text-xs text-gray-300 leading-snug">{label}</span>
        {valor && (
          <span className="ml-1.5 num text-xs text-gray-500">{valor}</span>
        )}
      </div>
    </div>
  );
}

function dept(rows, nome) {
  return rows?.find((r) => r.nombre === nome);
}

export default function ReasonsToWin({ candidatos, rows, exterior, modelo }) {
  if (!candidatos || !modelo) return null;
  const [keiko, sanchez] = candidatos;
  const kFrente = keiko.pctAtual > sanchez.pctAtual;
  const margem = Math.abs(keiko.pctAtual - sanchez.pctAtual);

  const lima = dept(rows, "Lima");
  const arequipa = dept(rows, "Arequipa");
  const ayacucho = dept(rows, "Ayacucho");
  const cusco = dept(rows, "Cusco");
  const puno = dept(rows, "Puno");
  const lambayeque = dept(rows, "Lambayeque");
  const laLibertad = dept(rows, "La Libertad");
  const callao = dept(rows, "Callao");
  const extPct = exterior?.pct ?? 0;

  // Keiko items
  const kItems = [
    {
      status: lima ? (lima.pctK > 50 ? "ok" : "nao") : "pendente",
      label: "Lima vota Keiko",
      valor: lima ? `${pct(lima.pctK, 1)} (${pct(lima.pctApurado, 0)} apurado)` : null,
    },
    {
      status: lambayeque ? (lambayeque.pctK > 55 ? "ok" : "nao") : "pendente",
      label: "Lambayeque / norte costeiro",
      valor: lambayeque ? `${pct(lambayeque.pctK, 1)} Keiko` : null,
    },
    {
      status: laLibertad ? (laLibertad.pctK > 50 ? "ok" : "nao") : "pendente",
      label: "La Libertad acima de 50%",
      valor: laLibertad ? `${pct(laLibertad.pctK, 1)} Keiko` : null,
    },
    {
      status: extPct < 5 ? "pendente" : extPct > 0 && (exterior?.vK ?? 0) > (exterior?.vS ?? 0) ? "ok" : "nao",
      label: "Exterior não apurado (historicamente +66% Keiko)",
      valor: extPct > 0 ? `${pct(extPct, 0)} apurado` : "0% apurado — ainda por vir",
    },
    {
      status: kFrente ? "ok" : "nao",
      label: "Na frente no cômputo geral",
      valor: kFrente ? `+${pct(margem, 2)} pp` : null,
    },
  ];

  // Sánchez items
  const sItems = [
    {
      status: ayacucho ? (ayacucho.pctS > 65 ? "ok" : "nao") : "pendente",
      label: "Sul andino maciço (Ayacucho / Apurímac)",
      valor: ayacucho ? `${pct(ayacucho.pctS, 1)} Sánchez` : null,
    },
    {
      status: cusco ? (cusco.pctS > 65 ? "ok" : "nao") : "pendente",
      label: "Cusco e Puno consolidados",
      valor: cusco ? `Cusco ${pct(cusco.pctS, 1)} · Puno ${pct(puno?.pctS ?? 50, 1)}` : null,
    },
    {
      status: arequipa ? (arequipa.pctS > 55 ? "ok" : "nao") : "pendente",
      label: "Arequipa vira para a esquerda",
      valor: arequipa ? `${pct(arequipa.pctS, 1)} Sánchez` : null,
    },
    {
      status: callao ? (callao.pctS > 55 ? "ok" : "nao") : "pendente",
      label: "Callao / periferia de Lima",
      valor: callao ? `${pct(callao.pctS, 1)} Sánchez (${pct(callao.pctApurado, 0)} apurado)` : null,
    },
    {
      status: !kFrente ? "ok" : "nao",
      label: "Na frente no cômputo geral",
      valor: !kFrente ? `+${pct(margem, 2)} pp` : null,
    },
  ];

  const kColor = "#f59e0b";
  const sColor = "#3b82f6";

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="text-xs uppercase tracking-widest text-gray-500 mb-4">
        Razões para vitória
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Keiko */}
        <div className="rounded-xl bg-panel2 border border-hair p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-2.5 w-2.5 rounded-sm" style={{ background: kColor }} />
            <span className="text-sm font-semibold" style={{ color: kColor }}>
              {keiko.nome}
            </span>
            <span className="num text-xs text-gray-500 ml-auto">
              {pct(modelo.pVitoriaKeiko * 100, 0)} prob.
            </span>
          </div>
          <div className="space-y-2.5">
            {kItems.map((it, i) => (
              <Item key={i} {...it} />
            ))}
          </div>
        </div>

        {/* Sánchez */}
        <div className="rounded-xl bg-panel2 border border-hair p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-2.5 w-2.5 rounded-sm" style={{ background: sColor }} />
            <span className="text-sm font-semibold" style={{ color: sColor }}>
              {sanchez.nome}
            </span>
            <span className="num text-xs text-gray-500 ml-auto">
              {pct(modelo.pVitoriaSanchez * 100, 0)} prob.
            </span>
          </div>
          <div className="space-y-2.5">
            {sItems.map((it, i) => (
              <Item key={i} {...it} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
