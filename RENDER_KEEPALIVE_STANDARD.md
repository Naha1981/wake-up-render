# RENDER-KA — Render Free Tier Deployment & Keep-Alive Standard

**Version:** 1.0
**Scope:** Applies to every NahaLabs project deployed on Render Free Tier (CargoIQ, GigNurse, iGosa, RSL ASYCUDA, SENAKANGOELI, RailGuard, etc.)
**Activation:** Reference this file (or say "apply RENDER-KA") when scaffolding any new Render-hosted service under AE-OS.

## Purpose

Render's free tier spins down idle services and cold-starts them on the next request. This standard eliminates that failure mode by:

1. Giving every service cheap, AI-free health endpoints.
2. Pinging those endpoints on a schedule from a single, reusable GitHub Actions hub.
3. Optionally layering a self-hosted monitor (Uptime Kuma) for tighter intervals and alerting.

**Honest limit:** nothing here can force Render to never sleep — that's Render's platform policy. This reduces cold starts to near-zero by keeping traffic flowing; it does not override Render's resource management.

---

## 1. Required Health Endpoints

Every backend exposes three endpoints. No exceptions.

### `GET /health`
```json
{ "status": "ok", "service": "<service-name>", "version": "<version>" }
```
- No DB queries, no model loading, no external API calls
- Target response time: <100ms

### `GET /ready`
Verifies real dependencies are actually up: database, Redis, vector store, model availability. This is the only endpoint allowed to check downstream systems.

### `GET /ping`
Returns HTTP 200 immediately. Reserved exclusively for keep-alive pingers — never used for real health decisions.

**Hard rule:** `/health` and `/ping` must never call OpenAI, Anthropic, Gemini, Ollama, embeddings, OCR, or any document/inference pipeline. If it touches an LLM or a model, it belongs in `/ready` or nowhere near a health check.

---

## 2. Central Keep-Alive Hub (one repo, all projects)

Don't build a keep-alive workflow per project. Maintain **one** repo — this scaffold — as the hub:

```
render-keepalive/
├── .github/workflows/keep-alive.yml
├── urls.txt
└── README.md
```

- New project → add its URL(s) to `urls.txt` → done. No workflow edits.
- Runs every 10 minutes via cron, plus manual `workflow_dispatch`.
- Continues past individual failures; logs status, latency, and timestamp per endpoint.
- Never hardcode URLs inside the workflow — always read from `urls.txt`.

---

## 3. Environment Variables (per project)

| Variable | Purpose |
|---|---|
| `APP_NAME` | Service identifier in logs/health payload |
| `APP_VERSION` | Version string in `/health` |
| `RENDER_EXTERNAL_URL` | Render-provided public URL |
| `PORT` | Bind port (Render sets this) |

---

## 4. Logging Standard

Every ping and health check logs structurally:
`timestamp, endpoint, status_code, latency_ms, success/failure`

---

## 5. Graceful Startup

- Preload config and lightweight dependencies at boot.
- Never load heavy AI models (Qwen2.5-VL, embeddings, OCR models) during startup health checks.
- Lazily initialize expensive resources on first real use, not on `/health`.

---

## 6. Project Folder Convention

```
project/
├── .github/workflows/    (if project also self-pings; optional if hub covers it)
├── docs/
├── src/
│   └── routes/
│       ├── health.py
│       ├── ready.py
│       └── ping.py
├── urls.txt               (only in the hub repo)
└── README.md
```

---

## 7. Monitoring Compatibility

Endpoints must work with **any** monitor, unauthenticated, no custom headers required:
- GitHub Actions (hub, every 10 min)
- Uptime Kuma (self-hosted, 1–5 min, if/when you run one)
- UptimeRobot / cron-job.org (optional external backup layer)

`/health` returns plain HTTP 200 when healthy — that's the universal contract.

---

## 8. Layered Defense (recommended combo)

For near-zero cold starts on anything customer-facing (e.g. CargoIQ during the July SARS rollout window):

1. **GitHub Actions cron** — every 10 min (the hub, always on)
2. **Uptime Kuma** — 1–5 min, only if you have an always-on host to run it on
3. **External backup pinger** (UptimeRobot/cron-job.org) — free tier, redundancy in case GitHub Actions has an outage

Layer 1 alone is usually enough. Add 2–3 only for revenue-critical services.

---

## 9. Scalability Rule

One project can mean multiple Render services (frontend, backend, worker, webhook, AI service). Each exposes its own `/health`. All get added as separate lines in the hub's `urls.txt` — the hub scales with zero new code.

---

## 10. Documentation Checklist (per project README)

- [ ] Render deployment steps
- [ ] Required env vars
- [ ] Health endpoint contract
- [ ] Confirmation it's added to the keep-alive hub's `urls.txt`
- [ ] Troubleshooting: what a failed ping in the hub log means for this service

---

## 11. Code Quality Rules

- No hardcoded URLs, ports, or service names — config-driven.
- Health/monitoring code stays fully decoupled from business logic.
- Health endpoint contracts stay stable even as the app grows — don't let `/health` acquire dependencies ov er time.
