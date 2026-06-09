"""Adapter da API oficial da ONPE — segunda vuelta presidencial 2026.

DESCOBERTA-CHAVE (jun/2026):
  O portal é uma SPA Angular que consome a API via POST. O CloudFront da ONPE
  roteia GET → origem (backend real) mas POST → S3 (devolve o index.html).
  Replicando as MESMAS chamadas como **GET com query params** obtemos o JSON
  oficial direto da origem. Sem fingerprint Chrome (curl_cffi
  impersonate="chrome124" + UA Chrome) a ONPE devolve a SPA em vez de JSON.

Tudo OFICIAL, sem amostragem:
  • resumen-general/mapa-calor?codigoAgrupacionPolitica={8|10}&idAmbitoGeografico=1
        &tipoFiltro=ambito_geografico
      → para CADA um dos 25 departamentos: votos do candidato, atas
        contabilizadas e % de atas apuradas. Duas chamadas (Keiko=8, Sánchez=10)
        dão o quadro doméstico completo por departamento.
  • resumen-general/{participantes,totales}?idAmbitoGeografico=2&tipoFiltro=ambito_geografico
      → votos e atas do EXTERIOR (idAmbitoGeografico: 1=Peru, 2=exterior).

Com isso o RawTally carrega votos + atas OFICIAIS por região, e o modelo
calcula o lean do voto restante a partir de ONDE as atas pendentes estão
(não de médias históricas).

Party IDs: 8 = Fuerza Popular (Keiko) · 10 = Juntos por el Perú (Sánchez).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import config

try:
    from curl_cffi.requests import AsyncSession as CurlSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

from .base import RawTally, RegionTally

log = logging.getLogger("onpe")

BASE = "https://resultadosegundavuelta.onpe.gob.pe/presentacion-backend"

ID_FUERZA_POPULAR = 8    # Keiko Fujimori
ID_JUNTOS_PERU = 10      # Roberto Sánchez

AMBITO_NACIONAL = 1      # Peru (doméstico)
AMBITO_EXTRANJERO = 2    # Exterior

# ubigeoNivel01 do mapa-calor = código do departamento × 10000.
_DEPT_NOME: dict[int, str] = {
    1: "Amazonas", 2: "Áncash", 3: "Apurímac", 4: "Arequipa", 5: "Ayacucho",
    6: "Cajamarca", 7: "Callao", 8: "Cusco", 9: "Huancavelica", 10: "Huánuco",
    11: "Ica", 12: "Junín", 13: "La Libertad", 14: "Lambayeque", 15: "Lima",
    16: "Loreto", 17: "Madre de Dios", 18: "Moquegua", 19: "Pasco", 20: "Piura",
    21: "Puno", 22: "San Martín", 23: "Tacna", 24: "Tumbes", 25: "Ucayali",
}


@dataclass
class _Ambito:
    vK: int
    vS: int
    actas_contabilizadas: int
    actas_total: int
    actas_enviadas_jee: int


class OnpeSource:
    name = "onpe"

    _CHROME_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        if not HAS_CURL_CFFI:
            raise RuntimeError(
                "curl_cffi não encontrado. Instale com: pip install curl_cffi"
            )
        self._headers = {
            "User-Agent": self._CHROME_UA,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://resultadosegundavuelta.onpe.gob.pe",
            "Referer": "https://resultadosegundavuelta.onpe.gob.pe/main/presidenciales",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
        }
        self._id_eleccion = 10  # presidencial

    async def _get_json(self, session, path, params):
        r = await session.get(
            f"{BASE}/{path}", headers=self._headers, params=params,
            timeout=config.REQUEST_TIMEOUT,
        )
        if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
            raise RuntimeError(f"{path} inválido: HTTP {r.status_code}")
        return r.json().get("data")

    # ------------------------------------------------------------------ #
    # Doméstico: mapa-calor por departamento (oficial)                   #
    # ------------------------------------------------------------------ #
    async def _fetch_mapa(self, session, party: int) -> dict[int, dict]:
        """{cod_depto: {votos, actas_contab, pct_actas}} para um candidato."""
        data = await self._get_json(session, "resumen-general/mapa-calor", {
            "idEleccion": self._id_eleccion,
            "codigoAgrupacionPolitica": party,
            "idAmbitoGeografico": AMBITO_NACIONAL,
            "tipoFiltro": "ambito_geografico",
            "ubigeoNivel01": "", "ubigeoNivel02": "", "ubigeoNivel03": "",
        })
        out: dict[int, dict] = {}
        for it in data or []:
            code = (it.get("ubigeoNivel01") or 0) // 10000
            if code <= 0:
                continue
            out[code] = {
                "votos": it["participante"]["totalVotosValidos"],
                "actas_contab": it["actasContabilizadas"],
                "pct_actas": it["porcentajeActasContabilizadas"],
            }
        return out

    # ------------------------------------------------------------------ #
    # Exterior: participantes + totales (oficial)                        #
    # ------------------------------------------------------------------ #
    async def _fetch_ambito(self, session, ambito: int) -> _Ambito:
        params = {
            "idEleccion": self._id_eleccion,
            "tipoFiltro": "ambito_geografico",
            "idAmbitoGeografico": ambito,
        }
        cand = await self._get_json(session, "resumen-general/participantes", params)
        tot = await self._get_json(session, "resumen-general/totales", params)
        vK = vS = 0
        for c in cand or []:
            ag = c.get("codigoAgrupacionPolitica")
            v = c.get("totalVotosValidos", 0) or 0
            if ag == ID_FUERZA_POPULAR:
                vK = v
            elif ag == ID_JUNTOS_PERU:
                vS = v
        t = tot or {}
        return _Ambito(
            vK=vK, vS=vS,
            actas_contabilizadas=int(t.get("contabilizadas", 0)),
            actas_total=int(t.get("totalActas", 0)),
            actas_enviadas_jee=int(t.get("enviadasJee", 0)),
        )

    # ------------------------------------------------------------------ #
    async def fetch(self) -> RawTally:
        async with CurlSession(impersonate="chrome124") as session:
            keiko_map, sanchez_map, ext = await asyncio.gather(
                self._fetch_mapa(session, ID_FUERZA_POPULAR),
                self._fetch_mapa(session, ID_JUNTOS_PERU),
                self._fetch_ambito(session, AMBITO_EXTRANJERO),
            )

        # --- regiões domésticas (oficiais, por departamento) ---
        regiones: list[RegionTally] = []
        for code, kd in sorted(keiko_map.items()):
            sd = sanchez_map.get(code, {})
            vK = kd["votos"]
            vS = sd.get("votos", 0)
            contab = kd["actas_contab"]
            pct = kd["pct_actas"] or 0.0
            total = round(contab / (pct / 100.0)) if pct > 0 else contab
            regiones.append(RegionTally(
                nombre=_DEPT_NOME.get(code, f"Depto {code}"),
                vK=vK, vS=vS,
                actas_contabilizadas=contab,
                actas_total=max(contab, total),
                es_exterior=False,
            ))

        # --- região do exterior (oficial) ---
        if ext.actas_total > 0:
            regiones.append(RegionTally(
                nombre="Peruanos en el Extranjero",
                vK=ext.vK, vS=ext.vS,
                actas_contabilizadas=ext.actas_contabilizadas,
                actas_total=ext.actas_total,
                es_exterior=True,
            ))

        # --- nacional = soma de todas as regiões (oficial) ---
        vK_nac = sum(r.vK for r in regiones)
        vS_nac = sum(r.vS for r in regiones)
        contab_nac = sum(r.actas_contabilizadas for r in regiones)
        total_nac = sum(r.actas_total for r in regiones)

        dom_regs = [r for r in regiones if not r.es_exterior]
        log.info(
            "ONPE oficial · Peru: K=%s S=%s (%s/%s atas) · "
            "Exterior: K=%s S=%s (%s/%s atas)",
            f"{sum(r.vK for r in dom_regs):,}", f"{sum(r.vS for r in dom_regs):,}",
            f"{sum(r.actas_contabilizadas for r in dom_regs):,}",
            f"{sum(r.actas_total for r in dom_regs):,}",
            f"{ext.vK:,}", f"{ext.vS:,}",
            f"{ext.actas_contabilizadas:,}", f"{ext.actas_total:,}",
        )

        return RawTally(
            vK=vK_nac,
            vS=vS_nac,
            actas_contabilizadas=contab_nac,
            actas_total=total_nac,
            actas_observadas=ext.actas_enviadas_jee,
            regiones=regiones,
            fuente="onpe",
        )
