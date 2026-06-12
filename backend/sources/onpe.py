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

# Tradução ES→PT dos nomes que a ONPE manda (já title-cased). O que não
# estiver aqui sai como veio (Chile, Argentina, Brasil, Portugal…).
_PAIS_PT: dict[str, str] = {
    "Estados Unidos De Ámerica": "Estados Unidos",
    "España": "Espanha",
    "Italia": "Itália",
    "Japón": "Japão",
    "Bolivia": "Bolívia",
    "Francia": "França",
    "Alemania": "Alemanha",
    "Ecuador": "Equador",
    "Colombia": "Colômbia",
    "Suiza": "Suíça",
    "Australia": "Austrália",
    "Gran Bretaña": "Reino Unido",
    "Suecia": "Suécia",
    "Uruguay": "Uruguai",
    "Antillas Holandesas": "Antilhas Holandesas",
    "Paraguay": "Paraguai",
    "Guayana Francesa": "Guiana Francesa",
    "Nueva Zelanda": "Nova Zelândia",
    "Puerto Rico": "Porto Rico",
    "Austria": "Áustria",
    "Gran Ducado De Luxemburgo": "Luxemburgo",
    "República Popular China": "China",
    "Rusia": "Rússia",
    "Republica De Corea": "Coreia do Sul",
    "Hungría": "Hungria",
    "Principado De Andorra": "Andorra",
    "Finlandia": "Finlândia",
    "Emiratos Árabes Unidos": "Emirados Árabes Unidos",
    "República Checa": "República Tcheca",
    "Polonia": "Polônia",
    "Nicaragua": "Nicarágua",
    "Rumanía": "Romênia",
    "Grecia": "Grécia",
    "Jordania": "Jordânia",
    "Singapur": "Singapura",
    "Turquía": "Turquia",
    "Sudáfrica": "África do Sul",
    "Tailandia": "Tailândia",
    "Arabia Saudita": "Arábia Saudita",
    "Bielorrusia": "Bielorrússia",
    "República Árabe De Egipto": "Egito",
    "Marruecos": "Marrocos",
    "India": "Índia",
    "Indonesia": "Indonésia",
    "Argelia": "Argélia",
    "Trinidad Y Tobago": "Trinidad e Tobago",
    "Malasia": "Malásia",
    "Vietnam": "Vietnã",
    "Macedonia": "Macedônia do Norte",
    "Kenia": "Quênia",
    "Ghana": "Gana",
    "Irán": "Irã",
}
_CONT_PT: dict[str, str] = {
    "Asia": "Ásia",
    "Oceanía": "Oceania",
}

# Nome (.title() do espanhol, como vem da ONPE) -> ISO-3, p/ colorir o mapa.
# Países sem entrada (ou ausentes no GeoJSON) simplesmente não pintam.
_PAIS_ISO: dict[str, str] = {
    "Estados Unidos De Ámerica": "USA", "Argentina": "ARG", "Bolivia": "BOL",
    "Brasil": "BRA", "Canadá": "CAN", "Chile": "CHL", "Colombia": "COL",
    "Costa Rica": "CRI", "Cuba": "CUB", "Ecuador": "ECU", "El Salvador": "SLV",
    "Guatemala": "GTM", "México": "MEX", "Panamá": "PAN", "Uruguay": "URY",
    "Paraguay": "PRY", "Venezuela": "VEN", "Nicaragua": "NIC", "Honduras": "HND",
    "República Dominicana": "DOM", "Puerto Rico": "PRI", "Holanda": "NLD",
    "España": "ESP", "Italia": "ITA", "Francia": "FRA", "Alemania": "DEU",
    "Suiza": "CHE", "Bélgica": "BEL", "Gran Bretaña": "GBR", "Suecia": "SWE",
    "Austria": "AUT", "Dinamarca": "DNK", "Portugal": "PRT",
    "Gran Ducado De Luxemburgo": "LUX", "Rusia": "RUS", "Noruega": "NOR",
    "Hungría": "HUN", "Finlandia": "FIN", "República Checa": "CZE",
    "Polonia": "POL", "Irlanda": "IRL", "Rumanía": "ROU", "Grecia": "GRC",
    "Malta": "MLT", "Bielorrusia": "BLR", "Macedonia": "MKD",
    "Japón": "JPN", "Israel": "ISR", "República Popular China": "CHN",
    "Republica De Corea": "KOR", "Emiratos Árabes Unidos": "ARE",
    "Jordania": "JOR", "Turquía": "TUR", "Tailandia": "THA", "Catar": "QAT",
    "Arabia Saudita": "SAU", "India": "IND", "Indonesia": "IDN",
    "Malasia": "MYS", "Filipinas": "PHL", "Vietnam": "VNM", "Kuwait": "KWT",
    "Líbano": "LBN", "Irán": "IRN", "Australia": "AUS", "Nueva Zelanda": "NZL",
    "Sudáfrica": "ZAF", "República Árabe De Egipto": "EGY", "Marruecos": "MAR",
    "Argelia": "DZA", "Kenia": "KEN", "Ghana": "GHA", "Trinidad Y Tobago": "TTO",
}

