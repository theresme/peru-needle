import { useState } from "react";
import { int, pct } from "../format";

const COLORS = { keiko: "#f59e0b", sanchez: "#3b82f6" };
const NOMES = { keiko: "Keiko", sanchez: "Sánchez" };

export default function DepartmentTable({ rows }) {
  const [sort, setSort] = useState({ key: "votos", dir: -1 });
  if (!rows?.length) return null;

  // Remove rows com zero votos (ubigeos não mapeados ou sem dados na amostra)
  const filtered = rows.filter((r) => r.vK + r.vS > 0);

  const sorted = [...filtered].sort((a, b) => {
    const dir = sort.dir;
    switch (sort.key) {
      case "nombre":
        return dir * a.nombre.localeCompare(b.nombre);
      case "apurado":
        return dir * (a.pctApurado - b.pctApurado);
      case "margem":
        return dir * (a.pctK - a.pctS - (b.pctK - b.pctS));
      default:
        return dir * (a.vK + a.vS - (b.vK + b.vS));
    }
  });

  const th = (key, label, align = "left") => (
    <th
      className={`py-2 px-3 text-${align} cursor-pointer select-none hover:text-gray-200`}
      onClick={() =>
        setSort((s) => ({ key, dir: s.key === key ? -s.dir : -1 }))
      }
    >
      {label}
      {sort.key === key && <span className="text-gray-500"> {sort.dir < 0 ? "▼" : "▲"}</span>}
    </th>
  );

  return (
    <div className="rounded-2xl bg-panel border border-hair p-2 sm:p-4 fade-in">
      <div className="px-2 pt-2 pb-3 text-sm font-semibold text-gray-200">
        Por circunscrição
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-xs uppercase tracking-wider text-gray-500 border-b border-hair">
            <tr>
              {th("nombre", "Região")}
              {th("margem", "Líder")}
              {th("votos", "Votos", "right")}
              {th("apurado", "% apurado", "right")}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => {
              const lc = COLORS[r.lider];
              return (
                <tr key={r.nombre} className="border-b border-hair/50 last:border-0">
                  <td className="py-2 px-3">
                    <span className="text-gray-200">{r.nombre}</span>
                    {r.esExterior && (
                      <span className="ml-2 text-[10px] uppercase text-amber-300/80">exterior</span>
                    )}
                  </td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: lc }} />
                      <span style={{ color: lc }}>{NOMES[r.lider]}</span>
                      <span className="num text-gray-400">
                        {pct(Math.max(r.pctK, r.pctS), 1)}
                      </span>
                    </div>
                  </td>
                  <td className="py-2 px-3 text-right num text-gray-300">{int(r.vK + r.vS)}</td>
                  <td className="py-2 px-3 text-right num text-gray-400">{pct(r.pctApurado, 1)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
