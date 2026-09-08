# MCP TypeScript SDK — transport research (2026-09-08)

Background research for `noema` transport matrix. Primary sources only: official
docs at `modelcontextprotocol.io`, the SDK source at
`github.com/modelcontextprotocol/typescript-sdk`, and the npm registry. Every claim
is cited with a URL or repo path.

## TL;DR

1. **There are now TWO SDK lines, not one.** The npm package named in the design doc,
   `@modelcontextprotocol/sdk`, is the **v1** monolithic line — latest **1.30.0**,
   implementing the 2025-11-25 spec. The repo's `main` branch is now **v2**, split into
   `@modelcontextprotocol/server` + `@modelcontextprotocol/client` (both **2.0.0**),
   implementing the 2026-07-28 spec. The SDK README calls **v2 "the stable release line"**
   and says v1.x gets bug/security fixes for "at least 6 months after v2's release".
   This version fork is the single most important decision for `packages/mcp`.

2. **HTTP (Streamable HTTP) + bearer token is supported in both lines**, but the API is
   completely different. v1: `StreamableHTTPServerTransport` + `createMcpExpressApp` +
   a hand-written or `requireBearerAuth` middleware. v2: `createMcpHandler(factory)` +
   `requireBearerAuth` with a `verifyAccessToken` you supply. Both reject a missing/
   invalid token with **401**; neither validates the token *for* you — you mount the
   check in front of the handler.

3. **stdio is a separate entry point** (`StdioServerTransport` in v1, `serveStdio` in v2)
   that the *client* spawns as a local child process. It carries no HTTP auth. Sharing a
   SQLite file is an app-level concern (WAL + `busy_timeout`), not an SDK constraint.

4. **Clients declare stdio via `command`/`args`/`env`, and HTTP via `url` + a static
   `Authorization: Bearer` header.** `streamable-http` is accepted as an alias for `http`.

5. **Gotchas**: (a) the v1/v2 fork; (b) the v2 handler validates *no* Host/Origin/token —
   mount guards in front; (c) the SDKs do NOT auto-enable permissive CORS on the MCP
   endpoint — browser clients need it added manually while keeping `Origin` validation;
   (d) **stdio cannot cross a container boundary** — a client outside Docker cannot spawn
   a process inside, so Docker deploy = HTTP only.

---

## Q1 — Current stable version + HTTP (Streamable HTTP) transport with bearer auth

### Version landscape (the fork)

| Package | Latest | Node | Spec | Status |
|---|---|---|---|---|
| `@modelcontextprotocol/sdk` (v1, monolithic) | **1.30.0** | `>=18` | 2025-11-25 | bug/security fixes ≥6 mo after v2 |
| `@modelcontextprotocol/server` (v2) | **2.0.0** | `>=20` | 2026-07-28 | "stable release line" |
| `@modelcontextprotocol/client` (v2) | **2.0.0** | `>=20` | 2026-07-28 | "stable release line" |

Sources:

- `https://registry.npmjs.org/@modelcontextprotocol/sdk/latest` → `"version": "1.30.0"`, `"engines": {"node": ">=18"}`, license MIT.
- `https://registry.npmjs.org/@modelcontextprotocol/server/latest` → `"version": "2.0.0"`, `"engines": {"node": ">=20"}`.
- `https://registry.npmjs.org/@modelcontextprotocol/client/latest` → `"version": "2.0.0"`, `"engines": {"node": ">=20"}`.
- SDK README, `main` branch: "**This is the `main` branch — v2 of the SDK** (`@modelcontextprotocol/server`, `@modelcontextprotocol/client`), implementing the 2026-07-28 MCP spec. … **v2 is the stable release line** … v1.x continues to receive bug fixes and security updates for at least 6 months after v2's release." — `https://github.com/modelcontextprotocol/typescript-sdk/blob/main/README.md`

