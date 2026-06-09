// Formatação pt-BR para números grandes e percentuais (ponto = milhar).
const nf = new Intl.NumberFormat("pt-BR");

export const int = (n) => nf.format(Math.round(n ?? 0));

export const pct = (n, dec = 1) =>
  `${(n ?? 0).toLocaleString("pt-BR", {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  })}%`;

// margem com sinal e cor implícita pelo chamador
export const signedPct = (n, dec = 1) =>
  `${n >= 0 ? "+" : ""}${(n ?? 0).toLocaleString("pt-BR", {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  })}`;
