# Name collision research — "cortex"

**Date:** 2026-09-08
**Subject:** proposed name for a self-hosted OSS personal-data app
**Sources checked:** GitHub search API, npm registry, Docker Hub search API, USPTO / WIPO / EUIPO trademark databases (via public records and secondary trademark aggregators)
**Scope note:** This is a factual collision scan, not a legal opinion. A trademark clearance opinion from a trademark attorney is still required before any launch decision is final.

---

## TL;DR

**Verdict: SWITCH.** "cortex" is saturated on every axis simultaneously, and fails most decisively on the trademark axis:

- **GitHub** — three 5k–8k★ projects named `cortex` (`cortexlabs/cortex`, `cortexproject/cortex` CNCF, `TheHive-Project/Cortex`), plus multiple small but directly-on-point *personal-memory / second-brain* apps named "cortex".
- **npm** — the bare name `cortex` is taken (dormant since 2015, but still owned), and the `cortex`-CLI name is actively claimed by `nexus-cortex`.
- **Docker Hub** — `cortexproject/cortex`, `ubuntu/cortex`, `portworx/cortex`, `thehiveproject/cortex` each have millions of pulls.
- **Trademark** — **Palo Alto Networks** owns an active "Cortex" security-software product line (Cortex XDR / XSIAM / Cortex Cloud) with live `CORTEX` registrations; a live EU word mark `CORTEX` (EU-004793551) exists; and a live US `CORTEX` class-42 mark (Volt Athletics) exists. This is the decisive blocker for a software/SaaS product.

Recommended alternatives (pre-checked below): **Noema** and **Reliquary** clear the trademark axis (their live marks are in non-software classes), with only minor, dormant npm/GitHub collisions. Avoid **Anamnesis / Memora / Cerebra / Mneme** (each fails trademark or npm).

---

## 1. GitHub — notable projects named "cortex"

