# ─────────────────────────────────────────────────────────────────────────────
#  Dockerfile — HHD-HY Survey System
#  Author  : Đỗ Hữu Hải (HHD-HY)
#  Stack   : Python 3.11 slim + Streamlit 1.32+
#  DB      : SQLite (default) | PostgreSQL (via DATABASE_URL env var)
#  Port    : 8501 (map to 80 hoặc 443 qua Nginx/Traefik)
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build dependencies ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Cài system packages cần thiết để build các thư viện Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements trước để tận dụng Docker layer cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

# System runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo user không phải root để bảo mật
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python packages từ builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code (loại trừ file trong .dockerignore)
COPY --chown=appuser:appuser . .

# Tạo thư mục data và phân quyền
RUN mkdir -p data && chown -R appuser:appuser /app

# Chuyển sang non-root user
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Health check — kiểm tra mỗi 30 giây
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Entrypoint
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false"]
