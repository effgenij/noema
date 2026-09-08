# TanStack Start stack research — 2026-09-08

Primary-sources only (official docs, npm registry, official examples/starter repos). Every claim carries its source URL.

## TL;DR

- **TanStack Start is 1.x GA** — `@tanstack/react-start@1.168.50` (`latest` dist-tag, MIT, `engines.node >=22.12.0`), `@tanstack/react-router@1.170.33`. The framework now ships as scoped packages; the docs Overview page still carries a stale "Release Candidate" banner, but the npm `latest` tag is a stable 1.x release. ([npm: @tanstack/react-start](https://www.npmjs.com/package/@tanstack/react-start), [Overview](https://tanstack.com/start/latest/docs/framework/react/overview))
- **Server functions (`createServerFn`) already give end-to-end type safety + Zod validation + TanStack Query integration.** They are same-origin only. **tRPC is largely redundant for v1** — the only non-browser consumer (the MCP server) imports `@noema/core` in-process, not over HTTP. Keep tRPC only if you later need a public/versioned HTTP API for non-web clients (mobile/desktop) or want request batching/subscriptions. This refines the approved design's P8 (which lists tRPC). ([server functions](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions), [tRPC](https://trpc.io/docs), [discussion #3884](https://github.com/TanStack/router/discussions/3884))
- **SQLite driver: `better-sqlite3`** for a single-process Docker deploy (synchronous, local-file, fastest; `13.0.3`, node ≥22). `libsql`/`@libsql/client` only if you want Turso-remote or at-rest encryption. Migrations via `drizzle-kit generate` + `drizzle-kit migrate` (or programmatic `migrate()` at container start). WAL + `busy_timeout` set on the connection at startup, **not** via a migration file. ([drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite), [better-sqlite3 API](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md))
- **Sharing:** `packages/core` exports Drizzle schemas (via `drizzle-orm/sqlite-core`, driver-agnostic) + Zod + domain logic + a single `createDb()` (better-sqlite3 + WAL + busy_timeout). `apps/web` and `packages/mcp` depend on it with `"@noema/core": "workspace:*"`. Dependencies flow one way (`* → core`), so no cycles. ([pnpm workspaces](https://pnpm.io/workspaces))
- **One Docker image:** multi-stage BuildKit build with the pnpm store cache mount, `pnpm deploy --filter=@noema/web --prod` to assemble a slim runtime layer, SQLite file on a `VOLUME`, migrations run at container start. ([pnpm Docker](https://pnpm.io/docker))

---

## 1. TanStack Start — version, maturity, and the tRPC question

### Version & maturity

- `@tanstack/react-start` `latest` = **1.168.50** (MIT, `engines.node >=22.12.0`, published via GitHub Actions trusted publishing). ([npm](https://www.npmjs.com/package/@tanstack/react-start))
- `@tanstack/react-router` `latest` = **1.170.33**. ([npm](https://www.npmjs.com/package/@tanstack/react-router))
- `@tanstack/start` (unscoped, the older umbrella package) sits at **1.120.20**; the framework is now delivered as scoped packages (`@tanstack/react-start`, `@tanstack/react-start-client`, `@tanstack/react-start-server`, `@tanstack/start-*`). ([npm: @tanstack/start](https://www.npmjs.com/package/@tanstack/start))
- Maturity caveat: the official Overview page still shows a "**Release Candidate** stage" note ("feature-complete … API is considered stable … the road to v1 will likely be a quick one"). This banner is **stale relative to npm**, where `latest` is a 1.x release — treat Start as GA-but-fast-moving (near-daily releases), and expect to read changelogs. ([Overview](https://tanstack.com/start/latest/docs/framework/react/overview))

### What it provides (per the official docs)

- **Server functions** — `createServerFn()`, type-safe RPC across the client/server boundary, callable from route loaders, components (`useServerFn()`), event handlers, and other server functions. Inputs can be validated with **Zod**. On the client they compile to fetch-based RPC stubs; the server code never reaches the browser. ([server functions guide](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions))
- **Same-origin only.** "Server functions are meant to be called by your TanStack Start application." For callers outside the app, the docs direct you to **server routes / API routes**. ([server functions guide](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions))
- **SSR** — full-document SSR by default, plus **selective SSR** (configure which routes run `beforeLoad`/`loader` on server) and streaming. ([Overview](https://tanstack.com/start/latest/docs/framework/react/overview), [selective SSR](https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr))
- **File-based routing** — routes live in `src/routes` (`__root.tsx`, `index.tsx`, `posts/$postId.tsx`); Start "relies 100% on TanStack Router". ([routing guide](https://tanstack.com/start/latest/docs/framework/react/guide/routing))
- Scaffold via **TanStack Builder**, the **TanStack CLI**, or clone the official **`start-basic`** / **`start-basic-react-query`** examples. ([quick-start](https://tanstack.com/start/latest/docs/framework/react/quick-start))

### tRPC on top of server functions — what does it actually add?

Server functions already provide the core tRPC value (compile-time typesafety across the network, input validation, no codegen) for a single app. tRPC's incremental value is:

1. **Callable from outside the Start app.** tRPC is framework-agnostic and can be mounted as an HTTP endpoint consumed by *other* apps (mobile, desktop, third parties) with the same type inference — server functions are same-origin only. ([tRPC](https://trpc.io/docs), [server functions note](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions))
2. **Request batching** — simultaneous calls combined into one request. ([tRPC features](https://trpc.io/docs))
3. **Subscriptions** — type-safe realtime. ([tRPC features](https://trpc.io/docs))
4. **Ecosystem** — adapters, OpenAPI generation, middleware, etc. ([tRPC](https://trpc.io/docs))

The community's own discussion lands on: server functions are sufficient when your backend isn't consumed by *other* apps; you reach for tRPC when a non-Start client needs the same type-safe API (otherwise you'd fall back to plain server routes and lose typesafety). ([TanStack router discussion #3884](https://github.com/TanStack/router/discussions/3884))

**Recommendation for noema:** the MCP server (`packages/mcp`) is *not* an HTTP consumer of the web app — it imports `@noema/core` directly (in-process or stdio on the same SQLite file). So tRPC's #1 reason doesn't apply. Use **Start server functions + Zod** as the web data layer (they integrate with TanStack Query via `useServerFn`/loaders), and **defer tRPC** until a versioned public HTTP API for non-web clients is actually needed. This is a smaller v1 than the approved P8's "tRPC" and removes a redundant API surface.

---

## 2. Drizzle + SQLite — driver, migrations, WAL + busy_timeout

### Driver choice

Drizzle has native SQLite support for **`libsql`**, **`node:sqlite`**, and **`better-sqlite3`**. ([drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite))

| Driver | Package / version | Model | Use when |
|---|---|---|---|
| **better-sqlite3** | `13.0.3`, MIT, node ≥22 | synchronous, local file | single-process self-hosted app (default) |
| **node:sqlite** | built into Node 22+ | synchronous, local file | want zero native deps |
| **libsql** (`@libsql/client`) | `0.18.0`, MIT | async, file **or** Turso remote | need Turso remote, at-rest encryption, or extra `ALTER`s |

The official Drizzle SQLite guide notes the *main* difference: **libSQL can connect to both local files and Turso remote** and adds encryption-at-rest and more `ALTER` statements, whereas `better-sqlite3`/`node:sqlite` are plain local-file drivers. ([drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite))

**Recommendation:** `better-sqlite3` for noema — synchronous, fastest, local-file only, single Docker process. `libsql` buys you remote/encryption you don't need for a volume-mounted single DB file. (Fallback: built-in `node:sqlite` if you want to drop the native dependency; Drizzle supports it via `drizzle-orm/node-sqlite`.) ([drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite))

**Version pinning note:** `drizzle-orm` `latest` = **0.45.2** (Apache-2.0), `rc` = **1.0.0-rc.4**; `drizzle-kit` `latest` = **0.31.10**. The current Drizzle SQLite guide installs `drizzle-orm@rc`. Pick one consistently (stable 0.45.x or the 1.0 RC) — the `sqliteTable` schema API is effectively the same for both. ([npm: drizzle-orm](https://www.npmjs.com/package/drizzle-orm), [drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite))

### Migration workflow

Drizzle supports codebase-first migrations: `drizzle-kit generate` diffs your schema against the previous migration folder and writes SQL + `snapshot.json` into `./drizzle/<timestamp>_<name>/`; then `drizzle-kit migrate` applies unapplied migrations using a `drizzle` migrations table. ([drizzle migrations](https://orm.drizzle.team/docs/migrations), [drizzle-kit migrate](https://orm.drizzle.team/docs/sqlite/drizzle-kit-migrate))

- **Config** (`drizzle.config.ts`): `dialect: "sqlite"`, `schema`, `out: "./drizzle"`, and for `migrate`/`push` a `dbCredentials: { url: "./data/noema.db" }` (the SQLite file path). ([drizzle config](https://orm.drizzle.team/docs/drizzle-config-file))
- **Apply at runtime** (recommended for Docker): `migrate(db, { migrationsFolder })` from `drizzle-orm/better-sqlite3/migrator` in the app entrypoint, so the container runs pending migrations on startup. ([drizzle migrations — option 4](https://orm.drizzle.team/docs/migrations))

### WAL + busy_timeout

- `better-sqlite3` sets `busy_timeout` via the constructor **`timeout`** option (default **5000 ms**): "the number of milliseconds to wait when executing queries on a locked database, before throwing a `SQLITE_BUSY` error." ([better-sqlite3 API](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md))
- WAL: `db.pragma('journal_mode = WAL')`. The better-sqlite3 performance doc recommends turning on WAL for web apps to avoid slow concurrent read/write. ([better-sqlite3 performance](https://github.com/WiseLibs/better-sqlite3/blob/HEAD/docs/performance.md), [sqlite WAL](https://www.sqlite.org/wal.html))
- **Gotcha:** set WAL **on the connection at startup**, not inside a migration file — `PRAGMA journal_mode` cannot run inside a transaction (drizzle's migrator runs migrations in a transaction, so it fails/silently doesn't persist). ([drizzle issue #4968](https://github.com/drizzle-team/drizzle-orm/issues/4968))
- WAL is still **single-writer**: it removes reader/writer contention but does not allow concurrent writers. For noema's two-process case (web app + stdio MCP on one file), WAL + a nonzero `busy_timeout` is the standard mitigation for `SQLITE_BUSY`. ([sqlite WAL](https://www.sqlite.org/wal.html))

```ts
// packages/core/src/db.ts  (single place for connection + pragmas)
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";

export function createDb(path: string) {
  const sqlite = new Database(path, { timeout: 5000 }); // busy_timeout
  sqlite.pragma("journal_mode = WAL");
  sqlite.pragma("busy_timeout = 5000");
  return drizzle({ client: sqlite });
}
```

---

## 3. Sharing schemas + Zod via `packages/core` (no circular deps)

pnpm workspaces are enabled by a root `pnpm-workspace.yaml`. The `workspace:` protocol pins a dependency to a local workspace package and *refuses* to resolve to the registry, guaranteeing `apps/web` and `packages/mcp` always get the local `@noema/core`. ([pnpm workspaces](https://pnpm.io/workspaces), [workspace protocol](https://pnpm.io/workspaces#workspace-protocol-workspace))

Dependency graph (one direction only):

```
apps/web   ──▶ @noema/core
packages/mcp ─▶ @noema/core
@noema/core ─▶ (nothing from the workspace)
```

Because `core` never imports from `apps/*` or `packages/mcp`, there is no cycle. pnpm warns on cyclic workspace deps, and `disallowWorkspaceCycles: true` makes install **fail** on a cycle — useful as a guardrail. ([pnpm workspaces — cycles](https://pnpm.io/workspaces#disallowworkspacecycles))

Key rules to keep `core` SDK/driver-independent and shareable:

1. **Define tables with `drizzle-orm/sqlite-core`** (`sqliteTable`), which is driver-agnostic and pure TS — it pulls **no native binding** into `core`. ([drizzle SQLite](https://orm.drizzle.team/docs/get-started-sqlite))
2. `core` exports: Drizzle tables, **Zod** schemas, domain functions, and a `createDb()` factory (see §2). Declare `better-sqlite3` + `drizzle-orm` + `zod` as `core`'s dependencies — both consumers need the DB anyway, so a single connection/pragma source is DRY and avoids drift between web and MCP.
3. `apps/web` and `packages/mcp` declare `"@noema/core": "workspace:*"` and import `{ createDb, tables, zodSchemas }` from it. ([workspace protocol](https://pnpm.io/workspaces#workspace-protocol-workspace))

If you *do* want to keep the native driver out of `core` (e.g. future `node:sqlite` switch), export only `sqlite-core` schemas + Zod + a `Db` type, and instantiate `better-sqlite3` in each app — but that duplicates the pragma/connection setup in two places, so the single `createDb()` in core is simpler for v1.

---

## 4. One Docker image for a pnpm monorepo + volume-mounted SQLite

pnpm's official guidance for monorepo Docker builds: use the **official pnpm image** (`ghcr.io/pnpm/pnpm`, debian-slim, standalone pnpm, **Node not bundled**), set Node via `pnpm runtime set node 22 -g` (or use `node:22-slim` + install pnpm), and mount the pnpm store as a **BuildKit cache** at `/pnpm/store`. ([pnpm Docker](https://pnpm.io/docker))

For a **single image** from a monorepo, the documented pattern is multi-stage + **`pnpm deploy`** to copy only the app's necessary files and dependencies into a slim runtime layer. `pnpm deploy` needs `injectWorkspacePackages: true` (and, for TS workspace packages, `syncInjectedDepsAfterScripts`) in `pnpm-workspace.yaml` so workspace deps are materialized rather than symlinked. ([pnpm Docker — example 2](https://pnpm.io/docker))

Volume-mounted SQLite is standard Docker: write the DB to an env-driven path, declare a `VOLUME`, and run migrations at container start so a fresh volume is initialized.

### Recipe

```dockerfile
# Dockerfile
FROM ghcr.io/pnpm/pnpm:12 AS base
RUN pnpm runtime set node 22 -g

FROM base AS build
COPY . /app
WORKDIR /app
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm -r build
RUN pnpm deploy --filter=@noema/web --prod /prod/web

FROM base AS runner
ENV DB_PATH=/data/noema.db NODE_ENV=production
COPY --from=build /prod/web /app
WORKDIR /app
EXPOSE 3000
VOLUME /data
# entrypoint runs pending Drizzle migrations, then starts the server
CMD ["sh", "-c", "pnpm migrate && pnpm start"]
```

```yaml
# docker-compose.yml
services:
  noema:
    build: .
    ports: ["3000:3000"]
    environment:
      - DB_PATH=/data/noema.db
      - NOEMA_MCP_TOKEN=${NOEMA_MCP_TOKEN:?set a token}
    volumes:
      - noema-data:/data
volumes:
  noema-data:
```

Key points (all from [pnpm Docker](https://pnpm.io/docker)):

- `--mount=type=cache,id=pnpm,target=/pnpm/store` reuses the store across builds and avoids re-downloading.
- `pnpm deploy --filter=<app> --prod /prod/app` assembles the runtime layer with only that app + its workspace deps.
- Run migrations at **startup** (not build) so the volume is initialized on first run and updated on redeploy — matches §2's runtime `migrate()`.
- `.dockerignore` should exclude `node_modules`, `.git`, `dist`, etc. ([pnpm Docker](https://pnpm.io/docker))

---

## 5. Concrete scaffold

```bash
# 1. workspace root
mkdir noema && cd noema
cat > pnpm-workspace.yaml <<'YAML'
packages:
  - apps/*
  - packages/*
injectWorkspacePackages: true
syncInjectedDepsAfterScripts:
  - build
YAML

# 2. core package
mkdir -p packages/core/src
# packages/core/package.json
#   "name": "@noema/core",
#   "dependencies": { "drizzle-orm": "^0.45.2", "zod": "^3", "better-sqlite3": "^13.0.3" },
#   "devDependencies": { "@types/better-sqlite3": "^7", "typescript": "^5" }

# 3. web app (TanStack Start) — scaffold with TanStack Builder/CLI or clone the official example
#    https://tanstack.com/start/latest/docs/framework/react/quick-start
#    then:  "dependencies": { "@noema/core": "workspace:*" }

# 4. mcp package
mkdir -p packages/mcp/src
# packages/mcp/package.json
#   "name": "@noema/mcp",
#   "dependencies": { "@noema/core": "workspace:*", "@modelcontextprotocol/sdk": "..." }

# 5. drizzle config at repo root (or in packages/core)
cat > drizzle.config.ts <<'TS'
import { defineConfig } from "drizzle-kit";
export default defineConfig({
  dialect: "sqlite",
  schema: "./packages/core/src/schema.ts",
  out: "./drizzle",
  dbCredentials: { url: process.env.DB_PATH ?? "./data/noema.db" },
});
TS

# 6. install + migrate
pnpm install
pnpm drizzle-kit generate   # writes ./drizzle/<ts>_<name>/migration.sql
pnpm drizzle-kit migrate    # or run migrate() at app startup in Docker
```

### Resulting layout

```
noema/
├── pnpm-workspace.yaml
├── pnpm-lock.yaml
├── drizzle.config.ts
├── drizzle/                      # generated migration.sql + snapshot.json
├── Dockerfile
├── docker-compose.yml
├── apps/
│   └── web/                      # TanStack Start (UI + server functions + Drizzle client)
│       ├── src/routes/           # __root.tsx, index.tsx, notes/$noteId.tsx, ...
│       └── src/server/           # createServerFn() + createDb(@noema/core)
├── packages/
│   ├── core/                     # @noema/core: sqlite-core tables + zod + domain + createDb()
│   │   └── src/schema.ts, db.ts, domain/*.ts
│   └── mcp/                      # @noema/mcp: noema.* tools over @noema/core
│       └── src/index.ts
└── README.md, LICENSE
```

---

## Source index

- TanStack Start Overview — <https://tanstack.com/start/latest/docs/framework/react/overview>
- TanStack Start quick-start — <https://tanstack.com/start/latest/docs/framework/react/quick-start>
- Server functions — <https://tanstack.com/start/latest/docs/framework/react/guide/server-functions>
- Routing — <https://tanstack.com/start/latest/docs/framework/react/guide/routing>
- Selective SSR — <https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr>
- npm `@tanstack/react-start` — <https://www.npmjs.com/package/@tanstack/react-start>
- npm `@tanstack/start` — <https://www.npmjs.com/package/@tanstack/start>
- TanStack router discussion #3884 (server functions vs tRPC) — <https://github.com/TanStack/router/discussions/3884>
- tRPC docs — <https://trpc.io/docs>
- Drizzle SQLite — <https://orm.drizzle.team/docs/get-started-sqlite>
- Drizzle migrations — <https://orm.drizzle.team/docs/migrations>
- Drizzle config — <https://orm.drizzle.team/docs/drizzle-config-file>
- drizzle-kit migrate — <https://orm.drizzle.team/docs/sqlite/drizzle-kit-migrate>
- drizzle issue #4968 (WAL in migration) — <https://github.com/drizzle-team/drizzle-orm/issues/4968>
- better-sqlite3 API (`timeout`) — <https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md>
- better-sqlite3 performance (WAL) — <https://github.com/WiseLibs/better-sqlite3/blob/HEAD/docs/performance.md>
- SQLite WAL — <https://www.sqlite.org/wal.html>
- pnpm workspaces — <https://pnpm.io/workspaces>
- pnpm Docker — <https://pnpm.io/docker>