Primary source: GitHub search API `q=cortex in:name, sort=stars` (<https://api.github.com/search/repositories?q=cortex+in:name&sort=stars&order=desc>) — 16,147 repositories match.

### Major OSS projects (5k+ stars)

| Repo | Stars | What it is | License |
|---|---|---|---|
| [cortexlabs/cortex](https://github.com/cortexlabs/cortex) | 8,011 | "Production infrastructure for machine learning at scale" | Apache-2.0 |
| [cortexproject/cortex](https://github.com/cortexproject/cortex) | 5,861 | CNCF-incubated "horizontally scalable … long term Prometheus" | Apache-2.0 |
| [janhq/cortex.cpp](https://github.com/janhq/cortex.cpp) | 2,753 | "Local AI API Platform" (archived) | Apache-2.0 |
| [qibin0506/Cortex](https://github.com/qibin0506/Cortex) | 2,692 | LLM pre-training/RLHF codebase | Apache-2.0 |

Also notable: [TheHive-Project/Cortex](https://github.com/TheHive-Project/Cortex) — widely-deployed open-source SOC "Observable Analysis and Active Response Engine" (security/incident-response).

### Directly on-point: personal-data / memory / "second-brain" apps named "cortex"

This is the confusion the author specifically asked about — it is real, not hypothetical:

- [trace-cortex/cortex-app](https://github.com/trace-cortex/cortex-app) — ~830★, "local-first personal memory app … a local, cited model of how you work … turns your notes and AI-chat history into a typed, layered, cited model." **Closest existing match to the author's pitch.**
- [tylerfloyd/cortex](https://github.com/tylerfloyd/cortex) — "self-hosted personal knowledge management system" (capture/organize/query web content with AI).
- [tools-for-agents/cortex](https://github.com/tools-for-agents/cortex) — "a local, Obsidian-compatible second brain for agents."
- [DoktorDaveJoos/cortex](https://github.com/DoktorDaveJoos/cortex) — "a powerful desktop notes app. Offline-first. AI-assisted."
- [tamimsangrar/cortex](https://github.com/tamimsangrar/cortex) — "turns your personal data into a knowledge base."

**Bottom line:** the name is not only crowded with large infra projects, it is already claimed inside the exact personal-memory niche.

---

## 2. npm — `cortex` and close matches

Primary source: <https://registry.npmjs.org/cortex> (and `/-/v1/search?text=cortex`).

- **`cortex` is TAKEN.** Owner `kael` (github: `cortexjs/cortex`); description "Cortex is an npm-like package manager for browsers." Latest version **6.2.3**, last published **2015-08-14**, ~870 downloads/month. Dormant but not abandoned — the name cannot be reused. (<https://www.npmjs.com/package/cortex>)
- **`nexus-cortex`** (Spitfire-Products, Apache-2.0) — "One install gives you the **`cortex` CLI** and HTTP server." So the `cortex` *binary* name is actively claimed by another project. (<https://www.npmjs.com/package/nexus-cortex>)
- Other active close matches in the `cortex` namespace: `@nexus-cortex/*` (cli/tui/server/executors/types), `vault-cortex` (Obsidian MCP server), `@cortex-docs/*`, `@cortex-ui/core`, `@cortexapps/plugin-core` (Cortex.io internal developer portal), `@tecsinapse/cortex-react`, `@theronap/cortex-mcp`.

**Bottom line:** bare npm `cortex` is unavailable, and even a scoped `@cortex/*` would collide with several active orgs.

---

## 3. Docker Hub — `cortex*` images

Primary source: <https://hub.docker.com/v2/search/repositories/?query=cortex> (2,061 matching repositories).

| Image | Pulls | Notes |
|---|---|---|
| [cortexproject/cortex](https://hub.docker.com/r/cortexproject/cortex) | 5,252,060 | Prometheus long-term storage (CNCF) |
| [ubuntu/cortex](https://hub.docker.com/r/ubuntu/cortex) | 4,255,021 | Canonical, deprecated |
| [portworx/cortex](https://hub.docker.com/r/portworx/cortex) | 4,129,765 | Portworx storage |
| [thehiveproject/cortex](https://hub.docker.com/r/thehiveproject/cortex) | 1,271,143 | SOC/security engine |
| [grafana/cortex](https://hub.docker.com/r/grafana/cortex) | 11,025 | |

Plus `cortexproject/cortex-linux`, `cleanstart/cortex`, `logship/cortex`, `vcxsolutions/cortex`, and dozens of personal namespaces.

**Bottom line:** `cortex` as an image name is heavily used by at least four organizations with production installs.

---

## 4. Trademark — USPTO / WIPO / EUIPO

Note: searched via USPTO TESS records, WIPO Global Brand Database, EUIPO/TMview, and public aggregators (uspto.report, markinton, tmdb.eu, Canadian CIPO). Not exhaustive — full clearance requires an attorney.

### Live / registered marks most relevant to software (classes 9 / 42)

- **CORTEX — Palo Alto Networks, Inc.** — US, class 42 (computer-networking / network-security consultation). <https://uspto.report/TM/88979203>
- **CORTEX CLOUD — Palo Alto Networks, Inc.** — US serial 99206205, classes 9 + 42, filed 2025-05-28, pending. <https://markinton.com/trademark/cortex-cloud-99206205>
- **CORTEX XSIAM — Palo Alto Networks, Inc.** — Canada reg 2232011, class 42 (cyber-threat detection/monitoring software). <https://ised-isde.canada.ca/cipo/trademark-search/2232011>
- **CORTEX — Volt Athletics, Inc.** — US serial 88084060 / reg 6301775, class 42, live. <https://markinton.com/trademark/cortex-88084060>
- **CORTEX — EU word mark** EU-004793551, filed 2005-12-09, registered 2006-10-11, status active. <https://tmdb.eu/marke/EU-004793551::cortex.html>

### The decisive factor

Palo Alto Networks operates a current, heavily-marketed **"Cortex"** software product family — [Cortex XDR](https://www.paloaltonetworks.com/cortex/cortex-xdr) and [Cortex XSIAM](https://www.paloaltonetworks.com/cortex/cortex-xsiam) — with live word-mark registrations in software/service classes. A new self-hosted software app named "cortex" sits directly inside a well-known, actively-enforced software brand (plus a live EU `CORTEX` word mark and a live US class-42 `CORTEX`). This is a concrete likelihood-of-confusion / enforcement risk, not a theoretical one.

---

## 5. Recommendation

**Keep "cortex"? No.** It fails all four axes, and the trademark axis alone (Palo Alto Networks + live EU/US marks in software classes) is disqualifying for a software/SaaS product without a trademark fight.

**Recommendation: switch.** Because the entire "memory/brain" thesaurus is crowded, prioritize the axis that actually differentiates names — **software-class trademark clearance** — and accept minor npm/GitHub collisions (single-word npm names are near-universally squatted anyway; publish under a scope or a compound).

### Pre-checked alternatives (same four axes)

**1. Noema** (Greek: "object of thought") — *best overall*

- Trademark: **clear for software.** Live mark `NOEMA` is Caprice Holdings, classes **41/43** (hospitality), not software. <https://markinton.com/trademark/noema-97398707>
- npm: `noema` taken (dormant v0.0.3, "AI React component generation"). <https://www.npmjs.com/package/noema> → use `@noema/...` or a compound.
- GitHub: small `Fail-Safe/Noema` (16★, AI memory layer). <https://github.com/Fail-Safe/Noema>
- Docker: no significant existing image.

**2. Reliquary** (a container for precious objects/memories)

- Trademark: **clear for software.** Live mark `RELIQUARY` is Reliquary Inc., classes **14/25** (jewelry/clothing). <https://markinton.com/trademark/reliquary-97622057>
- npm: `reliquary` taken (dormant "secrets manager"). <https://www.npmjs.com/package/reliquary>
- GitHub: tiny `c0ze/reliquary` (2★, qdrant agent memory), `SentimentalK/Reliquary`. <https://github.com/c0ze/reliquary>
- Docker: no significant existing image.

**3. Anamnesis** (Greek: "recollection") — *caution*

- Trademark: **risk.** `ANAMNESIS` pending, classes **9/42/45** (software), filed 2026-05-11. <https://markinton.com/trademark/anamnesis-99816710>
- npm: `anamnesis` taken (dormant React lib). <https://www.npmjs.com/package/anamnesis>
- GitHub: `Trapezohe/Anamnesis` (local-first agent-memory bridge), `gayawellness/anamnesis`. <https://github.com/trapezohe/anamnesis>
- **Not recommended as-is** unless the pending mark is cleared.

### Rejected during pre-check (for the record)

- **Memora** — npm taken; live class-42 mark "Memora Health" + "MNEMORA" class 42. Fails trademark.
- **Cerebra** — npm is a security-holding placeholder (squatted); "Cerebras" is an AI-hardware company. Fails npm + trademark.
- **Mneme** — npm taken; crowded with brand-new AI-memory projects (`steveyeow/mneme`, `BrettNye/Mneme`, etc.); "MNEMO"/"MNEMORA" pending in class 9/42. Fails.

### Practical next steps for whichever name is chosen

1. Run a **formal trademark clearance** (attorney) on the shortlist — this scan is not legal advice.
2. Secure the **scoped npm** (`@noema/…` / `@reliquary/…`) and a **Docker Hub namespace** early.
3. Pick a GitHub org name that is not bare `cortex` (e.g. `noema-app`, `reliquaryhq`).
