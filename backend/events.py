"""Detector de 'acontecimentos' da apuração.

Compara o snapshot anterior com o atual e gera fatos relevantes em linguagem
natural (PT-BR) para um feed estilo liveblog:
  • viradas (favorito / líder na contagem bruta)
  • saltos de probabilidade
  • atas que ENTRARAM em bloco ou que SUMIRAM (anomalia)
  • exterior vs. expectativa histórica
  • departamentos que fecham em 100%
  • marcos de apuração nacional

Cada evento é um dict serializável:
  {id, t, nivel, icone, titulo, texto}
nivel ∈ {"alerta","virada","info","marco","exterior"}
"""
from __future__ import annotations

# Expectativa histórica do voto do exterior (2ª volta 2021): ~66.5% Keiko.
EXT_HIST_KEIKO = 66.5

# Limiares (poll ~60s) para evitar spam.
SALTO_ATAS = 60          # atas novas em bloco p/ virar notícia
SWING_PROB_PP = 3.0      # variação de prob. do favorito (pontos %)
EXT_PASSO_PP = 1.5       # avanço da apuração do exterior
DEPT_FECHA = 99.9        # % p/ considerar departamento "fechado"


def _fmt_int(n) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def _fmt_pp(x: float) -> str:
    s = f"{abs(x):.2f}".replace(".", ",")
    return s


def _votos_lider(estado: dict) -> tuple[str, int, int]:
    cands = estado.get("candidatos", [])
    if len(cands) < 2:
        return "", 0, 0
    k = next((c for c in cands if c["id"] == "keiko"), cands[0])
    s = next((c for c in cands if c["id"] == "sanchez"), cands[1])
    lider = "keiko" if k["votos"] >= s["votos"] else "sanchez"
    return lider, k["votos"], s["votos"]