The design doc (`docs/noema-design-20260908-180300.md`) names
`@modelcontextprotocol/sdk` — that string is the **v1** line. If the intent is "latest
stable for new work," that is now `@modelcontextprotocol/server@2.0.0`. Recommend
resolving this explicitly before T1/T4 (see matrix at the end).

### v1 — `@modelcontextprotocol/sdk` 1.30.0

Exact classes/helpers (import paths are the subpath exports; `./*` is wildcard-mapped):

- `McpServer` — `@modelcontextprotocol/sdk/server/mcp.js`
- `StreamableHTTPServerTransport` — `@modelcontextprotocol/sdk/server/streamableHttp.js`
- `StdioServerTransport` — `@modelcontextprotocol/sdk/server/stdio.js`
- `createMcpExpressApp` — `@modelcontextprotocol/sdk/server/express.js` (DNS-rebinding
  protection enabled by default; default host `127.0.0.1`)
- `hostHeaderValidation` — `@modelcontextprotocol/sdk/server/middleware/hostHeaderValidation.js`
- `requireBearerAuth` — `@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js`
  (OAuth resource-server machinery — takes a `verifier` with `verifyAccessToken`)

Source: `https://ts.sdk.modelcontextprotocol.io/server` (transports, stdio, DNS-rebinding
sections); `https://github.com/modelcontextprotocol/typescript-sdk/blob/v1.x/src/examples/server/simpleStreamableHttp.ts`.

The canonical v1 wiring (stateful, from `simpleStreamableHttp.ts`):

```ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMcpExpressApp } from '@modelcontextprotocol/sdk/server/express.js';

const app = createMcpExpressApp(); // DNS-rebinding protection on by default

// per session: new StreamableHTTPServerTransport({ sessionIdGenerator: () => randomUUID(), ... })
//   await server.connect(transport);
//   await transport.handleRequest(req, res, req.body);   // POST /mcp
```

**Bearer-token auth in v1:** the SDK ships no static-token helper on the *server* side.
`requireBearerAuth` is full OAuth (expects a token verifier / introspection, issues a
`WWW-Authenticate: Bearer` challenge). For a static `NOEMA_MCP_TOKEN` the laziest correct
thing is a small Express middleware in front of `handleRequest`:

```ts
app.all('/mcp', (req, res, next) => {
  const expected = process.env.NOEMA_MCP_TOKEN;
  if (!expected) return res.status(503).end('NOEMA_MCP_TOKEN not set');
  const auth = req.headers.authorization;
  if (!auth || auth !== `Bearer ${expected}`) {
    return res.status(401).end('Unauthorized');
  }
  next();
});
```

(Or a `requireBearerAuth({ verifier: { verifyAccessToken: async t => t === expected ? { token: t, clientId: 'noema' } : (throw …) } })` if you want the OAuth-shaped challenge.)

### v2 — `@modelcontextprotocol/server` 2.0.0

Exact helpers:

- `createMcpHandler(factory)` — returns `{ fetch, close, notify, bus }`; `fetch` is a
  web-standard `(Request) => Promise<Response>`.
- `McpServer` — `@modelcontextprotocol/server`
- `serveStdio` — `@modelcontextprotocol/server/stdio`
- Mount on Node: `toNodeHandler(handler)` from `@modelcontextprotocol/node`; or
  `createMcpExpressApp` / `createMcpHonoApp` / `createMcpFastifyApp` from the middleware
  packages. Those framework factories arm Host/Origin validation on localhost binds.
- `requireBearerAuth` — from `@modelcontextprotocol/server` (web-standard gate) **or**
  `@modelcontextprotocol/express` (Express middleware); you supply a `verifyAccessToken`.

Source: `https://ts.sdk.modelcontextprotocol.io/v2/serving/http`;
`https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization`;
`https://github.com/modelcontextprotocol/typescript-sdk/blob/main/README.md` (middleware packages list).

Minimal HTTP server (web-standard, token-gated):

