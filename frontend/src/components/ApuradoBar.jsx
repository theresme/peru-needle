// Barra fininha colada no topo da janela mostrando o avanço da apuração.
export default function ApuradoBar({ pctApurado }) {
  if (pctApurado == null) return null;
  return (
    <div
      className="fixed inset-x-0 top-0 z-[60] h-[3px] bg-panel2/60 pointer-events-none"
      title={`${pctApurado}% apurado`}
    >
      <div
        className="h-full bg-gradient-to-r from-perudark via-peru to-crema transition-[width] duration-1000"
        style={{ width: `${Math.min(100, pctApurado)}%`, boxShadow: "0 0 8px #D9102388" }}
      />
    </div>
  );
}
