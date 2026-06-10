import Flag from "./Flag";

export default function Footer() {
  return (
    <footer className="mt-10 border-t border-hair pt-5 text-xs leading-relaxed text-gray-500">
      <div className="mb-3 flex items-center gap-2">
        <Flag width={24} height={16} />
        <span className="uppercase tracking-[0.2em] text-[10px] text-gray-500">
          rojo y blanco · hecho para la jornada electoral
        </span>
      </div>
      <p>
        <strong className="text-gray-400">Projeção não-oficial</strong> baseada em dados da
        ONPE e em um modelo estatístico (Monte Carlo) calibrado com a 2ª volta de 2021. As
        probabilidades são estimativas, não previsões garantidas.
      </p>
      <p className="mt-1">
        O resultado oficial é proclamado pelo <strong className="text-gray-400">JNE</strong> em
        meados de julho. Este painel não tem vínculo com a ONPE, o JNE ou qualquer campanha.
      </p>
    </footer>
  );
}
