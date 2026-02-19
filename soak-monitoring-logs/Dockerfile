# Soak Monitoring — multi-stage Docker image
# Runs the full soak monitoring workflow:
#   1. Fetch Velocity item logs
#   2. Fetch Kubernetes pod logs
#   3. Generate summary report via Azure OpenAI
#
# Build:
#   docker build -t soak-monitor:latest -f soak-monitoring-logs/Dockerfile .
#
# Run (local testing):
#   docker run --rm \
#     -v ~/.kube:/home/app/.kube:ro \
#     -v ~/.aws:/home/app/.aws:ro \
#     -e AWS_PROFILE=default \
#     soak-monitor:latest --config environments.yaml
#
# Note: Build context must be the repo root (not soak-monitoring-logs/)
#       so the common/ package is available.

FROM python:3.11-slim AS base

# Install kubectl
ARG KUBECTL_VERSION=v1.31.3
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/$(dpkg --print-architecture)/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Verify kubectl
RUN kubectl version --client

# Create non-root user
RUN useradd -m -s /bin/bash app
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir ".[soak-monitoring]"

# Copy application code
COPY common/ ./common/
COPY soak-monitoring-logs/ ./soak-monitoring-logs/

# Create logs output directory
RUN mkdir -p /app/soak-monitoring-logs/logs && \
    chown -R app:app /app

USER app

WORKDIR /app/soak-monitoring-logs

# Ensure common package is importable
ENV PYTHONPATH=/app

# Default entrypoint runs the orchestrator
ENTRYPOINT ["python", "src/run_soak_monitor.py"]
CMD ["--config", "environments.yaml"]
