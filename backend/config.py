"""
Configuração central do painel — TUDO que o modelo usa é ajustável aqui.

Calibrado com referências da 2ª volta de 2021 (Castillo x Keiko), que é a
melhor análoga disponível para o comportamento do voto rural/esquerda e do
voto do exterior/direita no Peru.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Fonte de dados
# ---------------------------------------------------------------------------
# "mock"  -> simulador que evolui a apuração ao longo do tempo (demo/offline)
# "onpe"  -> adapter da API oficial da ONPE (precisa do endpoint real, ver README)
SOURCE: str = os.getenv("SOURCE", "mock")

# Endpoint JSON interno da ONPE. PRECISA ser descoberto no DevTools (ver README).
# Deixe como placeholder; quando achar o endpoint real, coloque aqui ou via env.
ONPE_RESUMEN_URL: str = os.getenv(
    "ONPE_RESUMEN_URL",
    "https://resultadosegundavuelta.onpe.gob.pe/main/resumen",
)
ONPE_DETALLE_URL: str = os.getenv(
    "ONPE_DETALLE_URL",
    "",  # endpoint do desglose por circunscrição (se separado)
)

# Intervalo de polling do backend contra a ONPE (segundos). NÃO martelar.
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# User-Agent honesto.
USER_AGENT: str = os.getenv(
    "USER_AGENT",
    "peru-needle/1.0 (painel editorial nao-oficial; contato: voce@exemplo.com)",
)

REQUEST_TIMEOUT: float = 15.0
RETRY_MAX: int = 4
RETRY_BACKOFF_BASE: float = 1.8  # segundos: base^tentativa


# ---------------------------------------------------------------------------
# Candidatos
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Candidate:
    id: str
    nome: str
    partido: str
    cor: str  # cor de marca (hex)


KEIKO = Candidate("keiko", "Keiko Fujimori", "Fuerza Popular", "#f59e0b")   # âmbar
SANCHEZ = Candidate("sanchez", "Roberto Sánchez", "Juntos por el Perú", "#3b82f6")  # azul


# ---------------------------------------------------------------------------
# Parâmetros do modelo de probabilidade (Monte Carlo)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelConfig:
    n_sims: int = 20_000

    # Lean do voto DOMÉSTICO que ainda falta apurar -> fração que vai p/ Sánchez
    # (esquerda historicamente forte no voto rural/serra apurado por último).
    lean_rural_mean: float = 0.67
    lean_rural_sd: float = 0.04
    lean_rural_min: float = 0.50
    lean_rural_max: float = 0.85

    # Lean do voto do EXTERIOR -> fração que vai p/ Keiko (direita).
    # 0.665 ~ valor observado em 2021.
    lean_exterior_mean: float = 0.665
    lean_exterior_sd: float = 0.05
    lean_exterior_min: float = 0.50
    lean_exterior_max: float = 0.90

    # Ruído sobre o TOTAL de votos restantes (incerteza de comparecimento/anuladas).
    turnout_noise: float = 0.15  # ±15% (fallback)
    turnout_noise_dom: float = 0.05   # doméstico: quase todo apurado, baixa incerteza
    turnout_noise_ext: float = 0.18   # exterior: abstenção alta e desconhecida

    # Se a API der lean por departamento, preferir o lean observado de cada
    # região ainda não 100% apurada (bem melhor que o número global).
    use_regional_lean: bool = True

    # Percentis da margem final reportados.
    quantiles: tuple[float, float, float] = (10.0, 50.0, 90.0)


MODEL = ModelConfig()


# ---------------------------------------------------------------------------
# Faixas de confiança da agulha (rótulos "Toss-up / Leans / Likely / Solid")
# a partir da probabilidade do favorito (0..1).
# ---------------------------------------------------------------------------
def needle_label(p_favorito: float) -> str:
    """Rótulo editorial estilo NYT a partir da prob. do favorito (0..1)."""
    if p_favorito < 0.60:
        return "Toss-up"
    if p_favorito < 0.75:
        return "Leans"
    if p_favorito < 0.90:
        return "Likely"
    return "Solid"
