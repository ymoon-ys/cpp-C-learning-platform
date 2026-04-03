# Stage 1: 前端构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app/static

COPY package.json package-lock.json* ./
RUN npm ci

COPY src/ ./src/
RUN npm run build

# Stage 2: Python运行环境
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
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

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
