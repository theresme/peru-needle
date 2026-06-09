# Agulha · 2ª volta Peru 2026

Painel editorial ao vivo (estilo *needle* do NYT) para a 2ª volta presidencial
peruana de 2026 — **Keiko Fujimori** (Fuerza Popular) × **Roberto Sánchez**
(Juntos por el Perú). Faz scraping da apuração oficial da ONPE, roda um modelo
de probabilidade (Monte Carlo) e mostra uma agulha apontando quem é favorito a
**vencer no final** (não só quem lidera agora).

```
peru-needle/
├── backend/        FastAPI: polling da ONPE + modelo + /api/state
│   ├── config.py   << TODA a configuração do modelo e da fonte
│   ├── model.py    << Monte Carlo (o "coração" da agulha)
│   ├── sources/    << fontes plugáveis: onpe.py, mock.py
│   └── main.py     << API + loop de polling + cache
└── frontend/       React + Vite + Tailwind (agulha SVG custom)
```

## Como rodar (dev)

**1) Backend** (Python 3.11+):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
# fonte padrão = mock (simula uma noite de apuração, funciona offline)
.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

`GET http://localhost:8000/api/state` já responde com dados (mock).

**2) Frontend:**

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxy /api -> :8000)
```

Abra http://localhost:5173.

## Trocar para os dados REAIS da ONPE

A fonte mock existe porque, fora da noite eleitoral, a API da ONPE não tem dados
e o navegador é bloqueado por CORS. Para usar os números oficiais:

### Passo 1 — descobrir o endpoint JSON real (obrigatório)

O portal é uma SPA que consome uma API JSON interna. **Não** faça scraping do
HTML renderizado.

1. Abra https://resultadosegundavuelta.onpe.gob.pe (ou
   https://resultadoelectoral.onpe.gob.pe) no Chrome.
2. **DevTools → aba Network → filtro Fetch/XHR.**
3. Recarregue. Procure as respostas JSON com os números — campos como
   `votos`/`votosCandidatos`, `actasContabilizadas` / `actasProcesadas`,
   `actasTotal`, `actasObservadas`, e o desglose por `circunscripciones` /
   `departamentos` (incluindo **"Peruanos en el Extranjero"**).
4. Clique na requisição → **Copy → Copy as cURL** para ver URL + headers exatos.

### Passo 2 — apontar o adapter para o endpoint

Em `backend/config.py` (ou via variáveis de ambiente):

```python
ONPE_RESUMEN_URL = "https://.../o/endpoint/que/voce/achou"
ONPE_DETALLE_URL = "https://.../desglose/por/circunscricao"   # se for separado
```

### Passo 3 — ajustar o parser

Os nomes exatos das chaves do JSON só dá pra saber vendo a resposta real. Em
`backend/sources/onpe.py`, os métodos `_parse_resumen`, `_parse_detalle` e
`_candidate_votes` têm `# TODO` marcando onde mapear os campos. Ajuste para a
estrutura que você viu no DevTools.

### Passo 4 — ligar a fonte ONPE

```powershell
$env:SOURCE = "onpe"
.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

Se a resposta não tiver `actasTotal`, o adapter levanta erro pedindo para
ajustar o parser (e o backend mantém em cache o último snapshot válido).

> **Fonte de fallback (liveblog):** a interface `Source` em `sources/base.py` é
> plugável. Para ler um liveblog (Infobae/El Comercio) como alternativa, crie
> `sources/liveblog.py` implementando `fetch() -> RawTally` e registre em
> `sources/__init__.py`.

## O modelo (resumo)

Tudo configurável em `backend/config.py` (`ModelConfig`):

- Estima votos restantes a partir de `(atasTotal - atasContab) × média de votos/ata`,
  separando **doméstico** e **exterior**.
- Monte Carlo (N=20.000): sorteia o *lean* do voto restante doméstico
  (`Normal(0.67, 0.04)` → fração p/ Sánchez) e do exterior
  (`Normal(0.665, 0.05)` → fração p/ Keiko), mais ruído de comparecimento (±15%).
- A incerteza do *lean* **aumenta quando pouco foi apurado** → a agulha é larga
  no começo e estreita no fim (comportamento NYT).
- Se a API dá lean por departamento, usa o lean observado de cada região ainda
  não 100% apurada (`use_regional_lean`).
- Saída: `pVitoriaKeiko/Sanchez`, `margemP10/P50/P90`, projeção final e votos
  restantes estimados.

## Boas práticas embutidas

- Polling no máximo a cada **45s** (`POLL_INTERVAL_SECONDS`), User-Agent honesto,
  retry com backoff, cache do último snapshot válido, log com timestamp.
- A ONPE bloqueia CORS no browser → por isso o backend faz o fetch, não o front.

## Aviso

Projeção **não-oficial**. O resultado oficial é proclamado pelo **JNE** em
meados de julho. Sem vínculo com ONPE, JNE ou campanhas.
