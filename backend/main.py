"""API do painel.

- Faz polling da fonte (ONPE ou mock) a cada POLL_INTERVAL_SECONDS.
- Normaliza, roda o modelo de probabilidade, guarda em cache em memória.
- Expõe GET /api/state com o JSON consumido pelo frontend.
- Mantém um pequeno histórico (sparkline) das últimas N atualizações.
"""
from __future__ import annotations

import asyncio
import logging
import math
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

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

    # desglose do exterior por país (só publica se houver quebra real)
    media_ext = ((ext_vK + ext_vS) / ext_contab) if ext_contab else 0.0
    exterior_paises = []
    if len(ext) > 1:
        for r in sorted(ext, key=lambda x: -(x.vK + x.vS)):
            validos = r.vK + r.vS
            restantes = max(0, r.actas_total - r.actas_contabilizadas)
            vpa = (validos / r.actas_contabilizadas) if r.actas_contabilizadas else media_ext
            exterior_paises.append({
                "nombre": r.nombre,
                "continente": r.continente,
                "vK": r.vK,
                "vS": r.vS,
                "pctK": round(100.0 * r.vK / validos, 2) if validos else 0.0,
                "pctS": round(100.0 * r.vS / validos, 2) if validos else 0.0,
                "lider": r.lider,
                "atasContabilizadas": r.actas_contabilizadas,
                "atasTotal": r.actas_total,
                "atasRestantes": restantes,
                "pctApurado": round(r.pct_apurado, 2),
                "votosRestantesEstimados": int(restantes * vpa),
            })

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
        "exteriorPaises": exterior_paises,
        "porDepartamento": por_departamento,
        "modelo": model_to_dict(model),
    }


MOMENTUM_JANELA_MIN = 60  # janela alvo p/ "última hora"


def compute_last_hour(history: deque, cur: dict) -> dict:
    """Variação de votos/participação na última hora (ou no maior intervalo
    disponível, se ainda não houver 1h de dados). Define quem está SUBINDO."""
    base = {"janelaMin": MOMENTUM_JANELA_MIN, "spanMin": 0, "suficiente": False,
            "subindo": None, "deltaVotosK": 0, "deltaVotosS": 0,
            "deltaVotosTotal": 0, "deltaPctK": 0.0, "splitK": 0.0, "splitS": 0.0}
    if not history:
        return base

    now = cur["t"]
    alvo = now - timedelta(minutes=MOMENTUM_JANELA_MIN)
    ref = None
    for h in history:  # deque: mais antigo → mais novo
        try:
            ht = datetime.fromisoformat(h["t"])
        except Exception:  # noqa: BLE001
            continue
        if ht <= alvo:
            ref = h            # mantém o mais NOVO que ainda é ≥1h atrás
    if ref is None:
        ref = history[0]       # ainda não há 1h: usa o ponto mais antigo

    ht = datetime.fromisoformat(ref["t"])
    span = (now - ht).total_seconds() / 60.0
    dK = cur["vK"] - ref.get("vK", cur["vK"])
    dS = cur["vS"] - ref.get("vS", cur["vS"])
    dpK = cur["pctK"] - ref.get("pctK", cur["pctK"])
    tot = dK + dS

    splitK = (100.0 * dK / tot) if tot > 0 else 0.0
    splitS = (100.0 * dS / tot) if tot > 0 else 0.0

    # Quem está SUBINDO = quem leva, nos votos recentes, uma fatia acima da sua
    # média atual. Esse sinal é sensível mesmo no fim da apuração (quando a %
    # nacional quase não se mexe), porque compara o ritmo recente com o acumulado.
    pctK_atual = cur.get("pctK", 50.0)
    subindo = None
    if tot > 0:
        if splitK > pctK_atual + 0.5:
            subindo = "keiko"
        elif splitK < pctK_atual - 0.5:
            subindo = "sanchez"

    base.update({
        "spanMin": round(span),
        "suficiente": span >= 3 and tot > 0,
        "deltaVotosK": int(dK),
        "deltaVotosS": int(dS),
        "deltaVotosTotal": int(tot),
        "deltaPctK": round(dpK, 3),
        "subindo": subindo,
        "splitK": round(splitK, 1),
        "splitS": round(splitS, 1),
        # "vantagem" = quanto a fatia recente supera a média atual (pp)
        "vantagemK": round(splitK - pctK_atual, 1),
        "vantagemS": round(splitS - (100.0 - pctK_atual), 1),
    })
    return base


