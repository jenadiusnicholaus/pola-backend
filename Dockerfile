# ==========================================
# Multi-stage Dockerfile for POLA Backend
# Supports both local development and production
# ==========================================

# ==========================================
# Stage 1: Base image with common dependencies
# ==========================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client and development libraries
    libpq-dev \
    # Required for Pillow
    libjpeg-dev \
    zlib1g-dev \
    # Required for WeasyPrint/Cairo
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    # Required for python-magic
    libmagic1 \
    # Build essentials for compiling packages
    gcc \
    g++ \
    # Useful utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# ==========================================
# Stage 2: Development image
# ==========================================
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ==========================================
# Stage 3: Production builder
# ==========================================
FROM base as builder

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 4: Production image
# ==========================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Disable debug in production
    DEBUG=False

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    shared-mime-info \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 pola \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home pola

# Set work directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY --chown=pola:pola . .

# Create necessary directories
RUN mkdir -p logs media static \
    && chown -R pola:pola logs media static

# Collect static files
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Switch to non-root user
USER pola

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Production command with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--worker-tmp-dir", "/dev/shm", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "pola_settings.wsgi:application"]
