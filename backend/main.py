"""API do painel.

- Faz polling da fonte (ONPE ou mock) a cada POLL_INTERVAL_SECONDS.
- Normaliza, roda o modelo de probabilidade, guarda em cache em memória.
- Expõe GET /api/state com o JSON consumido pelo frontend.
- Mantém um pequeno histórico (sparkline) das últimas N atualizações.
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from events import detectar_eventos
from model import model_to_dict, run_model
from sources import get_source
from sources.base import RawTally

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("painel")

HISTORY_MAX = 120  # ~ últimas 90 min a 45s


EVENTS_MAX = 80  # feed de acontecimentos


class StateCache:
    def __init__(self) -> None:
        self.state: dict | None = None
        self.history: deque[dict] = deque(maxlen=HISTORY_MAX)
        self.events: deque[dict] = deque(maxlen=EVENTS_MAX)  # mais novo à esquerda
        self.last_ok_ts: str | None = None
        self.last_error: str | None = None


cache = StateCache()


def _candidato_dict(c: config.Candidate, votos: int, total_validos: int, proj: float) -> dict:
    pct = round(100.0 * votos / total_validos, 2) if total_validos else 0.0
    return {
        "id": c.id,
        "nome": c.nome,
        "partido": c.partido,
        "cor": c.cor,
        "votos": votos,
        "pctAtual": pct,
        "projFinal": proj,
    }


def _ambito_block(regs) -> dict:
    """Resumo de um conjunto de regiões (doméstico ou exterior)."""
    contab = sum(r.actas_contabilizadas for r in regs)
    total = sum(r.actas_total for r in regs)
    vK = sum(r.vK for r in regs)
    vS = sum(r.vS for r in regs)
    validos = vK + vS
    media = (validos / contab) if contab else 0.0
    restantes_atas = max(0, total - contab)
    return {
        "contabilizadas": contab,
        "total": total,
        "restantes": restantes_atas,
        "pct": round(100.0 * contab / total, 2) if total else 0.0,
        "vK": vK,
        "vS": vS,
        "pctK": round(100.0 * vK / validos, 2) if validos else 0.0,
        "pctS": round(100.0 * vS / validos, 2) if validos else 0.0,
        "lider": "keiko" if vK >= vS else "sanchez",
        # votos válidos ainda por contar (estimativa: atas restantes × média)
        "votosRestantesEstimados": int(restantes_atas * media),
    }


def build_state(tally: RawTally) -> dict:
    model = run_model(tally)
    dom, ext = tally.split_dom_ext()

    dom_block = _ambito_block(dom)
    ext_block = _ambito_block(ext)

    ext_contab = ext_block["contabilizadas"]
    ext_total = ext_block["total"]
    ext_vK = ext_block["vK"]
    ext_vS = ext_block["vS"]

    total_validos = tally.votos_validos

    por_departamento = [
        {
            "nombre": r.nombre,
            "vK": r.vK,
            "vS": r.vS,
            "pctK": round(100.0 * r.vK / (r.vK + r.vS), 2) if (r.vK + r.vS) else 0.0,
            "pctS": round(100.0 * r.vS / (r.vK + r.vS), 2) if (r.vK + r.vS) else 0.0,
            "pctApurado": round(r.pct_apurado, 2),
            "lider": r.lider,
            "esExterior": r.es_exterior,
        }
        for r in sorted(tally.regiones, key=lambda x: -(x.vK + x.vS))
    ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fonte": tally.fuente,
        "vK": tally.vK,
        "vS": tally.vS,
        "pctApurado": round(tally.pct_apurado, 2),
        "candidatos": [
            _candidato_dict(config.KEIKO, tally.vK, total_validos, model.projFinalKeiko),
            _candidato_dict(config.SANCHEZ, tally.vS, total_validos, model.projFinalSanchez),
        ],
        "atas": {
            "contabilizadas": tally.actas_contabilizadas,
            "total": tally.actas_total,
            "observadas": tally.actas_observadas,
            "restantes": max(0, tally.actas_total - tally.actas_contabilizadas),
        },
        "domestico": dom_block,
        "exterior": {
            **ext_block,
            # compat: campos antigos mantidos
            "contabilizadas": ext_contab,
            "total": ext_total,
        },
        "porDepartamento": por_departamento,
        "modelo": model_to_dict(model),
    }


async def poll_once() -> None:
    source = get_source(config.SOURCE)
    try:
        tally = await source.fetch()
        state = build_state(tally)
        # detecta acontecimentos comparando com o snapshot anterior
        try:
            for ev in detectar_eventos(cache.state, state):
                cache.events.appendleft(ev)
        except Exception as exc:  # noqa: BLE001
            log.warning("falha ao detectar eventos: %s", exc)
        cache.state = state
        cache.last_ok_ts = state["timestamp"]
        cache.last_error = None
        cache.history.append(
            {
                "t": state["timestamp"],
                "pctApurado": state["pctApurado"],
                "pKeiko": state["modelo"]["pVitoriaKeiko"],
                "margemP50": state["modelo"]["margemP50"],
            }
        )
        log.info(
            "OK [%s] apurado=%.1f%% pKeiko=%.2f margem50=%.2f",
            state["fonte"], state["pctApurado"],
            state["modelo"]["pVitoriaKeiko"], state["modelo"]["margemP50"],
        )
    except Exception as exc:  # noqa: BLE001
        cache.last_error = str(exc)
        log.error("Falha no polling (mantendo último cache): %s", exc)


async def poll_loop() -> None:
    while True:
        await poll_once()
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await poll_once()  # primeira carga imediata
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


app = FastAPI(title="Painel 2ª volta Peru 2026", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend local; restrinja em produção
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/state")
async def get_state():
    if cache.state is None:
        return {
            "ready": False,
            "error": cache.last_error or "carregando primeira apuração…",
        }
    return {
        "ready": True,
        "lastOk": cache.last_ok_ts,
        "error": cache.last_error,
        "pollSeconds": config.POLL_INTERVAL_SECONDS,
        "eventos": list(cache.events)[:40],
        **cache.state,
    }


@app.get("/api/history")
async def get_history():
    return {"history": list(cache.history)}


@app.get("/api/health")
async def health():
    return {"ok": True, "fonte": config.SOURCE, "lastOk": cache.last_ok_ts}


# ---------------------------------------------------------------------------
# Servir o frontend buildado (produção). Em DEV não existe a pasta `static`,
# então o Vite continua servindo o front e este bloco fica inativo.
# IMPORTANTE: montar DEPOIS das rotas /api para não as sombrear.
# ---------------------------------------------------------------------------
import os  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="frontend")
    log.info("Servindo frontend estático de %s", _STATIC_DIR)
