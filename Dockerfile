# ---------------------------------------------------------------------------
# Painel 2ª volta Peru 2026 — imagem única (frontend + backend).
# Estágio 1: builda o frontend React/Vite com Node.
# Estágio 2: roda o backend FastAPI (Python) servindo o front buildado.
# ---------------------------------------------------------------------------

# ---- 1) build do frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build          # gera /app/frontend/dist

# ---- 2) runtime do backend ----
FROM python:3.11-slim AS backend
WORKDIR /app
# deps do Python (inclui curl_cffi para o fingerprint TLS da ONPE)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# código do backend
COPY backend/ ./
# frontend buildado entra como ./static (o main.py serve essa pasta)
COPY --from=frontend /app/frontend/dist ./static

# fonte de dados oficial da ONPE
ENV SOURCE=onpe
# o Render injeta a porta via $PORT; localmente cai em 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
