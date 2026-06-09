from __future__ import annotations

from .base import RawTally, RegionTally, Source


def get_source(name: str) -> Source:
    """Fábrica simples de fontes plugáveis."""
    name = (name or "mock").lower()
    if name == "onpe":
        from .onpe import OnpeSource

        return OnpeSource()
    if name == "mock":
        from .mock import MockSource

        return MockSource()
    raise ValueError(f"Fonte desconhecida: {name!r} (use 'onpe' ou 'mock')")


__all__ = ["get_source", "RawTally", "RegionTally", "Source"]
