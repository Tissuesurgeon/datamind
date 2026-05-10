# syntax=docker/dockerfile:1.7
# DataMind 0G Storage bridge (Node sidecar).
FROM node:20-alpine
WORKDIR /app

COPY infra/og-bridge/package.json infra/og-bridge/package-lock.json* ./infra/og-bridge/
WORKDIR /app/infra/og-bridge
RUN npm install --omit=dev --no-audit --no-fund || npm install --no-audit --no-fund

COPY infra/og-bridge/ ./
WORKDIR /app
EXPOSE 8200
HEALTHCHECK --interval=20s --timeout=4s --retries=5 \
  CMD wget -qO- http://localhost:8200/healthz >/dev/null 2>&1 || exit 1
CMD ["node", "infra/og-bridge/cli.mjs", "serve"]
