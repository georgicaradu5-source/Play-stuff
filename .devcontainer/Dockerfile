FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies useful for development
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        git \
        curl \
        ca-certificates \
        build-essential \
        sqlite3 \
        jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Pre-install Python dev tooling globally to speed up container builds
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir pytest pytest-cov pytest-mock nox ruff mypy

# Set working directory
WORKDIR /workspace

# Default user is vscode (non-root)
USER vscode
