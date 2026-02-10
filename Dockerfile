# Multi-stage build for tinyvc pipeline
# Optimized for size and security

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies to a local directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Metadata
LABEL maintainer="tinyvc"
LABEL description="Automated weekly investment research pipeline"
LABEL version="1.0.0"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash tinyvc

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/tinyvc/.local

# Copy application code
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY config/ ./config/
COPY templates/ ./templates/
COPY prompts/ ./prompts/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p data/raw data/processed data/llm data/reports data/metadata \
    data/evaluations data/performance outputs \
    && chown -R tinyvc:tinyvc /app

# Switch to non-root user
USER tinyvc

# Add local Python packages to PATH
ENV PATH=/home/tinyvc/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Set Python to run in unbuffered mode (better for logs)
ENV PYTHONUNBUFFERED=1

# Health check (optional, validates Python environment)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command: run the pipeline
CMD ["python", "src/main.py"]
