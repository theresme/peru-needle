import { useEffect, useRef, useState } from "react";

// Anima a transição entre valores numéricos (ease-out cúbico).
// Uso: const n = useCountUp(votos); render int(n).
export function useCountUp(value, duration = 700) {
  const [display, setDisplay] = useState(value ?? 0);
  const fromRef = useRef(value ?? 0);

  useEffect(() => {
    const from = fromRef.current;
    const to = value ?? 0;
    if (from === to) return;
    let raf;
    const t0 = performance.now();
    const ease = (x) => 1 - Math.pow(1 - x, 3);
    const loop = (now) => {
      const k = Math.min(1, (now - t0) / duration);
      setDisplay(from + (to - from) * ease(k));
      if (k < 1) {
        raf = requestAnimationFrame(loop);
      } else {
        fromRef.current = to;
      }
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      fromRef.current = to;
    };
  }, [value, duration]);

  return display;
}
