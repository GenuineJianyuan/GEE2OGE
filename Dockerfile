FROM node:20-bookworm-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt "earthengine-api>=1.7.0"

COPY . .
RUN cd web/gee_runner && npm install --omit=dev

RUN mkdir -p /app/web/gee_runner/runs

EXPOSE 5000

# Runner 内存状态只适用于单 worker；线程模式允许页面轮询与批处理并发。
CMD ["python3", "-m", "gunicorn", "--workers", "1", "--threads", "8", "--bind", "0.0.0.0:5000", "web.app:app"]
