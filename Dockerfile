# Stage 1: 前端构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY static/src/ ./static/src/
COPY vite.config.js ./
RUN npm run build

# Stage 2: Python运行环境（生产优化版）
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# 从builder阶段复制构建产物
COPY --from=frontend-builder /app/static/dist ./static/dist

COPY . .

RUN mkdir -p uploads/covers uploads/videos uploads/images \
             uploads/documents uploads/materials uploads/community

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
