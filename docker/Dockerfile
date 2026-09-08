# ---- Builder ----
FROM node:22-slim AS builder
ENV PNPM_HOME="/pnpm" PATH="/pnpm:$PATH" COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN corepack enable && corepack prepare pnpm@11.24.0 --activate
# required to compile native deps (better-sqlite3) under linux
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml tsconfig.base.json ./
COPY packages/core ./packages/core
COPY apps/web ./apps/web

# esbuild's optional postinstall builds its native binary; allow it explicitly.
RUN pnpm install --frozen-lockfile --ignore-scripts
RUN pnpm rebuild esbuild
RUN pnpm --filter @noema/web build

# ---- Runner ----
FROM node:22-slim
ENV NODE_ENV=production PORT=3000 NITRO_HOST=0.0.0.0
WORKDIR /app

COPY --from=builder /app/apps/web/.output ./app

EXPOSE 3000
CMD ["node", "app/server/index.mjs"]
