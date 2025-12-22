# Backend Dockerfile for Django REST Framework
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements/ requirements/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements/development.txt

# Copy project files
COPY . .

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Set permissions for entrypoint script
RUN chmod +x /app/docker-entrypoint.sh

# Collect static files (will be overridden by volume in development)
RUN python manage.py collectstatic --noinput || true

# Create a non-root user
RUN useradd -m -u 1000 django && \
    chown -R django:django /app

USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5)" || exit 1

# Default command (can be overridden in docker-compose)
CMD ["/app/docker-entrypoint.sh"]
