"""Interface plugável de 'fonte' de dados de apuração.

Qualquer fonte (ONPE oficial, liveblog de fallback, mock) implementa
`fetch()` e devolve um `RawTally` normalizado. O resto do backend
(modelo + API) não sabe de onde os números vieram.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RegionTally:
    nombre: str
    vK: int
    vS: int
    actas_contabilizadas: int
    actas_total: int
    es_exterior: bool = False
    continente: str = ""  # só p/ países do exterior (ex.: "América")

    @property
    def pct_apurado(self) -> float:
        if self.actas_total <= 0:
            return 0.0
        return 100.0 * self.actas_contabilizadas / self.actas_total

    @property
    def lider(self) -> str:
        return "keiko" if self.vK >= self.vS else "sanchez"


@dataclass
class RawTally:
    """Snapshot normalizado de uma atualização da apuração."""

    vK: int
    vS: int

    actas_contabilizadas: int      # nacional (inclui exterior)
    actas_total: int
    actas_observadas: int = 0

    regiones: list[RegionTally] = field(default_factory=list)

    fuente: str = "desconhecida"

    # --- derivados -----------------------------------------------------
    @property
    def pct_apurado(self) -> float:
        if self.actas_total <= 0:
            return 0.0
        return 100.0 * self.actas_contabilizadas / self.actas_total

    @property
    def votos_validos(self) -> int:
        return self.vK + self.vS

    def split_dom_ext(self) -> tuple[list[RegionTally], list[RegionTally]]:
        dom = [r for r in self.regiones if not r.es_exterior]
        ext = [r for r in self.regiones if r.es_exterior]
        return dom, ext


class Source(Protocol):
    name: str

    async def fetch(self) -> RawTally:
        """Devolve o snapshot atual. Pode levantar exceção em falha."""
        ...
