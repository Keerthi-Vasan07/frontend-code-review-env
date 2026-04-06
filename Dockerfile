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
# ── Stage 3: final image ──────────────────────────────────────────────────────
FROM base AS final

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# ✅ Copy entire project (FIX)
COPY --chown=envuser:envuser . .

USER envuser

ENV PYTHONPATH=/app
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]