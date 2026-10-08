# Multi-stage minimal secure container for Appointment Booking System
# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Security: Install only necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Distroless / Hardened Runtime
FROM python:3.11-slim AS runtime

# Security Control 1: Minimal packages, clean apt cache
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Security Control 2: Non-root dedicated service user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# Copy python dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY backend /app/backend
COPY frontend /app/frontend

# Security Control 3: File permissions locked down to non-root user
RUN chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Set environment paths
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Security Control 4: Execute under non-privileged non-root user
USER 10001:10001

# Security Control 5: Explicit single port exposure
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/metrics')" || exit 1

ENTRYPOINT ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
