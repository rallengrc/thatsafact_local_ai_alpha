# Multi-Environment Container Definition for Hello MLaaS Burst
# Compatible with: Local Mac (arm64), AWS EKS (amd64/arm64), and On-Prem VMs
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy workflow, runner, and the benchmark modules local_runner.py imports
COPY workflow.py .
COPY local_runner.py .
COPY benchmark_runner.py .
COPY benchmark_db.py .

# Default entrypoint runs the local verification suite
ENTRYPOINT ["python3", "local_runner.py"]