# ubigeoNivel01 do mapa-calor = código do departamento × 10000.
# ATENÇÃO: a ONPE usa ubigeo ELEITORAL (Callao=24, Lima=14, Cusco=7…), que
# NÃO é o do INEI. Por isso os nomes vêm da própria API (ubigeos/
# departamentos) e não de tabela hardcoded — já erramos isso uma vez.


def _title_es(s: str) -> str:
    """Title-case respeitando conectivos ('MADRE DE DIOS' → 'Madre de Dios')."""
    out = (s or "").strip().title()
    for con in (" De ", " Del ", " La ", " El ", " Y "):
        out = out.replace(con, con.lower())
    return out


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
    async def _fetch_mapa(
        self, session, party: int, ambito: int = AMBITO_NACIONAL
    ) -> dict:
        """Mapa-calor de um candidato, agrupado por unidade geográfica.

        - ambito NACIONAL  → chave = cód. do departamento (int), nome via tabela.
        - ambito EXTRANJERO → chave = ubigeo do país (continente/país), nome
          vindo direto do payload (a ONPE rotula cada circunscrição do exterior).

        Cada valor: {nombre, votos, actas_contab, pct_actas}.
        """
        data = await self._get_json(session, "resumen-general/mapa-calor", {
            "idEleccion": self._id_eleccion,
            "codigoAgrupacionPolitica": party,
            "idAmbitoGeografico": ambito,
            "tipoFiltro": "ambito_geografico",
            "ubigeoNivel01": "", "ubigeoNivel02": "", "ubigeoNivel03": "",
        })
        out: dict = {}
        for it in data or []:
            if ambito == AMBITO_NACIONAL:
                key = (it.get("ubigeoNivel01") or 0) // 10000
                if key <= 0:
                    continue
                nombre = (self._nomes_dept or {}).get(key, f"Depto {key}")
            else:
                # Exterior: cada item é uma circunscrição (país). Usamos o
                # ubigeo mais específico disponível como chave e o rótulo do
                # próprio payload como nome do país.
                key = it.get("ubigeoNivel02") or it.get("ubigeoNivel01")
                if not key:
                    continue
                nombre = (
                    it.get("nombre") or it.get("descripcion")
                    or it.get("nombreUbigeo") or it.get("ubigeoDescripcion")
                    or f"Exterior {key}"
                ).strip().title()
            out[key] = {
                "nombre": nombre,
                "votos": it["participante"]["totalVotosValidos"],
                "actas_contab": it["actasContabilizadas"],
                "pct_actas": it["porcentajeActasContabilizadas"],
            }
        return out

    # ------------------------------------------------------------------ #
    # Exterior por PAÍS (descoberta jun/2026):                           #
    #   ubigeos/departamentos (ambito=2)        → 5 continentes c/ nome  #
    #   ubigeos/provincias?idUbigeoDepartamento → países do continente   #
    #   mapa-calor tipoFiltro=ubigeo_nivel_01&ubigeoNivel01=<continente> #
    #       → TODOS os países desse continente: votos, atas, % apuradas  #
    # ------------------------------------------------------------------ #
    _nomes_paises: dict[str, tuple[str, str]] | None = None  # ubigeo → (país, continente)
    _continentes: list[str] = []
    _nomes_dept: dict[int, str] | None = None  # cód. eleitoral → nome oficial

    async def _fetch_nomes_dept(self, session) -> None:
        """Nomes oficiais dos departamentos (ubigeo ELEITORAL da ONPE)."""
        if self._nomes_dept is not None:
            return
        data = await self._get_json(session, "ubigeos/departamentos", {
            "idEleccion": self._id_eleccion,
            "idAmbitoGeografico": AMBITO_NACIONAL,
        }) or []
        type(self)._nomes_dept = {
            int(d["ubigeo"]) // 10000: _title_es(d.get("nombre"))
            for d in data
        }
        log.info("departamentos: %s nomes oficiais carregados", len(data))

    async def _fetch_nomes_exterior(self, session) -> None:
        """Carrega (uma vez) os nomes oficiais de continentes e países."""
        if self._nomes_paises is not None:
            return
        conts = await self._get_json(session, "ubigeos/departamentos", {
            "idEleccion": self._id_eleccion,
            "idAmbitoGeografico": AMBITO_EXTRANJERO,
        }) or []
        listas = await asyncio.gather(*[
            self._get_json(session, "ubigeos/provincias", {
                "idEleccion": self._id_eleccion,
                "idAmbitoGeografico": AMBITO_EXTRANJERO,
                "idUbigeoDepartamento": c["ubigeo"],
            }) for c in conts
        ])
        nomes: dict[str, tuple[str, str, str]] = {}
        for c, paises in zip(conts, listas):
            cont_nome = (c.get("nombre") or "").strip().title()
            cont_nome = _CONT_PT.get(cont_nome, cont_nome)
            for p in paises or []:
                raw = (p.get("nombre") or "").strip().title()
                iso = _PAIS_ISO.get(raw, "")
                nome = _PAIS_PT.get(raw, raw)
                nomes[str(p["ubigeo"])] = (nome, cont_nome, iso)
        type(self)._nomes_paises = nomes
        type(self)._continentes = [str(c["ubigeo"]) for c in conts]
        log.info("exterior: %s continentes, %s países mapeados", len(conts), len(nomes))

    async def _fetch_exterior_paises(self, session) -> list[RegionTally]:
        """Desglose oficial do exterior POR PAÍS. [] se indisponível."""
        try:
            await self._fetch_nomes_exterior(session)
            if not self._continentes:
                return []
            tarefas = []
            for cont in self._continentes:
                for party in (ID_FUERZA_POPULAR, ID_JUNTOS_PERU):
                    tarefas.append(self._get_json(session, "resumen-general/mapa-calor", {
                        "idEleccion": self._id_eleccion,
                        "codigoAgrupacionPolitica": party,
                        "idAmbitoGeografico": AMBITO_EXTRANJERO,
                        "tipoFiltro": "ubigeo_nivel_01",
                        "ubigeoNivel01": cont,
                        "ubigeoNivel02": "", "ubigeoNivel03": "",
                    }))
            res = await asyncio.gather(*tarefas)
        except Exception as exc:  # noqa: BLE001
            log.warning("desglose do exterior por país indisponível: %s", exc)
            return []

        paises: dict[str, dict] = {}
        i = 0
        for cont in self._continentes:
            kdata, sdata = res[i], res[i + 1]
            i += 2
            for it in kdata or []:
                ub = str(it.get("ubigeoNivel02") or "")
                if not ub:
                    continue
                paises[ub] = {
                    "vK": it["participante"]["totalVotosValidos"],
                    "vS": 0,
                    "contab": it["actasContabilizadas"],
                    "pct": it["porcentajeActasContabilizadas"] or 0.0,
                }
            for it in sdata or []:
                ub = str(it.get("ubigeoNivel02") or "")
                if ub in paises:
                    paises[ub]["vS"] = it["participante"]["totalVotosValidos"]

        regiones: list[RegionTally] = []
        for ub, d in paises.items():
            nome, cont_nome, iso = (self._nomes_paises or {}).get(ub, (f"País {ub}", "", ""))
            total = round(d["contab"] / (d["pct"] / 100.0)) if d["pct"] > 0 else d["contab"]
            regiones.append(RegionTally(
                nombre=nome,
                vK=d["vK"], vS=d["vS"],
                actas_contabilizadas=d["contab"],
                actas_total=max(d["contab"], total),
                es_exterior=True,
                continente=cont_nome,
                iso=iso,
            ))
        return regiones

    # ------------------------------------------------------------------ #
    # Totais NACIONAIS oficiais (inclui o desglose do JEE)               #
    #   contabilizadas + enviadasJee + pendientesJee = totalActas (exato) #
    # ------------------------------------------------------------------ #
    async def _fetch_totales_nacional(self, session) -> dict:
        """`totales` no âmbito 0 = quadro nacional fechado, com JEE.

        Campos: contabilizadas, totalActas, enviadasJee, pendientesJee,
        totalVotosValidos. O filtro de ubigeo é IGNORADO pela ONPE aqui
        (sempre devolve o nacional), então só vale como total-país.
        """
        return await self._get_json(session, "resumen-general/totales", {
            "idEleccion": self._id_eleccion,
            "tipoFiltro": "ambito_geografico",
            "idAmbitoGeografico": 0,
        }) or {}

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
            # nomes oficiais primeiro (1 chamada, cacheada p/ sempre)
            await self._fetch_nomes_dept(session)
            keiko_map, sanchez_map, ext, ext_paises, tot_nac = await asyncio.gather(
                self._fetch_mapa(session, ID_FUERZA_POPULAR),
                self._fetch_mapa(session, ID_JUNTOS_PERU),
                self._fetch_ambito(session, AMBITO_EXTRANJERO),
                self._fetch_exterior_paises(session),
                self._fetch_totales_nacional(session),
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
                nombre=kd["nombre"],
                vK=vK, vS=vS,
                actas_contabilizadas=contab,
                actas_total=max(contab, total),
                es_exterior=False,
            ))

        # --- exterior: preferir desglose POR PAÍS; senão, agregado oficial ---
        if ext_paises:
            regiones.extend(ext_paises)
            # Reconciliação com o agregado oficial: países ainda sem ata
            # apurada não aparecem no mapa-calor e o total por % tem
            # arredondamento. O resíduo vira uma linha "por abrir" para a
            # partição nacional continuar batendo 1:1 com a ONPE.
            res_contab = ext.actas_contabilizadas - sum(p.actas_contabilizadas for p in ext_paises)
            res_total = ext.actas_total - sum(p.actas_total for p in ext_paises)
            res_vK = ext.vK - sum(p.vK for p in ext_paises)
            res_vS = ext.vS - sum(p.vS for p in ext_paises)
            if res_total > 0 or res_contab > 0 or res_vK > 0 or res_vS > 0:
                regiones.append(RegionTally(
                    nombre="Outros países (por abrir)",
                    vK=max(0, res_vK), vS=max(0, res_vS),
                    actas_contabilizadas=max(0, res_contab),
                    actas_total=max(0, res_total, res_contab),
                    es_exterior=True,
                ))
        elif ext.actas_total > 0:
            regiones.append(RegionTally(
                nombre="Peruanos en el Extranjero",
                vK=ext.vK, vS=ext.vS,
                actas_contabilizadas=ext.actas_contabilizadas,
                actas_total=ext.actas_total,
                es_exterior=True,
            ))

        # --- nacional: votos = soma das regiões (oficial); atas = totais
        # NACIONAIS oficiais da ONPE (mais exatos que somar estimativas por
        # região, e trazem o desglose do JEE). Fallback p/ soma se faltar. ---
        vK_nac = sum(r.vK for r in regiones)
        vS_nac = sum(r.vS for r in regiones)

        enviadas_jee = int(tot_nac.get("enviadasJee", 0) or 0)
        pendientes_jee = int(tot_nac.get("pendientesJee", 0) or 0)
        contab_nac = int(tot_nac.get("contabilizadas", 0) or 0) or sum(
            r.actas_contabilizadas for r in regiones)
        total_nac = int(tot_nac.get("totalActas", 0) or 0) or sum(
            r.actas_total for r in regiones)

        dom_regs = [r for r in regiones if not r.es_exterior]
        log.info(
            "ONPE oficial · Peru: K=%s S=%s (%s/%s atas) · "
            "Exterior: K=%s S=%s (%s/%s atas) · %s país(es) · "
            "JEE: %s enviadas + %s pendentes (todo o resto que falta)",
            f"{sum(r.vK for r in dom_regs):,}", f"{sum(r.vS for r in dom_regs):,}",
            f"{sum(r.actas_contabilizadas for r in dom_regs):,}",
            f"{sum(r.actas_total for r in dom_regs):,}",
            f"{ext.vK:,}", f"{ext.vS:,}",
            f"{ext.actas_contabilizadas:,}", f"{ext.actas_total:,}",
            len(ext_paises) if ext_paises else 0,
            f"{enviadas_jee:,}", f"{pendientes_jee:,}",
        )

        return RawTally(
            vK=vK_nac,
            vS=vS_nac,
            actas_contabilizadas=contab_nac,
            actas_total=total_nac,
            actas_observadas=enviadas_jee + pendientes_jee,
            actas_enviadas_jee=enviadas_jee,
            actas_pendientes_jee=pendientes_jee,
            regiones=regiones,
            fuente="onpe",
        )
