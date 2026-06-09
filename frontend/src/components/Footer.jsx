export default function Footer() {
  return (
    <footer className="mt-10 border-t border-hair pt-5 text-xs leading-relaxed text-gray-500">
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
