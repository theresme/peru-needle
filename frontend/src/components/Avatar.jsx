import { useState } from "react";

// Quadrado com a foto do candidato (tenta png/jpg/jpeg/webp em /fotos/<id>.*)
// e cai nas iniciais se nenhuma existir. object-cover recorta qualquer
// proporção; object-position mira o rosto (geralmente no terço superior).
const EXTS = ["png", "jpg", "jpeg", "webp"];

export default function Avatar({ id, cor, iniciais, size = 48, radius = 12, ring = 2 }) {
  const [i, setI] = useState(0);
  const falhou = i >= EXTS.length;
  return (
    <div
      className="shrink-0 overflow-hidden flex items-center justify-center"
      style={{
        width: size,
        height: size,
        borderRadius: radius,
        background: `${cor}22`,
        boxShadow: `inset 0 0 0 ${ring}px ${cor}`,
      }}
    >
      {!falhou ? (
        <img
          src={`/fotos/${id}.${EXTS[i]}`}
          alt={iniciais}
          width={size}
          height={size}
          className="h-full w-full object-cover"
          style={{ objectPosition: "center 30%" }}
          onError={() => setI((n) => n + 1)}
        />
      ) : (
        <span className="num font-extrabold" style={{ color: cor, fontSize: size * 0.34 }}>
          {iniciais}
        </span>
      )}
    </div>
  );
}

// Helper: iniciais a partir do nome ("Keiko Fujimori" -> "KF").
export function iniciaisDe(nome = "") {
  return nome.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
}
