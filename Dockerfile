# Stage 1: Build dependencies
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
    && rm -rf /var/lib/apt/lists/*

# OCI labels
LABEL org.opencontainers.image.title="TekBetter Scraper" \
      org.opencontainers.image.description="TekBetter Scraping Service" \
      org.opencontainers.image.version="1.0.0" \
      app.component="scraper-service"

WORKDIR /tekbetter

# Copy Python packages from builder
COPY --from=builder /root/.local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /root/.local/bin /usr/local/bin

# Create non-root user
RUN useradd -m -s /bin/bash scraper && \
    chown -R scraper:scraper /tekbetter

# Set environment variables
ENV PYTHONPATH=/tekbetter \
    PYTHONUNBUFFERED=1 \
    SCRAPERS_CONFIG_FILE=/tekbetter/scrapers.json

# Switch to non-root user
USER scraper

# Copy application code
COPY --chown=scraper:scraper app /tekbetter/app
COPY --chown=scraper:scraper app/main.py /tekbetter/

CMD ["python", "main.py"]