```ts
import { createMcpHandler, McpServer, requireBearerAuth } from '@modelcontextprotocol/server';

const handler = createMcpHandler(() => {
  const server = new McpServer({ name: 'noema', version: '0.1.0' });
  // server.registerTool(...) inside the factory
  return server;
});

const gate = requireBearerAuth({
  verifier: {
    verifyAccessToken: async (token) => {
      if (token !== process.env.NOEMA_MCP_TOKEN) throw new Error('invalid token');
      return { token, clientId: 'noema', scopes: [], expiresAt: Infinity }; // expiresAt MUST be set
    }
  },
  requiredScopes: []
});

export default {
  async fetch(request: Request): Promise<Response> {
    const auth = await gate(request);
    if (auth instanceof Response) return auth;   // 401 invalid_token / 403 insufficient_scope
    return handler.fetch(request, { authInfo: auth });
  }
};
```

Key v2 semantics (all from `https://ts.sdk.modelcontextprotocol.io/v2/serving/http` and
`/v2/serving/authorization`):

- "The handler trusts its caller: it validates no `Host` header, no `Origin` header, and
  no token. Mount those checks in front of it."
- A missing/malformed/expired token → **`401`** with OAuth error `invalid_token`; a valid
  token missing a `requiredScopes` entry → **`403`** `insufficient_scope`; both carry a
  `WWW-Authenticate: Bearer` challenge.
- `requireBearerAuth` also answers `401 invalid_token` for a token whose `expiresAt` is
  unset — **always populate `expiresAt`**.
- `authInfo` flows `req.auth` → `handler.fetch(request, { authInfo })` → `ctx.http.authInfo`
  in tool handlers. `ctx.http` is `undefined` over stdio — guard the read if one server
  serves both transports.

---

## Q2 — stdio transport as a standalone entry point (separate process, shared SQLite)

### Setup

**v1** (`https://ts.sdk.modelcontextprotocol.io/server`):

```ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new McpServer({ name: 'noema', version: '0.1.0' });
// register tools...
const transport = new StdioServerTransport();
await server.connect(transport);
```

**v2** (`https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio`):

```ts
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';

const handle = serveStdio(() => {
  const server = new McpServer({ name: 'noema', version: '0.1.0' });
  // register tools...
  return server;
});
// handle is a StdioServerHandle; handle.close() on SIGINT
```

### Constraints / notes

