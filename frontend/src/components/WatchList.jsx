import { pct, int } from "../format";

const COLORS = { keiko: "#f59e0b", sanchez: "#3b82f6" };
const NOMES = { keiko: "Keiko", sanchez: "Sánchez" };

// Peso eleitoral aproximado por departamento (% do eleitorado nacional).
// Usado para estimar votos restantes e ranquear quão importante é a região.
const DEPT_WEIGHT = {
  "Lima": 0.32,
  "La Libertad": 0.06,
  "Piura": 0.06,
  "Cajamarca": 0.05,
  "Puno": 0.045,
  "Cusco": 0.045,
  "Arequipa": 0.05,
  "Junín": 0.04,
  "Lambayeque": 0.035,
  "Áncash": 0.035,
  "Loreto": 0.03,
  "Callao": 0.03,
  "Ica": 0.025,
  "Ayacucho": 0.02,
  "Huánuco": 0.02,
  "San Martín": 0.02,
  "Peruanos en el Extranjero": 0.045,
};

function importancia(r) {
  // Quanto essa região pode mudar o resultado: votos restantes × diferencial de lean
  const frac_restante = Math.max(0, (100 - r.pctApurado) / 100);
  const peso = DEPT_WEIGHT[r.nombre] ?? 0.01;
  const lean_diff = Math.abs(r.pctK - r.pctS) / 100;
  return frac_restante * peso * (1 + lean_diff);
}

function narrativa(r) {
  const falta = Math.round(100 - r.pctApurado);
  const lider = r.lider === "keiko" ? "Keiko" : "Sánchez";
  const margem = Math.abs(r.pctK - r.pctS).toFixed(1);
  if (r.esExterior) return `Voto do exterior tende à direita (+${margem} pp histór.); ${falta}% sem apurar`;
  if (falta > 30) return `${falta}% ainda por apurar — ${lider} lidera c/ ${margem} pp de margem`;
  return `${falta}% por apurar — ${lider} lidera localmente (${margem} pp)`;
}

export default function WatchList({ rows, exterior }) {
  if (!rows?.length) return null;

  // Filtra regiões com dados e ainda com votos por contar (>3% restante)
  const candidates = rows.filter(
    (r) => r.vK + r.vS > 0 && r.pctApurado < 97
  );

  // Ordena por impacto potencial
  const sorted = [...candidates].sort((a, b) => importancia(b) - importancia(a));
  const items = sorted.slice(0, 5);

  if (items.length === 0) return null;

  return (
    <div className="rounded-2xl bg-panel border border-hair p-5 fade-in">
      <div className="text-xs uppercase tracking-widest text-gray-500 mb-4">
        Manter o olho em
      </div>

      <div className="space-y-3">
        {items.map((r) => {
          const lc = COLORS[r.lider];
          const frac_falta = (100 - r.pctApurado) / 100;
          return (
            <div key={r.nombre} className="rounded-xl bg-panel2 border border-hair p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-100 text-sm truncate">
                      {r.nombre}
                    </span>
                    {r.esExterior && (
                      <span className="text-[10px] uppercase text-amber-300/80 shrink-0">
                        exterior
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-gray-400 leading-relaxed">
                    {narrativa(r)}
                  </p>
                </div>

                <div className="shrink-0 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <span
                      className="inline-block h-2 w-2 rounded-sm"
                      style={{ background: lc }}
                    />
                    <span className="num text-sm font-semibold" style={{ color: lc }}>
                      {NOMES[r.lider]} {pct(Math.max(r.pctK, r.pctS), 1)}
                    </span>
                  </div>
                  <div className="num text-xs text-gray-500 mt-0.5">
                    {pct(r.pctApurado, 0)} apurado
                  </div>
                  {/* barra de progresso */}
                  <div className="mt-1.5 h-1 w-16 rounded-full bg-hair overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${r.pctApurado}%`, background: lc + "88" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
