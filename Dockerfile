# ── Build stage ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage ──────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for security
RUN useradd --create-home --no-log-init --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from build stage
COPY --from=builder /install /usr/local

# Copy application code (excluding .env, .venv, __pycache__)
COPY app/         ./app/
COPY run.py       ./run.py
COPY requirements.txt ./requirements.txt

# The .env file is NOT baked into the image.
# Pass environment variables at runtime via docker run -e or docker-compose.

USER appuser

EXPOSE 5000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Use gunicorn in production; 2 workers per CPU (adjust to your instance)
CMD ["gunicorn", "run:app", \
     "--workers", "4", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
