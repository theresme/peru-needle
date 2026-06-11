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

# Limiares (poll ~60s). Afrouxados de propósito: feed vivo > feed mudo.
SALTO_ATAS = 25          # atas novas em bloco p/ virar notícia
SWING_PROB_PP = 1.5      # variação de prob. do favorito (pontos %)
EXT_PASSO_PP = 0.8       # avanço da apuração do exterior
DEPT_FECHA = 99.9        # % p/ considerar departamento "fechado"
LOTE_MIN_VOTOS = 50      # votos novos p/ noticiar o lote e quem o venceu
PAIS_MIN_ATAS = 3        # atas novas de um país do exterior p/ noticiar

# Marcos de diferença de votos (notícia quando o gap cai abaixo).
GAP_MARCOS = [100_000, 50_000, 25_000, 15_000, 10_000, 5_000, 2_500, 1_000, 500]
# Marcos de probabilidade do favorito (notícia ao cruzar p/ cima).
PROB_MARCOS = [75, 90, 95, 99]


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
            pct_ext = ext.get("pct", 0) or 0
            titulo = ("Voto do exterior mal começou" if pct_ext < 50
                      else f"Exterior já {str(pct_ext).replace('.', ',')}% apurado")
            add("exterior", "🌎", titulo,
                f"{str(pct_ext).replace('.', ',')}% apurado; está em "
                f"{ext.get('pctK')}% Keiko vs. ~{str(EXT_HIST_KEIKO).replace('.', ',')}% "
                "em 2021. É o principal curinga restante.", "ctx_ext")
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

    # --- 9) LOTE: quem venceu os votos novos deste poll -----------------
    dvK = novo.get("vK", 0) - prev.get("vK", 0)
    dvS = novo.get("vS", 0) - prev.get("vS", 0)
    dtot = dvK + dvS
    if dtot >= LOTE_MIN_VOTOS:
        split_k = 100.0 * dvK / dtot
        quem = "Keiko" if dvK >= dvS else "Sánchez"
        pct_lote = split_k if dvK >= dvS else 100.0 - split_k
        saldo = abs(dvK - dvS)
        icone = "🟠" if quem == "Keiko" else "🔵"
        add("info", icone, f"Lote pende para {quem}",
            f"{quem} levou {_fmt_pp(pct_lote)}% dos {_fmt_int(dtot)} votos novos "
            f"(saldo +{_fmt_int(saldo)} no lote"
            + (f", {_fmt_int(delta)} atas" if delta > 0 else "") + ").", "lote")

    # --- 10) gap cruza marcos (a caçada da virada) ----------------------
    gap_p = abs(prev.get("vK", 0) - prev.get("vS", 0))
    gap_n = abs(novo.get("vK", 0) - novo.get("vS", 0))
    lid_nome = "Keiko" if vk >= vs else "Sánchez"
    persegue = "Sánchez" if vk >= vs else "Keiko"
    for marco in reversed(GAP_MARCOS):  # menor marco cruzado = mais dramático
        if gap_n < marco <= gap_p:
            quente = marco <= 5_000
            add("alerta" if quente else "virada", "🔥" if quente else "📏",
                f"Diferença cai abaixo de {_fmt_int(marco)}!",
                f"{lid_nome} lidera por só {_fmt_int(gap_n)} votos — "
                f"{persegue} se aproxima.", f"gap_{marco}")
            break
        if gap_p < marco <= gap_n and marco >= 10_000:
            add("info", "🛡️", f"{lid_nome} amplia a frente",
                f"Diferença volta a superar {_fmt_int(marco)} votos "
                f"({_fmt_int(gap_n)}).", f"gapup_{marco}")
            break

    # --- 11) probabilidade cruza marcos ---------------------------------
    if pf_p is not None and pf_n is not None and fav_n:
        fava_nome = "Keiko" if fav_n == "keiko" else "Sánchez"
        p_fav_p = (pf_p if fav_n == "keiko" else 1 - pf_p) * 100
        p_fav_n = (pf_n if fav_n == "keiko" else 1 - pf_n) * 100
        for marco in reversed(PROB_MARCOS):  # maior marco cruzado primeiro
            if p_fav_p < marco <= p_fav_n:
                add("virada", "🎯", f"Modelo crava {marco}% para {fava_nome}",
                    f"Probabilidade de vitória subiu para {round(p_fav_n)}% "
                    f"(margem projetada {_fmt_pp(mod_n.get('margemP50', 0))} pp).",
                    f"prob_{marco}")
                break
            if p_fav_n < marco <= p_fav_p:
                add("alerta", "🫨", f"Modelo recua de {marco}%",
                    f"Probabilidade de {fava_nome} caiu para {round(p_fav_n)}% — "
                    "o desfecho reabriu.", f"probdown_{marco}")
                break

    # --- 12) exterior por PAÍS: atas novas / país fechado ---------------
    paises_p = {p["nombre"]: p for p in prev.get("exteriorPaises", [])}
    movs = []
    for p in novo.get("exteriorPaises", []):
        ant = paises_p.get(p["nombre"])
        if not ant:
            continue
        d_atas = p.get("atasContabilizadas", 0) - ant.get("atasContabilizadas", 0)
        d_vk = p.get("vK", 0) - ant.get("vK", 0)
        d_vs = p.get("vS", 0) - ant.get("vS", 0)
        if d_atas >= PAIS_MIN_ATAS and (d_vk + d_vs) > 0:
            movs.append((d_vk + d_vs, p, d_atas, d_vk, d_vs))
        elif ant.get("atasRestantes", 0) > 0 and p.get("atasRestantes", 1) == 0:
            add("exterior", "🏁", f"{p['nombre']} fechou a apuração",
                f"100% das atas: {'Keiko' if p['lider'] == 'keiko' else 'Sánchez'} "
                f"venceu com {_fmt_pp(max(p['pctK'], p['pctS']))}%.",
                f"pais_fecha_{p['nombre']}")
    for tot, p, d_atas, d_vk, d_vs in sorted(movs, reverse=True)[:2]:
        quem = "Keiko" if d_vk >= d_vs else "Sánchez"
        pct_lote = 100.0 * max(d_vk, d_vs) / tot
        add("exterior", "🌍", f"{p['nombre']} abriu {_fmt_int(d_atas)} atas",
            f"{quem} levou {_fmt_pp(pct_lote)}% do lote "
            f"(+{_fmt_int(abs(d_vk - d_vs))} de saldo). "
            f"País agora {_fmt_pp(p.get('pctApurado', 0))}% apurado.",
            f"pais_{p['nombre']}")

    # --- 12b) MATEMATICAMENTE ELEITO (o evento da noite) ----------------
    el_p = (prev.get("eleito") or {}).get("estado")
    el_n = novo.get("eleito") or {}
    if el_p == "em_aberto" and el_n.get("estado") == "eleito":
        nome = "Keiko" if el_n.get("quem") == "keiko" else "Sánchez"
        add("virada", "🏆", f"{nome} está matematicamente eleito(a)!",
            f"Mesmo que todos os votos restantes fossem para o adversário, "
            f"{nome} segue à frente. Vantagem de {_fmt_int(el_n.get('gap', 0))} "
            f"votos é maior que o máximo que ainda pode entrar.", "eleito")

    # --- 13) conta-giro: contagem pausa / retoma com ETA -----------------
    vir_p = prev.get("virada") or {}
    vir_n = novo.get("virada") or {}
    if vir_p.get("estado") == "pausada" and vir_n.get("estado") == "contando":
        eta = vir_n.get("etaMin")
        extra = (f" No ritmo atual, virada em ~{_fmt_int(eta)} min."
                 if eta else "")
        add("info", "▶️", "Contagem retomada",
            f"Novas atas voltaram a entrar após a pausa.{extra}", "retoma")
    elif vir_p.get("estado") == "contando" and vir_n.get("estado") == "pausada":
        add("info", "⏸️", "Contagem dá uma pausa",
            f"Sem atas novas há {_fmt_int(vir_n.get('minSemMovimento', 0))} min. "
            "O saldo restante continua "
            + ("projetando virada." if vir_n.get("projetaVirar") else "sem virada."),
            "pausa")

    return eventos