- **stdout is the protocol channel.** "The server MUST NOT write anything to its `stdout`
  that is not a valid MCP message." Log via `console.error` (stderr), never `console.log`.
  Sources: `https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio` ("Log to stderr, never
  stdout"); spec `https://modelcontextprotocol.io/specification/2025-11-25/basic/transports`
  (stdio section).
- **No HTTP auth over stdio.** "Stdio servers handle authentication outside the MCP
  protocol entirely. The server process inherits env vars." — Cursor MCP auth docs
  (`https://www.truefoundry.com/blog/mcp-authentication-in-cursor-oauth-api-keys-and-secure-configuration`,
  corroborated by Cursor `https://cursor.com/docs/mcp` table "stdio … Auth: Manual").
- **Transport is a child process.** "The client launches the MCP server as a subprocess."
  (`https://modelcontextprotocol.io/specification/2025-11-25/basic/transports`). So the
  separate `packages/mcp` stdio entry point must be a *runnable binary* the client can spawn
  (e.g. `node packages/mcp/dist/stdio.js` or an `npx`-style bin).
- **Sharing SQLite is orthogonal to the SDK.** Both the web process and the stdio process
  open the same file. No SDK option governs this; the design doc's WAL + `busy_timeout`
  note is exactly the right mitigation (`docs/noema-design-20260908-180300.md`,
  transport-matrix fix 2.1). Keep exactly one process "canonical" for the file per the
  design doc's sync premise.
- **v2 caveat:** `ctx.http` is `undefined` over stdio, so any tool handler that reads
  `ctx.http.authInfo` must guard for the stdio case
  (`https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization`, "Read the caller").

---

## Q3 — How clients declare a connection

Common denominator (the `mcpServers` shape clients read):

```jsonc
{
  "mcpServers": {
    "noema-stdio": {
      "command": "node",
      "args": ["packages/mcp/dist/stdio.js"],
      "env": { "NOEMA_DB": "/path/noema.sqlite" }
    },
    "noema-http": {
      "type": "http",                      // "streamable-http" is an accepted alias
      "url": "https://host.example/mcp",
      "headers": { "Authorization": "Bearer <NOEMA_MCP_TOKEN>" }
    }
  }
}
```

- **Claude Code** (`https://code.claude.com/docs/en/mcp-servers.md`):
  - HTTP: `claude mcp add --transport http noema https://host.example/mcp --header "Authorization: Bearer <token>"`.
  - stdio: `claude mcp add --transport stdio noema -- node packages/mcp/dist/stdio.js` (everything after `--` is the command).
  - JSON: "the `type` field accepts `streamable-http` as an alias for `http`"; "a JSON entry
    that has a `url` but no `type` is a configuration error, because Claude Code reads an
    entry with no `type` as a stdio server."
- **Cursor** (`https://cursor.com/docs/mcp`): config type is
  `{ type?: "stdio"; command; args?; env?; cwd? } | { type?: "http" | "sse"; url; headers?; auth? }`.
  Table: stdio = "Local … Single user … Auth: Manual"; Streamable HTTP = "Local/Remote …
  Multiple users … Auth: OAuth". `headers` carries a static `Authorization` for non-OAuth
  API-key deployments.
- **Claude Desktop**: classic `claude_desktop_config.json` uses the same `mcpServers`
  `command`/`args`/`env` shape for stdio; remote HTTP is configured via `url` in newer
  configs or through "Connectors" (`https://www.getmesa.com/blog/configure-mcp-servers-claude-desktop`).
  Note the known bug: a `url` entry in `claude_desktop_config.json` has historically been
  wiped on startup — `https://github.com/anthropics/claude-code/issues/37286`. Prefer the
  `type: "http"` + `url` + `headers` form (Claude Code shape) or Connectors.

---

## Q4 — Known gotchas

1. **v1 vs v2 fork (decide before you build).** `@modelcontextprotocol/sdk` in the design
   doc is v1 (1.30.0); the SDK README marks v2 (`@modelcontextprotocol/server`) as the
   stable release line and gives v1 only "at least 6 months" of fixes post-v2
   (`https://github.com/modelcontextprotocol/typescript-sdk/blob/main/README.md`). Don't mix
   v1 server imports with v2 middleware packages — pick one line.

2. **Auth middleware is not automatic.** v1: `requireBearerAuth` is OAuth-only; a static
   `NOEMA_MCP_TOKEN` needs a hand-written middleware (see Q1). v2: the handler "verifies no
   token" — the `requireBearerAuth` gate must be mounted in front, and `expiresAt` must be
   set or it 401s
   (`https://ts.sdk.modelcontextprotocol.io/v2/serving/http`,
   `https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization`).

3. **CORS for browser-based clients is manual, and the spec mandates `Origin` validation.**
   The Streamable HTTP spec says servers **MUST validate the `Origin` header** and respond
   **403** if invalid (`https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http`,
   "Security & Endpoint"; same text in `2025-11-25`). Neither SDK auto-adds permissive
   `Access-Control-Allow-Origin` to the MCP endpoint — v1 `createMcpExpressApp` does not,
   and v2 only serves "permissive CORS" on its OAuth metadata routes
   (`https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization`). A browser-hosted
   client therefore needs explicit CORS (`Access-Control-Allow-Origin`,
   `Access-Control-Allow-Headers` for the custom `MCP-Protocol-Version` / `Accept` headers)
   plus an OPTIONS preflight handler, while *keeping* `Origin` validation (or
   `localhostOriginValidation` in v2) for DNS-rebinding protection.

4. **Docker-only-HTTP (stdio cannot cross a container boundary).** stdio means "the client
   launches the MCP server as a subprocess" on the *same host*
   (`https://modelcontextprotocol.io/specification/2025-11-25/basic/transports`; Cursor
   `https://cursor.com/docs/mcp` table: stdio = "Local"). A client (Claude Desktop, Cursor,
   Hermes on a laptop) cannot spawn a process *inside* a remote container, and cannot speak
   stdio over a network. So a Dockerized `noema` is reachable **only over HTTP (Streamable
   HTTP)** — map/publish the MCP HTTP port. stdio works only for bare-metal installs where
   the agent runs on the same machine as the `noema` stdio binary.

5. **DNS-rebinding guard.** v1 `createMcpExpressApp` enables it by default (host `127.0.0.1`);
   v2 framework factories arm Host validation on localhost binds
   (`https://ts.sdk.modelcontextprotocol.io/server`;
   `https://ts.sdk.modelcontextprotocol.io/v2/serving/http`). When binding `0.0.0.0` inside
   Docker, you must pass your own allowed hosts / reverse-proxy TLS.

6. **stdout pollution breaks stdio.** One `console.log` injects a non-JSON-RPC line into the
   stream the host parses (`https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio`).

---

## Recommended transport matrix

Decision first: **pick the SDK line.** The design doc says `@modelcontextprotocol/sdk`
(v1, 1.30.0). For a brand-new 2026 project the SDK's own README points new work at v2
(`@modelcontextprotocol/server` 2.0.0), which is the "stable release line". Both satisfy
every requirement in the approved architecture; the differences are package shape, Node
floor (18 vs 20), and API. Recommendation: **target v2** (`@modelcontextprotocol/server` +
`@modelcontextprotocol/node`/`express` middleware) for new code, and update the design doc's
stack line; staying on v1 `@modelcontextprotocol/sdk@1.30.0` is acceptable if matching the
doc verbatim matters more than the v1-EOL clock.

| Scenario | Transport | SDK entry point | Auth | Notes |
|---|---|---|---|---|
| Docker / VPS deploy (MCP inside web process) | **Streamable HTTP** | v1: `StreamableHTTPServerTransport`; v2: `createMcpHandler` + `toNodeHandler` | `NOEMA_MCP_TOKEN` bearer → **401** (thin middleware in v1, `requireBearerAuth`+`verifyAccessToken` in v2) | single `/mcp` endpoint; `Origin` validation + reverse-proxy TLS |
| Bare-metal, agent on same host (Hermes/Claude/Cursor local) | **stdio** (separate `packages/mcp` binary) | v1: `StdioServerTransport`; v2: `serveStdio` | none (process env) | shares the SQLite file; WAL + `busy_timeout`; log to stderr |
| Docker + local agent (Hermes on laptop) | **HTTP only** (published port) | same as Docker row | `NOEMA_MCP_TOKEN` bearer | stdio cannot cross the container boundary |
| Browser-based client (future) | Streamable HTTP | same as Docker row | bearer + **manual permissive CORS** + OPTIONS preflight | keep `Origin` validation for DNS-rebinding |

Key source links:

- SDK README (v1/v2 split): <https://github.com/modelcontextprotocol/typescript-sdk/blob/main/README.md>
- v1 server guide: <https://ts.sdk.modelcontextprotocol.io/server>
- v1 streamable-http example (auth wiring): <https://github.com/modelcontextprotocol/typescript-sdk/blob/v1.x/src/examples/server/simpleStreamableHttp.ts>
- v2 HTTP serving: <https://ts.sdk.modelcontextprotocol.io/v2/serving/http>
- v2 bearer auth: <https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization>
- v2 stdio: <https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio>
- Streamable HTTP spec (Origin validation): <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http>
- Claude Code MCP config: <https://code.claude.com/docs/en/mcp-servers.md>
- Cursor MCP config: <https://cursor.com/docs/mcp>
