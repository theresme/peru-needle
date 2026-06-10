// Bandeira do Peru em CSS (rojo-blanco-rojo). O emoji 🇵🇪 vira "PE" no
// Windows, então desenhamos as três faixas verticais na mão.
export default function Flag({ width = 30, height = 20, className = "" }) {
  return (
    <span
      className={`inline-flex overflow-hidden rounded-[3px] align-middle ${className}`}
      style={{ width, height, boxShadow: "0 0 0 1px rgba(255,255,255,0.15)" }}
      role="img"
      aria-label="Bandeira do Peru"
      title="Perú"
    >
      <span className="h-full flex-1" style={{ background: "#D91023" }} />
      <span className="h-full flex-1" style={{ background: "#f5efe4" }} />
      <span className="h-full flex-1" style={{ background: "#D91023" }} />
    </span>
  );
}