def compute_virada(history: deque, cur: dict, modelo: dict) -> dict:
    """'Conta-giro' da virada: quanto falta p/ o gap zerar, saldo de votos
    restante a favor de cada um, e ETA ao vivo se houver ritmo de contagem."""
    gap = cur["vK"] - cur["vS"]          # <0 => Sánchez na frente
    quem_atras = "keiko" if gap < 0 else ("sanchez" if gap > 0 else None)
    faltam = abs(gap) if gap < 0 else 0

    rd = modelo.get("votosRestantesDom", 0)
    re = modelo.get("votosRestantesExt", 0)
    ls = modelo.get("leanRestanteDomSanchez", 50.0) / 100.0
    lk = modelo.get("leanRestanteExtKeiko", 50.0) / 100.0
    net_dom = rd * (1.0 - 2.0 * ls)      # >0 favorece Keiko
    net_ext = re * (2.0 * lk - 1.0)
    net_total = net_dom + net_ext        # saldo líquido p/ Keiko no que falta

    net_atras = net_total if quem_atras == "keiko" else (-net_total if quem_atras == "sanchez" else 0)
    projeta_virar = quem_atras is not None and net_atras > faltam

    # ritmo ativo (net Keiko/min) na última janela + detecção de pausa
    pts = [(datetime.fromisoformat(h["t"]), h["vK"], h["vS"]) for h in history if "vK" in h]
    now = cur["t"]
    allpts = pts + [(now, cur["vK"], cur["vS"])]
    last_move = None
    for i in range(len(allpts) - 1, 0, -1):
        if (allpts[i][1] + allpts[i][2]) != (allpts[i - 1][1] + allpts[i - 1][2]):
            last_move = allpts[i][0]
            break
    min_sem_mov = (now - last_move).total_seconds() / 60.0 if last_move else None

    netps = None
    tot_net = tot_min = 0.0
    recent = [p for p in allpts if (now - p[0]).total_seconds() <= 45 * 60]
    for i in range(1, len(recent)):
        dv = (recent[i][1] + recent[i][2]) - (recent[i - 1][1] + recent[i - 1][2])
        if dv > 0:
            tot_min += (recent[i][0] - recent[i - 1][0]).total_seconds() / 60.0
            tot_net += (recent[i][1] - recent[i - 1][1]) - (recent[i][2] - recent[i - 1][2])
    if tot_min >= 1:
        netps = tot_net / tot_min

    pausada = (min_sem_mov is None) or (min_sem_mov > 6)
    eta_min = eta_iso = None
    if quem_atras and not pausada and netps is not None:
        rate_close = netps if quem_atras == "keiko" else -netps
        if rate_close > 5:
            eta_min = faltam / rate_close
            eta_iso = (now + timedelta(minutes=eta_min)).isoformat()

    estado = "virou" if gap >= 0 else ("pausada" if pausada else "contando")
    return {
        "estado": estado,
        "quemAtras": quem_atras,
        "quemFrente": "sanchez" if quem_atras == "keiko" else ("keiko" if quem_atras == "sanchez" else None),
        "gapAtual": int(abs(gap)),
        "faltamParaVirar": int(faltam),
        "saldoRestante": int(net_total),     # >0 favorece Keiko
        "saldoDom": int(net_dom),
        "saldoExt": int(net_ext),
        "projetaVirar": bool(projeta_virar),
        "minSemMovimento": round(min_sem_mov) if min_sem_mov is not None else None,
        "ritmoNetMin": round(netps) if netps is not None else None,
        "etaMin": round(eta_min) if eta_min is not None else None,
        "etaISO": eta_iso,
    }