def detectar_eventos(prev: dict | None, novo: dict) -> list[dict]:
    """Retorna a lista de eventos (mais relevantes primeiro) entre dois estados."""
    t = novo.get("timestamp", "")
    eventos: list[dict] = []

    def add(nivel, icone, titulo, texto, key):
        eventos.append({
            "id": f"{t}|{key}",
            "t": t,
            "nivel": nivel,
            "icone": icone,
            "titulo": titulo,
            "texto": texto,
        })

    if prev is None:
        # Primeiro snapshot: descreve a situação atual para o feed já ter contexto.
        mod = novo.get("modelo", {})
        cands = novo.get("candidatos", [])
        ext = novo.get("exterior", {})
        if len(cands) >= 2:
            lid, vk, vs = _votos_lider(novo)
            nome = "Keiko" if lid == "keiko" else "Sánchez"
            add("info", "🗳️", f"{nome} lidera a contagem",
                f"Com {novo.get('pctApurado', 0)}% das atas apuradas, "
                f"{nome} está à frente por {_fmt_int(abs(vk - vs))} votos.", "ctx_lider")
        if mod.get("favorito"):
            fnome = "Keiko" if mod["favorito"] == "keiko" else "Sánchez"
            add("virada", "🎯", f"Modelo favorece {fnome}",
                f"{round(mod.get('pFavorito', 0)*100)}% de probabilidade de vitória "
                f"(margem final projetada {_fmt_pp(mod.get('margemP50', 0))} pp).", "ctx_modelo")
        if ext.get("pct") is not None and ext.get("pctK") is not None:
            add("exterior", "🌎", "Voto do exterior mal começou",
                f"Só {ext.get('pct', 0)}% apurado; tende a Keiko "
                f"({ext.get('pctK')}%) vs. ~{str(EXT_HIST_KEIKO).replace('.', ',')}% em 2021. "
                "É o principal curinga restante.", "ctx_ext")
        add("info", "📡", "Monitoramento iniciado",
            "Painel conectado à apuração oficial da ONPE.", "init")
        return eventos

    mod_n = novo.get("modelo", {})
    mod_p = prev.get("modelo", {})

    # --- 1) atas que SUMIRAM ou entraram em bloco ----------------------
    atas_p = prev.get("atas", {}).get("contabilizadas", 0)
    atas_n = novo.get("atas", {}).get("contabilizadas", 0)
    delta = atas_n - atas_p
    if delta < 0:
        add("alerta", "🚨", "Atas saíram da contagem!",
            f"O total contabilizado CAIU {_fmt_int(-delta)} atas "
            f"(de {_fmt_int(atas_p)} para {_fmt_int(atas_n)}). "
            "Pode ser reprocessamento/observação da ONPE.", "atas_caiu")
    elif delta >= SALTO_ATAS:
        pp = 100.0 * delta / max(1, novo.get("atas", {}).get("total", 1))
        add("info", "📥", "Entrada de atas em bloco",
            f"+{_fmt_int(delta)} atas novas (≈{_fmt_pp(pp)} pp). "
            f"Agora {novo.get('pctApurado', 0)}% apurado.", "atas_bloco")

    # --- 2) virada do FAVORITO (modelo) --------------------------------
    fav_p = mod_p.get("favorito")
    fav_n = mod_n.get("favorito")
    if fav_p and fav_n and fav_p != fav_n:
        nome = "Keiko" if fav_n == "keiko" else "Sánchez"
        add("virada", "🔄", f"Virada: {nome} assume a frente",
            f"O modelo passou a favorecer {nome} "
            f"({round(mod_n.get('pFavorito', 0)*100)}% de probabilidade).", "vira_fav")

    # --- 3) virada na CONTAGEM BRUTA -----------------------------------
    lid_p, _, _ = _votos_lider(prev)
    lid_n, vk, vs = _votos_lider(novo)
    if lid_p and lid_n and lid_p != lid_n:
        nome = "Keiko" if lid_n == "keiko" else "Sánchez"
        dif = abs(vk - vs)
        add("virada", "⚡", f"{nome} assume a liderança nos votos",
            f"Passou à frente na contagem oficial por {_fmt_int(dif)} votos.", "vira_voto")

    # --- 4) swing de probabilidade -------------------------------------
    pf_p = mod_p.get("pVitoriaKeiko")
    pf_n = mod_n.get("pVitoriaKeiko")
    if pf_p is not None and pf_n is not None:
        d_pp = (pf_n - pf_p) * 100.0
        if abs(d_pp) >= SWING_PROB_PP and fav_p == fav_n:
            sobe = d_pp > 0  # subiu p/ Keiko
            nome = "Keiko" if sobe else "Sánchez"
            add("info", "📈" if sobe else "📉",
                f"Probabilidade move-se para {nome}",
                f"Chance de Keiko {('subiu' if sobe else 'caiu')} "
                f"{_fmt_pp(d_pp)} pp → {round(pf_n*100)}%.", "swing_prob")

    # --- 5) exterior vs expectativa ------------------------------------
    ext_p = prev.get("exterior", {})
    ext_n = novo.get("exterior", {})
    pct_ext_p = ext_p.get("pct", 0) or 0
    pct_ext_n = ext_n.get("pct", 0) or 0
    if pct_ext_n - pct_ext_p >= EXT_PASSO_PP and ext_n.get("pctK") is not None:
        k_ext = ext_n["pctK"]
        diff_hist = k_ext - EXT_HIST_KEIKO
        comp = ("acima" if diff_hist > 1 else "abaixo" if diff_hist < -1 else "em linha")
        add("exterior", "🌎", "Exterior avança na apuração",
            f"Esperava-se ~{str(EXT_HIST_KEIKO).replace('.', ',')}% Keiko (2021); "
            f"com {pct_ext_n}% apurado está em {k_ext}% "
            f"({comp} do histórico).", "ext_passo")

    # --- 6) departamentos que fecharam ---------------------------------
    dep_p = {d["nombre"]: d for d in prev.get("porDepartamento", [])}
    fechou = []
    for d in novo.get("porDepartamento", []):
        ant = dep_p.get(d["nombre"])
        if ant and ant.get("pctApurado", 0) < DEPT_FECHA <= d.get("pctApurado", 0):
            nome = "Keiko" if d["lider"] == "keiko" else "Sánchez"
            fechou.append(f"{d['nombre']} ({nome} {max(d['pctK'], d['pctS'])}%)")
    if fechou:
        add("marco", "✅",
            "Departamento fechado" if len(fechou) == 1 else f"{len(fechou)} departamentos fechados",
            "100% apurado: " + "; ".join(fechou[:4]) + ".", "dept_fecha")

    # --- 7) marco de apuração nacional (cruzou 0,5%) -------------------
    ap_p = prev.get("pctApurado", 0)
    ap_n = novo.get("pctApurado", 0)
    if int(ap_n * 2) > int(ap_p * 2):  # cruzou múltiplo de 0,5%
        marco = int(ap_n * 2) / 2
        add("marco", "📊", f"Apuração nacional em {str(marco).replace('.', ',')}%",
            f"{_fmt_int(atas_n)} de {_fmt_int(novo.get('atas',{}).get('total',0))} atas contabilizadas.",
            "marco_nac")

    # --- 8) empate técnico ---------------------------------------------
    m_p = abs(mod_p.get("margemP50", 99))
    m_n = abs(mod_n.get("margemP50", 99))
    if m_n < 0.10 <= m_p:
        add("alerta", "⚖️", "Empate técnico",
            f"Margem final projetada caiu para {_fmt_pp(mod_n.get('margemP50', 0))} pp.",
            "empate")

    return eventos
