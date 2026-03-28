# ──────────────────────────────────────────────────────────────────────────────
# frontend_code_review_env  –  Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
# Build : docker build -t frontend-code-review-env .
# Run   : docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY \
#                    frontend-code-review-env
#
# Optional overrides:
#   --task-id   single task   e.g.  easy_01
#   --model     OpenAI model  e.g.  gpt-4o-mini
#   --verbose   print generated code
#   --all       evaluate all 15 tasks (default)
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Security: do not run as root
RUN addgroup --system envuser && adduser --system --ingroup envuser envuser

# System deps (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: install Python dependencies ──────────────────────────────────────
FROM base AS builder

WORKDIR /build

# Copy requirements first for better layer caching
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 3: final image ──────────────────────────────────────────────────────
FROM base AS final

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project source
COPY --chown=envuser:envuser env.py       ./env.py
COPY --chown=envuser:envuser models.py    ./models.py
COPY --chown=envuser:envuser tasks.py     ./tasks.py
COPY --chown=envuser:envuser graders.py   ./graders.py
COPY --chown=envuser:envuser baseline.py  ./baseline.py
COPY --chown=envuser:envuser openenv.yaml ./openenv.yaml
COPY --chown=envuser:envuser README.md    ./README.md

USER envuser

# Expose PYTHONPATH so all local modules are importable
ENV PYTHONPATH=/app

# Default: evaluate all 15 tasks
ENTRYPOINT ["python", "baseline.py"]
CMD ["--all"]