def compute_eleito(state: dict) -> dict:
    """'Matematicamente eleito?': verdade dura, não probabilidade.

    Um candidato está MATEMATICAMENTE eleito quando, mesmo que TODOS os votos
    que ainda podem entrar fossem para o adversário, ele continuaria à frente.
    Teto duro do que falta = atas pendentes × máx. votos por ata (mesa).

    Também calcula o "número mágico": quantos dos votos restantes (estimados)
    o líder precisa garantir para cravar, e o que o perseguidor precisaria.
    """
    cands = state.get("candidatos", [])
    if len(cands) < 2:
        return {"estado": "indefinido"}
    k = next((c for c in cands if c["id"] == "keiko"), cands[0])
    s = next((c for c in cands if c["id"] == "sanchez"), cands[1])
    lider, atras = (k, s) if k["votos"] >= s["votos"] else (s, k)
    gap = lider["votos"] - atras["votos"]

    atas = state.get("atas", {})
    atas_rest = max(0, atas.get("restantes", 0))
    atas_obs = atas.get("observadas", 0) or 0
    # teto ABSOLUTO de votos que ainda podem entrar (pior caso p/ o líder):
    # toda ata pendente lotada (300) indo inteira para o perseguidor.
    max_reversivel = (atas_rest + atas_obs) * config.MAX_VOTOS_POR_ACTA

    eleito = gap > max_reversivel

    # número mágico (realista): líder precisa de x dos R votos estimados p/
    # ficar à frente mesmo que o resto vá pro adversário:
    #   (vL+x) > (vA + R - x)  ->  x > (R - gap)/2
    rest_est = max(0, state.get("modelo", {}).get("votosRestantesEstimados", 0))
    precisa_lider = max(0, math.ceil((rest_est - gap) / 2)) if rest_est else 0
    precisa_lider = min(precisa_lider, rest_est)
    # quanto o perseguidor precisaria capturar p/ virar (e ainda dá tempo?)
    precisa_atras = rest_est - precisa_lider  # complemento: o resto todo + reverter o gap

    pct_apurado = state.get("pctApurado", 0)
    return {
        "estado": "eleito" if eleito else "em_aberto",
        "quem": lider["id"],
        "perdedor": atras["id"],
        "gap": int(gap),
        "pctApurado": pct_apurado,
        "atasRestantes": int(atas_rest),
        "atasObservadas": int(atas_obs),
        "maxReversivel": int(max_reversivel),   # votos máx. que o líder poderia perder p/ o outro
        "votosRestEstimados": int(rest_est),
        "faltamParaCravar": int(precisa_lider),       # líder: votos a garantir do restante
        "faltamPctParaCravar": round(100.0 * precisa_lider / rest_est, 4) if rest_est else 0.0,
        "perseguidorPrecisa": int(precisa_atras),     # perseguidor: votos do restante p/ virar
        "perseguidorPrecisaPct": round(100.0 * precisa_atras / rest_est, 4) if rest_est else 0.0,
        # quantos % do restante seria necessário (>100% = impossível pela estimativa)
        "reversivelNaEstimativa": precisa_atras <= rest_est and precisa_atras > 0,
    }


async def poll_once() -> None:
    source = get_source(config.SOURCE)
    try:
        tally = await source.fetch()
        state = build_state(tally)
        # momentum: variação de votos na última hora (usa histórico anterior)
        cur = {
            "t": datetime.fromisoformat(state["timestamp"]),
            "vK": state["vK"], "vS": state["vS"],
            "pctK": state["candidatos"][0]["pctAtual"],
        }
        state["ultimaHora"] = compute_last_hour(cache.history, cur)
        state["virada"] = compute_virada(cache.history, cur, state["modelo"])
        state["eleito"] = compute_eleito(state)
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
                "vK": state["vK"],
                "vS": state["vS"],
                "pctK": state["candidatos"][0]["pctAtual"],
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


class SmartStatic(StaticFiles):
    """Serve o frontend com cache inteligente:
    - /assets/* (nomes com hash, imutáveis) → cache longo (1 ano)
    - resto, inclusive index.html → no-cache (revalida sempre)
    Assim toda atualização aparece na hora, sem Ctrl+Shift+R, mas o navegador
    ainda reaproveita os bundles pesados que não mudaram.
    """
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        try:
            norm = path.replace("\\", "/")  # Windows normpath usa "\"
            if norm.startswith("assets/"):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                resp.headers["Cache-Control"] = "no-cache, must-revalidate"
        except Exception:  # noqa: BLE001
            pass
        return resp


_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", SmartStatic(directory=_STATIC_DIR, html=True), name="frontend")
    log.info("Servindo frontend estático de %s", _STATIC_DIR)
