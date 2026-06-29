# ================================================================
# SmokeSentinel — Dockerfile
# Base: Playwright + Python 3.11 + Node.js (for Playwright MCP server)
# ================================================================

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 (required for Playwright MCP server)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright MCP server globally
RUN npx -y @playwright/mcp@latest --version || true
RUN npm install -g @playwright/mcp@latest

# Python deps
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" --break-system-packages

# Copy source
COPY . .

# Install Playwright browsers (Chromium only — smoke tests, no need for all)
RUN playwright install chromium --with-deps

# Default: run the smoke agent
CMD ["python", "-m", "smokesentinel"]
