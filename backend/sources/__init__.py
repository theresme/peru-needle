from __future__ import annotations

from .base import RawTally, RegionTally, Source


# Cache de instâncias: a fonte é criada UMA vez e reutilizada entre polls.
# Importante p/ o mock (que simula a passagem do tempo via estado interno);
# sem isso ele seria recriado a cada poll e a apuração nunca avançaria.
_INSTANCES: dict[str, Source] = {}


def get_source(name: str) -> Source:
    """Fábrica de fontes plugáveis (instância única por nome)."""
    name = (name or "mock").lower()
    if name in _INSTANCES:
        return _INSTANCES[name]
    if name == "onpe":
        from .onpe import OnpeSource

        src: Source = OnpeSource()
    elif name == "mock":
        from .mock import MockSource

        src = MockSource()
    else:
        raise ValueError(f"Fonte desconhecida: {name!r} (use 'onpe' ou 'mock')")
    _INSTANCES[name] = src
    return src


__all__ = ["get_source", "RawTally", "RegionTally", "Source"]
