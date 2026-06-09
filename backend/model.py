"""Modelo de probabilidade (a 'agulha') — versão impecável.

Princípios:
  1. Tudo ancorado nos dados OFICIAIS desta eleição (votos + atas por
     departamento + exterior). Sem médias de eleições passadas como centro.
  2. O lean do voto que ainda FALTA é estimado a partir de ONDE as atas
     pendentes estão: para o doméstico, soma-se o lean observado de cada
     departamento ponderado pelos VOTOS que ainda faltam ali. Para o exterior,
     usa-se o lean observado do exterior.
  3. A INCERTEZA cresce conforme cada âmbito está pouco apurado — separadamente.
     O exterior costuma estar ~95% por apurar → banda larga; o doméstico quase
     todo apurado → banda estreita. (As médias históricas entram só como
     fallback fraco quando NÃO há nenhum dado observado.)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

import config
from sources.base import RawTally, RegionTally


@dataclass
class ModelOutput:
    pVitoriaKeiko: float
    pVitoriaSanchez: float
    margemP10: float
    margemP50: float
    margemP90: float
    projFinalKeiko: float
    projFinalSanchez: float
    votosRestantesEstimados: int
    favorito: str
    pFavorito: float
    label: str
    # diagnósticos do "porquê" (impecável e auditável)
    leanRestanteDomSanchez: float   # % do doméstico restante p/ Sánchez
    leanRestanteExtKeiko: float     # % do exterior restante p/ Keiko
    votosRestantesDom: int
    votosRestantesExt: int
    # votação final esperada (faixas de incerteza + votos absolutos)
    projFinalKeikoP10: float
    projFinalKeikoP90: float
    projFinalSanchezP10: float
    projFinalSanchezP90: float
    projVotosKeiko: int
    projVotosSanchez: int
    projVotosKeikoP10: int
    projVotosKeikoP90: int
    projVotosSanchezP10: int
    projVotosSanchezP90: int
    projVotosTotal: int


def _truncated_normal(rng, mean, sd, lo, hi, n):
    return np.clip(rng.normal(mean, sd, n), lo, hi)


def _media_votos_por_acta(regs: list[RegionTally]) -> float:
    cont = sum(r.actas_contabilizadas for r in regs)
    votos = sum(r.vK + r.vS for r in regs)
    return (votos / cont) if cont > 0 else 0.0


def _pending_votes(r: RegionTally, media_fallback: float) -> float:
    """Votos válidos ainda por contar numa região = atas pendentes × média
    de votos/acta DA PRÓPRIA região (cai p/ a média global se a região ainda
    não tem atas contadas)."""
    pend_actas = max(0, r.actas_total - r.actas_contabilizadas)
    if pend_actas <= 0:
        return 0.0
    media = (r.vK + r.vS) / r.actas_contabilizadas if r.actas_contabilizadas > 0 else media_fallback
    return pend_actas * media


def _remaining_lean_for_sanchez(regs: list[RegionTally], media_fallback: float) -> tuple[float | None, float]:
    """Lean p/ Sánchez do voto restante de um conjunto de regiões, ponderado
    pelos VOTOS que ainda faltam em cada região (usa o lean observado de cada
    uma). Retorna (lean, total_votos_restantes)."""
    num = den = 0.0
    for r in regs:
        pv = _pending_votes(r, media_fallback)
        tot = r.vK + r.vS
        if pv <= 0 or tot <= 0:
            den += pv  # conta no total mesmo sem lean observado
            continue
        lean_s = r.vS / tot
        num += pv * lean_s
        den += pv
    if den <= 0:
        return None, 0.0
    # se nenhuma região com pendência tinha lean observado, num fica 0
    lean = (num / den) if num > 0 else None
    return lean, den


def run_model(tally: RawTally, cfg: config.ModelConfig = config.MODEL) -> ModelOutput:
    rng = np.random.default_rng()
    dom, ext = tally.split_dom_ext()

    media_dom = _media_votos_por_acta(dom) or 200.0
    media_ext = _media_votos_por_acta(ext) or media_dom

    # ----- votos restantes (oficiais) e lean observado por âmbito -----
    if dom or ext:
        lean_s_dom, rest_dom = _remaining_lean_for_sanchez(dom, media_dom)
        lean_s_ext, rest_ext = _remaining_lean_for_sanchez(ext, media_ext)
        lean_k_ext = (1.0 - lean_s_ext) if lean_s_ext is not None else None
    else:
        # sem desglose: trata tudo como doméstico, sem lean observado
        rest_actas = max(0, tally.actas_total - tally.actas_contabilizadas)
        rest_dom = rest_actas * media_dom
        rest_ext = 0.0
        lean_s_dom = None
        lean_k_ext = None

    # Centros dos leans: OBSERVADO desta eleição; histórico só como fallback
    # quando não há nenhum dado observado para o âmbito.
    lean_s_dom_mean = lean_s_dom if lean_s_dom is not None else cfg.lean_rural_mean
    lean_k_ext_mean = lean_k_ext if lean_k_ext is not None else cfg.lean_exterior_mean

    # ----- incerteza por âmbito: cresce com a fração NÃO apurada do âmbito ---
    counted_dom = sum(r.vK + r.vS for r in dom)
    counted_ext = sum(r.vK + r.vS for r in ext)
    frac_unc_dom = rest_dom / (counted_dom + rest_dom) if (counted_dom + rest_dom) > 0 else 0.0
    frac_unc_ext = rest_ext / (counted_ext + rest_ext) if (counted_ext + rest_ext) > 0 else 0.0

    # SD do lean: base × (1 + k·fração_não_apurada), com tetos sensatos.
    sd_dom = float(np.clip(cfg.lean_rural_sd * (1.0 + 2.0 * frac_unc_dom), 0.02, 0.08))
    sd_ext = float(np.clip(cfg.lean_exterior_sd * (1.0 + 3.0 * frac_unc_ext), 0.05, 0.10))

    # Ruído de comparecimento (quantos votos realmente vêm): exterior mais
    # volátil (abstenção alta e desconhecida).
    tn_dom = getattr(cfg, "turnout_noise_dom", 0.05)
    tn_ext = getattr(cfg, "turnout_noise_ext", 0.18)

    n = cfg.n_sims

    # ----- Monte Carlo --------------------------------------------------
    lean_s_dom_s = _truncated_normal(rng, lean_s_dom_mean, sd_dom, 0.20, 0.80, n)
    lean_k_ext_s = _truncated_normal(rng, lean_k_ext_mean, sd_ext, 0.20, 0.85, n)

    turn_dom = rng.normal(1.0, tn_dom, n).clip(0.6, 1.4)
    turn_ext = rng.normal(1.0, tn_ext, n).clip(0.3, 1.7)

    rd = rest_dom * turn_dom
    re = rest_ext * turn_ext

    k_dom = rd * (1.0 - lean_s_dom_s)
    s_dom = rd * lean_s_dom_s
    k_ext = re * lean_k_ext_s
    s_ext = re * (1.0 - lean_k_ext_s)

    final_k = tally.vK + k_dom + k_ext
    final_s = tally.vS + s_dom + s_ext
    total = np.maximum(final_k + final_s, 1.0)

    pct_k = 100.0 * final_k / total
    pct_s = 100.0 * final_s / total
    margem = pct_k - pct_s  # >0 => Keiko

    p_keiko = float(np.mean(margem > 0))
    p_sanchez = 1.0 - p_keiko
    q10, q50, q90 = np.percentile(margem, list(cfg.quantiles))

    favorito = "keiko" if p_keiko >= 0.5 else "sanchez"
    p_fav = max(p_keiko, p_sanchez)

    # ----- votação final esperada (percentis %) e votos absolutos -----
    kp10, kp50, kp90 = np.percentile(pct_k, [10, 50, 90])
    sp10, sp50, sp90 = np.percentile(pct_s, [10, 50, 90])
    vk10, vk50, vk90 = np.percentile(final_k, [10, 50, 90])
    vs10, vs50, vs90 = np.percentile(final_s, [10, 50, 90])
    vtot = float(np.median(total))

    return ModelOutput(
        pVitoriaKeiko=round(p_keiko, 4),
        pVitoriaSanchez=round(p_sanchez, 4),
        margemP10=round(float(q10), 2),
        margemP50=round(float(q50), 2),
        margemP90=round(float(q90), 2),
        projFinalKeiko=round(float(kp50), 2),
        projFinalSanchez=round(float(sp50), 2),
        votosRestantesEstimados=int(rest_dom + rest_ext),
        favorito=favorito,
        pFavorito=round(p_fav, 4),
        label=config.needle_label(p_fav),
        leanRestanteDomSanchez=round(100.0 * lean_s_dom_mean, 2),
        leanRestanteExtKeiko=round(100.0 * lean_k_ext_mean, 2),
        votosRestantesDom=int(rest_dom),
        votosRestantesExt=int(rest_ext),
        projFinalKeikoP10=round(float(kp10), 2),
        projFinalKeikoP90=round(float(kp90), 2),
        projFinalSanchezP10=round(float(sp10), 2),
        projFinalSanchezP90=round(float(sp90), 2),
        projVotosKeiko=int(vk50),
        projVotosSanchez=int(vs50),
        projVotosKeikoP10=int(vk10),
        projVotosKeikoP90=int(vk90),
        projVotosSanchezP10=int(vs10),
        projVotosSanchezP90=int(vs90),
        projVotosTotal=int(vtot),
    )


def model_to_dict(m: ModelOutput) -> dict:
    return asdict(m)
