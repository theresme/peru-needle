"""Fonte MOCK: simula uma noite de apuração que evolui com o tempo.

Útil para desenvolver/demonstrar offline (a ONPE bloqueia CORS e, fora da
noite eleitoral, não tem dados). A apuração avança ~real: começa pelas
cidades (lean Keiko) e termina no rural + exterior, fazendo a agulha
"virar" como numa eleição de verdade.
"""
from __future__ import annotations

import math
import random
import time

from .base import RawTally, RegionTally

# Departamentos do Peru + exterior, com peso de eleitorado aproximado e um
# "lean final" plausível (fração p/ Keiko) só para gerar dados de demo.
_REGIONS = [
    # (nome, peso_eleitoral, lean_final_keiko, es_exterior)
    ("Lima", 0.34, 0.55, False),
    ("La Libertad", 0.06, 0.50, False),
    ("Piura", 0.06, 0.52, False),
    ("Cajamarca", 0.05, 0.30, False),
    ("Puno", 0.045, 0.18, False),
    ("Cusco", 0.045, 0.28, False),
    ("Arequipa", 0.05, 0.48, False),
    ("Junín", 0.04, 0.40, False),
    ("Lambayeque", 0.035, 0.49, False),
    ("Áncash", 0.035, 0.45, False),
    ("Loreto", 0.03, 0.42, False),
    ("Ica", 0.025, 0.56, False),
    ("Ayacucho", 0.02, 0.22, False),
    ("Huánuco", 0.02, 0.38, False),
    ("San Martín", 0.02, 0.44, False),
    ("Callao", 0.03, 0.54, False),
    ("Apurímac", 0.015, 0.20, False),
    ("Tacna", 0.015, 0.46, False),
    ("Otros departamentos", 0.10, 0.41, False),
    # --- Exterior, desglosado por país (peso ≈ tamanho da comunidade peruana;
    # lean_final = fração p/ Keiko: o voto do exterior tende à direita, mas
    # varia por destino). Soma dos pesos = 0.025, igual ao agregado anterior,
    # para preservar a calibração ~50/50 da demo.
    ("Chile", 0.0050, 0.58, True),
    ("Estados Unidos", 0.0045, 0.72, True),
    ("España", 0.0040, 0.70, True),
    ("Argentina", 0.0040, 0.55, True),
    ("Italia", 0.0030, 0.69, True),
    ("Japón", 0.0020, 0.71, True),
    ("Brasil", 0.0015, 0.60, True),
    ("Otros (exterior)", 0.0010, 0.66, True),
]

# Atas totais por região, proporcional ao peso.
_TOTAL_ACTAS = 90_000
_VOTOS_POR_ACTA = 200

# Desloca o resultado final do mock para ~50/50 (nail-biter de demonstração).
_BIAS_KEIKO = 0.045


class MockSource:
    name = "mock"

    def __init__(self, *, duracao_seg: float = 240.0, inicio_frac: float = 0.30) -> None:
        # A apuração completa "leva" duracao_seg; começa já em inicio_frac p/
        # a primeira carga mostrar dados interessantes (não 0%).
        # Padrão: 4 min totais, começa em 30% → agulha já vibrante no load.
        self._duracao = duracao_seg
        self._t0 = time.monotonic() - inicio_frac * duracao_seg
        self._rng = random.Random(2026)

    def _progress(self) -> float:
        # curva: rápido no começo, devagar no fim (cauda rural/exterior).
        frac = min(1.0, (time.monotonic() - self._t0) / self._duracao)
        return 1.0 - (1.0 - frac) ** 1.6

    async def fetch(self) -> RawTally:
        prog = self._progress()
        regiones: list[RegionTally] = []
        tot_actas_nac = 0
        cont_actas_nac = 0
        vK = vS = 0

        for nome, peso, lean_k, ext in _REGIONS:
            actas_total = max(1, round(_TOTAL_ACTAS * peso))
            # Regiões urbanas/exterior contam mais devagar no fim;
            # damos um "atraso" para o rural e o exterior.
            atraso = 0.35 if (lean_k < 0.4 or ext) else 0.0
            reg_prog = max(0.0, min(1.0, (prog - atraso) / (1.0 - atraso + 1e-9)))
            # leve ruído por região
            reg_prog *= 1.0 - 0.05 * self._rng.random()
            contab = round(actas_total * reg_prog)

            votos = contab * _VOTOS_POR_ACTA
            lean_k = min(0.95, lean_k + (0.0 if ext else _BIAS_KEIKO))
            rk = votos * lean_k
            rs = votos - rk
            # ruído pequeno
            rk = int(rk * (1 + 0.01 * (self._rng.random() - 0.5)))
            rs = int(rs * (1 + 0.01 * (self._rng.random() - 0.5)))

            regiones.append(
                RegionTally(
                    nombre=nome,
                    vK=rk,
                    vS=rs,
                    actas_contabilizadas=contab,
                    actas_total=actas_total,
                    es_exterior=ext,
                )
            )
            vK += rk
            vS += rs
            tot_actas_nac += actas_total
            cont_actas_nac += contab

        observadas = round(cont_actas_nac * 0.012)  # ~1.2% observadas

        return RawTally(
            vK=vK,
            vS=vS,
            actas_contabilizadas=cont_actas_nac,
            actas_total=tot_actas_nac,
            actas_observadas=observadas,
            regiones=regiones,
            fuente="mock",
        )
